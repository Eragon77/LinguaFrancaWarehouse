import logging

class WarehouseController:
    def __init__(self, warehouse):
        self.wh = warehouse
        self.current_move_sequence = []

    # --- TIME CALCULATION HELPERS ---

    def _get_time_y(self, target_y: float) -> float:
        platform = self.wh.platform
        d = abs(target_y - platform.curr_y)
        
        try:
            return d/platform.speed_y
        except ZeroDivisionError:
            logging.error(f"[TIME CALC FAIL]: Platform speed_y is zero for distance {d}. Returning 0.0 time")
            return 0.0
        except AttributeError:
            logging.error("[TIME CALC FAIL] Platform object or speed_y attribute not found.")
            return 0.0
    
    def _get_time_x(self, target_x: float) -> float:
        platform = self.wh.platform
        d = abs(target_x - platform.curr_x)
        
        try:
            return d/platform.extract_speed
        except ZeroDivisionError:
             logging.error(f"[TIME CALC FAIL]: Platform speed_x is zero for distance {d}. Returning 0.0 time")
        except AttributeError:
            logging.error("[TIME CALC FAIL] Platform object or speed_x attribute not found.")
            return 0.0



    def _build_sequence_internal(self, slot_from, slot_to) -> bool:
        """Internal helper to build the PICKUP -> PLACE sequence."""
        if slot_from.tray is None:
            logging.error(f"Sequence Build Failed: Source slot {slot_from.position_id} is empty.")
            return False
            
        self.current_move_sequence = []

        # --- PHASE 2: PLACE (Action that will happen last) ---
        # 1. Calculate time to retract from X to 0.0
        time_retract_2 = self._get_time_x(0.0)
        self.current_move_sequence.append((time_retract_2, "update_x_position", (0.0,), "PLACE: Retraction complete. IDLE."))
        # 2. Place the tray into the destination slot (instantaneous action)
        self.current_move_sequence.append((0.0, "place_into", (slot_to,), f"PLACE: Tray placed into {slot_to.position_id}."))
        # 3. Calculate time to extend to destination X
        time_extend_2 = self._get_time_x(slot_to.x)
        self.current_move_sequence.append((time_extend_2, "update_x_position", (slot_to.x,), f"PLACE: Extending to X={slot_to.x}."))
        # 4. Calculate time to move Y to destination
        time_y_place = self._get_time_y(slot_to.y)
        self.current_move_sequence.append((time_y_place, "update_y_position", (slot_to.y,), f"PLACE: Moving Y to {slot_to.position_id}."))

        # --- PHASE 1: PICKUP (Action that will happen first) ---
        # 5. Calculate time to retract X to 0.0 after pickup
        time_retract_1 = self._get_time_x(0.0)
        self.current_move_sequence.append((time_retract_1, "update_x_position", (0.0,), "PICKUP: Retraction complete."))
        # 6. Pick up the tray from the source slot (instantaneous action)
        self.current_move_sequence.append((0.0, "pick_up_from", (slot_from,), f"PICKUP: Tray picked up from {slot_from.position_id}."))
        # 7. Calculate time to extend to source X
        time_extend_1 = self._get_time_x(slot_from.x)
        self.current_move_sequence.append((time_extend_1, "update_x_position", (slot_from.x,), f"PICKUP: Extending to X={slot_from.x}."))
        # 8. Calculate time to move Y to source
        time_y_pickup = self._get_time_y(slot_from.y)
        self.current_move_sequence.append((time_y_pickup, "update_y_position", (slot_from.y,), f"PICKUP: Moving Y to {slot_from.position_id}."))
        
        return True
    
    # ---------------------------------------------------------------------
    # HIGH-LEVEL COMMAND IMPLEMENTATIONS
    # ---------------------------------------------------------------------
    
    def build_enqueue_sequence(self, tray_id: str) -> bool:
        """
        Builds the sequence to move a specific tray from storage to the empty queue slot.
        """
        # 1. Find the source slot (in storage)
        slot_from = self.wh.find_slot_by_tray_id(tray_id)
        # 2. Find the destination slot (the queue)
        slot_to = self.wh.get_empty_queue_slot()

        if not slot_from:
            logging.error(f"Enqueue failed: Tray ID {tray_id} not found in warehouse.")
            return False
        
        # Ensure the found slot is not already the queue or bay
        if slot_from.position_id.startswith("queue_") or slot_from.position_id == "in_view":
            logging.error(f"Enqueue failed: Tray ID {tray_id} is already in the queue or bay.")
            return False
            
        if not slot_to:
            logging.error("Enqueue failed: Queue slot is occupied.")
            return False
            
        logging.info(f"Building ENQUEUE sequence: {slot_from.position_id} -> {slot_to.position_id}")
        return self._build_sequence_internal(slot_from, slot_to)

    def build_send_back_sequence(self) -> bool:
        """
        Builds the sequence to move the tray from the occupied bay (in_view_slot) back to empty storage.
        """
        # 1. Source: Must be the occupied Bay slot (in_view_slot)
        slot_from = self.wh.get_occupied_bay_slot()
        # 2. Destination: Must be an empty Storage slot
        slot_to = self.wh.find_empty_storage_slot()

        if not slot_from:
            logging.error("Send Back failed: Bay (in_view_slot) is empty.")
            return False
        if not slot_to:
            logging.error("Send Back failed: Warehouse storage is full.")
            return False

        logging.info(f"Building SEND_BACK sequence: {slot_from.position_id} -> {slot_to.position_id}")
        return self._build_sequence_internal(slot_from, slot_to)

    def build_extract_sequence(self) -> bool:
        """
        Builds the sequence to move the first tray from the occupied queue slot to the extraction bay (in_view_slot).
        This command does not accept a tray_id.
        """
        # 1. Source: Find the first occupied slot in the queue
        slot_from = self.wh.get_occupied_queue_slot()
        
        if not slot_from:
            logging.error("Extract failed: Queue is currently empty.")
            return False
        
        # 2. Destination: The extraction bay (in_view_slot)
        slot_to = self.wh.get_tray_bay_slot() 

        if not slot_to:
            logging.error("Extract failed: Extraction bay slot is invalid.")
            return False
            
        logging.info(f"Building EXTRACT sequence: {slot_from.position_id} -> {slot_to.position_id} (to In-View Bay)")
        
        return self._build_sequence_internal(slot_from, slot_to)

    # ---------------------------------------------------------------------
    # EXECUTION INTERFACE
    # ---------------------------------------------------------------------

    def get_next_step(self):
        """ Returns (next_step_time, function, arguments, message) """
        if not self.current_move_sequence:
            return None, None, None, None
        return self.current_move_sequence.pop()
    
    def execute_step(self, function_name, args):
        """ Executes the logical/physical step requested by LF. """
        platform = self.wh.platform
        try:
            method = getattr(platform, function_name)
            return method(*args)
        except (AttributeError,ValueError,ZeroDivisionError) as e:
            error_type=type(e).__name__
            logging.error(f"[EXECUTION FAIL] Function: {function_name}, Error Type: {error_type} - {e}")
            return False

    # ---------------------------------------------------------------------
    # STATE MANAGEMENT
    # ---------------------------------------------------------------------

    def set_busy(self): self.wh.set_busy()
    
    def set_idle(self): 
        self.current_move_sequence = []
        self.wh.set_idle()
        
    def is_ready(self) -> bool: return self.wh.is_ready()