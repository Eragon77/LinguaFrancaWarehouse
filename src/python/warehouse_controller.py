import logging
from typing import Optional
from warehouse_platform import Platform
from slot import Slot
from cfg_engine import get_next_action_from_egglog

class WarehouseController:
    def __init__(self, warehouse):
        self.wh = warehouse
        self.current_mission: str = "IDLE"  # Can be "IDLE", "FETCH", "DELIVER"
        self.source_slot: Optional[Slot] = None
        self.dest_slot: Optional[Slot] = None

    # ---------
    # API / COMMAND BUILDERS
    # ---------
    
    def build_enqueue_sequence(self, tray_id: str) -> bool:
        """Sets the target slots for an Enqueue operation and starts the FETCH mission."""
        slot_from = self.wh.find_slot_by_tray_id(tray_id)
        slot_to = self.wh.get_empty_queue_slot()

        if not slot_from:
            logging.error(f"Enqueue failed: Tray ID {tray_id} not found.")
            return False
        if slot_from.position_id.startswith("queue_") or slot_from.position_id == "in_view":
            logging.error(f"Enqueue failed: Tray ID {tray_id} is already in queue or bay.")
            return False
        if not slot_to:
            logging.error("Enqueue failed: Queue slot is occupied.")
            return False
            
        logging.info(f"Starting ENQUEUE: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def build_sendback_sequence(self) -> bool:
        """Sets the target slots for a Send Back operation and starts the FETCH mission."""
        slot_from = self.wh.get_occupied_bay_slot()
        slot_to = self.wh.find_empty_storage_slot()

        if not slot_from:
            logging.error("Send Back failed: Bay is empty.")
            return False
        if not slot_to:
            logging.error("Send Back failed: Storage is full.")
            return False

        logging.info(f"Starting SEND_BACK: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def build_extract_sequence(self) -> bool:
        """Sets the target slots for an Extract operation and starts the FETCH mission."""
        slot_from = self.wh.get_occupied_queue_slot()
        slot_to = self.wh.get_tray_bay_slot() 

        if not slot_from:
            logging.error("Extract failed: Queue is empty.")
            return False
        if not slot_to:
            logging.error("Extract failed: Bay slot invalid.")
            return False
            
        logging.info(f"Starting EXTRACT: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def _start_mission(self, slot_from: Slot, slot_to: Slot):
        """Internal helper to set mission targets."""
        self.source_slot = slot_from
        self.dest_slot = slot_to
        self.current_mission = "FETCH"
        self.set_busy()

    # ---------------------------------------------------------------------
    # EXECUTION INTERFACE
    # ---------------------------------------------------------------------

    def tick(self) -> bool:
        """
        Called periodically by Lingua Franca.
        Evaluates the current physical state, asks Egglog for the next action, and executes it.
        """
        if self.current_mission == "IDLE":
            return False

        platform = self.wh.platform
        
        # Determine targets
        target_slot = self.source_slot if self.current_mission == "FETCH" else self.dest_slot
        
        # Query Egglog for the next action
        func_name, args = get_next_action_from_egglog(
            curr_y=platform.curr_y,
            curr_x=platform.curr_x,
            is_holding_tray=platform.is_holding_tray(),
            is_busy=False,
            is_target_empty=(target_slot.tray is None),
            cmd_type=self.current_mission,
            target_x=target_slot.x,
            target_y=target_slot.y
        )

        # Execute the action if it's not a wait
        if func_name != "wait":
            self.execute_step(func_name, args)
            
            # Handle Phase Transitions
            if func_name == "pick_up_from":
                logging.info("Fetch complete. Switching to DELIVER phase.")
                self.current_mission = "DELIVER"
                
            elif func_name == "place_into":
                logging.info("Deliver complete. Mission finished.")
                self.set_idle()
                
        return True

    def execute_step(self, function_name, args):
        """ Executes the physical step on the platform. """
        platform = self.wh.platform
        try:
            # For pickup/place, we need to pass the actual slot object
            if function_name == "pick_up_from":
                return platform.pick_up_from(self.source_slot)
            elif function_name == "place_into":
                return platform.place_into(self.dest_slot)
            
            # For movements, pass the coordinates
            method = getattr(platform, function_name)
            return method(*args)
            
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            error_type = type(e).__name__
            logging.error(f"[EXECUTION FAIL] Function: {function_name}, Error: {error_type} - {e}")
            return False

    # ---------------------------------------------------------------------
    # STATE MANAGEMENT
    # ---------------------------------------------------------------------

    def set_busy(self): self.wh.set_busy()
    
    def set_idle(self): 
        self.current_mission = "IDLE"
        self.source_slot = None
        self.dest_slot = None
        self.wh.set_idle()
        
    def is_ready(self) -> bool: return self.wh.is_ready()

    #----------------------------------------
    # ICE FROST (?) methods.
    #----------------------------------------

    def extract(self, TrayNumber: int=0)->bool:
        return self.build_extract_sequence()
    
    def enqueueTray(self,TrayNumber:int)->bool:
        return self.build_enqueue_sequence(str(TrayNumber))
    
    def sendback(self,TrayNumber: int=0)->bool:
        return self.build_sendback_sequence()
    
    def requestInfoBay(self) -> str:
        import json
        tray_id = self.wh.tray_in_bay
        status = "Occupied" if tray_id > 0 else "Empty"
        return json.dumps({"status": status, "tray_id": tray_id})
    
    def clearBay(self) -> bool:
        bay_slot = self.wh.get_tray_bay_slot()
        if bay_slot and bay_slot.tray:
            logging.info(f"CLEAR BAY: Removing tray {bay_slot.tray.tray_id}.")
            try:
                bay_slot.remove_tray()
                return True
            except ValueError:
                return False
        return True