from egglog import *

class Action(Expr):
    # Maps to Platform.update_y_position(new_y)
    @classmethod
    def update_y_position(cls, target_y: f64Like) -> "Action": ...
    
    # Maps to Platform.update_x_position(new_x)
    @classmethod
    def update_x_position(cls, target_x: f64Like) -> "Action": ...
    
    # Maps to Platform.pick_up_from(slot)
    @classmethod
    def pick_up_from(cls) -> "Action": ...
    
    # Maps to Platform.place_into(slot)
    @classmethod
    def place_into(cls) -> "Action": ...
    
    # No action
    @classmethod
    def wait(cls) -> "Action": ...


class Command(Expr):
    @classmethod
    def fetch_from(cls, source_x: f64Like, source_y: f64Like) -> "Command": ...

    @classmethod
    def deliver_to(cls, dest_x: f64Like, dest_y: f64Like) -> "Command": ...
    
    @classmethod
    def idle(cls) -> "Command": ...


class WarehouseState(Expr):
    def __init__(
        self, 
        curr_y: f64Like,             
        curr_x: f64Like,             
        is_holding_tray: bLike,      
        is_busy: bLike,              
        is_target_slot_empty: bLike, 
        cmd: Command
    ) -> None: ...
    
    def get_action(self) -> Action: ...

    

egraph=EGraph()

current_y,target_y=vars_("current_y target_y",f64)

current_x, target_x= vars_("current_x target_x",f64)

busy,has_tray, slot_empty=vars_("busy has_tray slot_empty", bool)

command=vars_("command",Command)



"""
Registers the rewrite rules for the Warehouse state machine.
Handles safety, fetch (pickup) sequences, and deliver (place) sequences.
"""
egraph.register(
    # If motors are moving (busy=True), do nothing.
    rewrite(
        WarehouseState(current_y, current_x, has_tray, bool_(True), slot_empty, command).get_action()
    ).to(
        Action.wait()
    ),
    
    # --- FETCH PHASE ---
    
    # Move Y to target
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        current_y != target_y 
    ),

    # Move X to target (Y must be reached)
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        (current_x != target_x) & (current_y == target_y)
    ),

    # Pick up tray (Y and X reached, slot must NOT be empty)
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), bool_(False), Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.pick_up_from(),
        (current_y == target_y) & (current_x == target_x)
    ),

    # --- DELIVER PHASE ---
    
    # Move Y to target
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        current_y != target_y 
    ),

    # Move X to target (Y must be reached)
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        (current_x != target_x) & (current_y == target_y)
    ),

    # Place tray (Y and X reached, slot MUST be empty)
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), bool_(True), Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.place_into(),
        (current_y == target_y) & (current_x == target_x)
    ),

    #If no command do nothing
    rewrite(
        WarehouseState(current_y, current_x, has_tray, busy, slot_empty, Command.idle()).get_action()
    ).to(
        Action.wait()
    ),
)