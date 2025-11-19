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

    def build_move_sequence(self,slot_from:Slot, slot_to:Slot):
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





