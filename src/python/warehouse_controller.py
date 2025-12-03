import logging
from typing import List,Tuple

Step=Tuple[float,str,tuple,str] # (time, function_name, args, message)

class WarehouseController:
    def __init__(self, warehouse):
        self.wh = warehouse
        self.current_move_sequence: List[Step]=[]

    # --- TIME CALCULATION HELPERS ---

    def _compute_time(self,distance:float, speed:float, axis:str)->float:
        if speed<=0:
            logging.error(f"[TIME FAIL] Speed on axis {axis} is less than or equal to zero.")
            return 0.0
        return abs(distance)/speed

    def _get_time_y(self, target_y: float) -> float:
        platform = self.wh.platform
        return self._compute_time(target_y-platform.curr_y, platform.speed_y, "Y")
    
    def _get_time_x(self, target_x: float) -> float:
        platform = self.wh.platform
        return self._compute_time(target_x - platform.curr_x, platform.extract_speed, "X")
    
    # -----------------------
    # Sequence helpers
    # -----------------------
    
    def _add_step(self,duration:float,func:str,args:tuple,msg:str):
        """Adds a step to the move sequence"""
        self.current_move_sequence.append((duration,func,args,msg))

    def _move_x(self, x: float, phase: str):
        t = self._get_time_x(x)
        self._add_step(t, "update_x_position", (x,), f"{phase}: Moving X to {x}.")
    
    def _move_y(self, y: float, phase: str):
        t = self._get_time_y(y)
        self._add_step(t, "update_y_position", (y,), f"{phase}: Moving Y to {y}.")

    def _build_sequence_internal(self, slot_from, slot_to) -> bool:
        """Internal helper to build the PICKUP -> PLACE sequence."""
        if slot_from.tray is None:
            logging.error(f"Sequence Build Failed: Source slot {slot_from.position_id} is empty.")
            return False
            
        self.current_move_sequence = []
        platform=self.wh.platform

        # ------------------------
        # 1. PICKUP PHASE 
        # ------------------------

        self._move_y(slot_from.y, "PICKUP")
        self._move_x(slot_from.x, "PICKUP")

        self._add_step(0.0,"pick_up_from", (slot_from,), f"PICKUP: tray from {slot_from.position_id}.")

        self._move_x(0.0,"PICKUP")

        # -----------------
        # 2. PLACE PHASE 
        # ------------------
        
        self._move_y(slot_to.y, "PLACE")
        self._move_x(slot_to.x, "PLACE")

        self._add_step(0.0, "place_into", (slot_to,), f"PLACE: tray into {slot_to.position_id}.")

        self._move_x(0.0,"PLACE")
        return True
    
    # ---------
    # API
    # ---------
    
    def build_enqueue_sequence(self, tray_id: str) -> bool:
        """
        Builds the sequence to move a specific tray from storage to the empty queue slot.
        """
        slot_from = self.wh.find_slot_by_tray_id(tray_id)
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

    def build_sendback_sequence(self) -> bool:
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
        return self.current_move_sequence.pop(0)
    
    def execute_step(self, function_name, args):
        """ Executes the step requested by LF. """
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


    #----------------------------------------
    # ICE FROST DATAMODEL/WAREHOUSE methods.
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