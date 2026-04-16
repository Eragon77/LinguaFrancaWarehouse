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

    @property
    def is_busy(self) -> bool:
        """System is busy if mission is not idle."""
        return self.current_mission != "IDLE"

    # ---------
    # API / COMMAND BUILDERS
    # ---------
    
    def build_enqueue_sequence(self, tray_id: str) -> bool:
        slot_from = self.wh.find_slot_by_tray_id(tray_id)
        slot_to = self.wh.get_empty_queue_slot()
        if not slot_from or not slot_to: return False
        
        logging.info(f"Starting ENQUEUE: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def build_sendback_sequence(self) -> bool:
        slot_from = self.wh.get_occupied_bay_slot()
        slot_to = self.wh.find_empty_storage_slot()
        if not slot_from or not slot_to: 
            logging.error(f"[REJECTED] Sendback impossible: From={slot_from}, To={slot_to}")
            return False

        logging.info(f"Starting SEND_BACK: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def build_extract_sequence(self) -> bool:
        slot_from = self.wh.get_occupied_queue_slot()
        slot_to = self.wh.get_tray_bay_slot() 
        if not slot_from or not slot_to: return False
            
        logging.info(f"Starting EXTRACT: {slot_from.position_id} -> {slot_to.position_id}")
        self._start_mission(slot_from, slot_to)
        return True

    def _start_mission(self, slot_from: Slot, slot_to: Slot):
        self.source_slot = slot_from
        self.dest_slot = slot_to
        self.current_mission = "FETCH"

    # ---------------------------------------------------------------------
    # EXECUTION INTERFACE
    # ---------------------------------------------------------------------

    def tick(self) -> bool:
        if not self.is_busy:
            return False

        platform = self.wh.platform
        target_slot = self.source_slot if self.current_mission == "FETCH" else self.dest_slot
        
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

        if func_name != "wait":
            self.execute_step(func_name, args)
            
            if func_name == "pick_up_from":
                logging.info("Fetch complete. Switching to DELIVER phase.")
                self.current_mission = "DELIVER"
                
            elif func_name == "place_into":
                logging.info("Deliver complete. Mission finished.")
                self.set_idle()
                
        return True

    def execute_step(self, function_name, args):
        platform = self.wh.platform
        try:
            if function_name == "pick_up_from":
                return platform.pick_up_from(self.source_slot)
            elif function_name == "place_into":
                return platform.place_into(self.dest_slot)
            
            method = getattr(platform, function_name)
            return method(*args)
        except Exception as e:
            logging.error(f"[EXECUTION FAIL] {function_name}: {e}")
            return False

    # ---------------------------------------------------------------------
    # STATE MANAGEMENT
    # ---------------------------------------------------------------------

    def set_idle(self): 
        self.current_mission = "IDLE"
        self.source_slot = None
        self.dest_slot = None
        
    def is_ready(self) -> bool: 
        return not self.is_busy

    # --- API FROST ---
    def extract(self, TrayNumber: int=0): return self.build_extract_sequence()
    def enqueueTray(self, TrayNumber: int): return self.build_enqueue_sequence(str(TrayNumber))
    def sendback(self, TrayNumber: int=0): return self.build_sendback_sequence()
    
    def requestInfoBay(self) -> str:
        import json
        return json.dumps({"status": "Occupied" if self.wh.tray_in_bay > 0 else "Empty", "tray_id": self.wh.tray_in_bay})

    def clearBay(self) -> bool:
        bay_slot = self.wh.get_tray_bay_slot()
        if bay_slot and bay_slot.tray:
            bay_slot.remove_tray()
            return True
        return True