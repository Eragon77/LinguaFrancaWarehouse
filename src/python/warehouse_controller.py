from warehouse import Warehouse
from tray import Tray
from warehouse_platform import Platform
from slot import Slot
import logging

class WarehouseController:
    def __init__(self, warehouse):
        self.wh=warehouse
        self.current_move_sequence = []


        # TIME CALCULATION HELPERS

    def _get_time_y(self, target_y:float)->float:
            platform=self.wh.platform
            """Calculates vertical move time for platform to reach target y position."""
            d = abs(target_y - platform.curr_y)
            speed = platform.speed_y
            return d / speed
    
    def _get_time_x(self, target_x:float)->float:
            """Calculates horizontal move time for platform to reach target x position."""
            platform=self.wh.platform
            d = abs(target_x - platform.curr_x)
            speed = platform.extract_speed
            return d / speed 
    
    # MOVEMENT SEQUENCE

    def build_move_sequence(self,slot_from:Slot, slot_to:Slot, is_rollback:bool=False):
        """
        Builds the sequence of operations. 
        The list is a STACK (LIFO), so we append the LAST step first.
        Sequence: Place (Y, X, Action, Retract) <- Pickup (Retract, Action, X, Y)
        """
        
        self.current_move_sequence=[]

        # 8. Retract X to 0 
        time_retract_2 = self._get_time_x(0.0)
        self.current_move_sequence.append((time_retract_2, "update_x_position", (0.0,), "PLACE: Retraction complete. IDLE."))

        # 7. Place Action (Instant)
        self.current_move_sequence.append((0.0, "place_into", (slot_to,), f"PLACE: Tray placed into {slot_to.position_id}."))

        # 6. Extend X to slot_to
        time_extend_2 = self._get_time_x(slot_to.x)
        self.current_move_sequence.append((time_extend_2, "update_x_position", (slot_to.x,), f"PLACE: Extending to X={slot_to.x}."))

        # 5. Move Y to slot_to
        time_y_place = self._get_time_y(slot_to.y)
        self.current_move_sequence.append((time_y_place, "update_y_position", (slot_to.y,), f"PLACE: Moving Y to {slot_to.position_id}."))


        if not is_rollback:
            # 4. Retract X to 0
            time_retract_1 = self._get_time_x(0.0)
            self.current_move_sequence.append((time_retract_1, "update_x_position", (0.0,), "PICKUP: Retraction complete."))

            # 3. Pickup Action (Instant)
            self.current_move_sequence.append((0.0, "pick_up_from", (slot_from,), f"PICKUP: Tray picked up from {slot_from.position_id}."))

            # 2. Extend X to slot_from
            time_extend_1 = self._get_time_x(slot_from.x)
            self.current_move_sequence.append((time_extend_1, "update_x_position", (slot_from.x,), f"PICKUP: Extending to X={slot_from.x}."))

            # 1. Move Y to slot_from (PRIMA AZIONE DA ESEGUIRE)
            time_y_pickup = self._get_time_y(slot_from.y)
            self.current_move_sequence.append((time_y_pickup, "update_y_position", (slot_from.y,), f"PICKUP: Moving Y to {slot_from.position_id}."))
            
            self.last_pickup_slot = slot_from

        return self.current_move_sequence
    
    # In python/warehouse_controller.py

    def _get_safe_rollback_destination(self):
        """
        Controlla se lo slot di origine (last_pickup_slot) è libero. 
        Se sì, torna lì; altrimenti, trova un nuovo slot vuoto.
        """
        # 1. Prova a tornare all'origine se è vuota
        if self.last_pickup_slot and self.last_pickup_slot.tray is None:
            return self.last_pickup_slot
        
        # 2. L'origine è occupata/sconosciuta -> Cerca un nuovo rifugio
        logging.warning("[Controller] Original slot occupied or unknown. Finding new home for rollback.")
        return self.wh.find_empty_storage_slot()

    def build_rollback_sequence(self):
        """
        Dedicated Rollback sequence builder.
        """
        self.current_move_sequence = []
        platform = self.wh.platform
        
        # 1. Determine the safe destination slot
        slot_to_return = self._get_safe_rollback_destination()

        if slot_to_return is None:
            # Edge case: Warehouse 100% full AND original slot taken.
            # The only thing we can do is retract the fork for safety.
            logging.error("[Controller] CRITICAL: Warehouse full! Cannot complete rollback return.")
            time_retract = self._get_time_x(0.0)
            self.current_move_sequence.append((time_retract, "update_x_position", (0.0,), "ROLLBACK: Full House Retract."))
            return self.current_move_sequence
            
        # 2. Build the PLACE sequence (movement to put the tray back)
        
        # 8. Retract X to 0
        time_retract_2 = self._get_time_x(0.0)
        self.current_move_sequence.append((time_retract_2, "update_x_position", (0.0,), "ROLLBACK: Retraction complete. System Idle."))

        # 7. Place Action (Instant)
        self.current_move_sequence.append((0.0, "place_into", (slot_to_return,), f"ROLLBACK: Tray placed into safe slot {slot_to_return.position_id}."))

        # 6. Extend X to target
        time_extend_2 = self._get_time_x(slot_to_return.x)
        self.current_move_sequence.append((time_extend_2, "update_x_position", (slot_to_return.x,), f"ROLLBACK: Extending to X={slot_to_return.x}."))

        # 5. Move Y to target
        time_y_place = self._get_time_y(slot_to_return.y)
        self.current_move_sequence.append((time_y_place, "update_y_position", (slot_to_return.y,), f"ROLLBACK: Moving Y to {slot_to_return.position_id}."))
        
        return self.current_move_sequence
         
    
    def get_next_step(self):
        """
        Pops and returns the next step in the current move sequence.
        Each step is a tuple: (time_to_wait, method_name, method_args, log_message)
        """
        if not self.current_move_sequence:
             return None, None, None, None
        return self.current_move_sequence.pop()
    
    def execute_step(self, function_name, args):
        """
        Executes a single step in the move sequence.
        """
        platform=self.wh.platform
        try:
             method=getattr(platform,function_name)
             success=method(*args)
             return success
        except AttributeError:
             return False
    
    def set_busy(self):
        """Marks the warehouse as busy."""
        self.wh.set_busy()

    def set_idle(self):
        """Marks the warehouse as idle and clears the current move sequence."""
        self.current_move_sequence = []
        self.wh.set_idle()

    def is_ready(self)->bool:
         """Checks if the warehouse is ready"""
         return self.wh.is_ready()

    def _get_safe_rollback_destination(self):
        """
        Checks if origin slot is empty and returns tray to its original slot if so.
        Otherwise finds a new empty storage slot.
        """
        if self.last_pickup_slot and self.last_pickup_slot.tray is None:
            return self.last_pickup_slot
        logging.warning("[Controller] Original slot occupied or unknown. Finding new home for rollback.")
        return self.wh.find_empty_storage_slot()
    
    def get_enqueue_slot(self,tray_id):
         
        slot_from = self.wh.get_slot_by_tray_id(tray_id)
        slot_to = self.wh.get_empty_queue_slot()

        if not slot_from: logging.error(f"Tray ID {tray_id} not found")
        if not slot_to: logging.error("Queue is busy")

        return slot_from, slot_to
    
    def get_send_back_slots(self):
        slot_from=self.wh.get_occupied_queue_slot()
        slot_to=self.wh.find_empty_storage_slot()

        if not slot_from: logging.error("No occupied queue slot found")
        if not slot_to: logging.error("No empty storage slot available")

        return slot_from, slot_to