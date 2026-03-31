from egglog import *

class Action(Expr):
    @classmethod
    def update_y_position(cls, target_y: f64Like) -> "Action": ...
    
    @classmethod
    def update_x_position(cls, target_x: f64Like) -> "Action": ...
    
    @classmethod
    def pick_up_from(cls) -> "Action": ...
    
    @classmethod
    def place_into(cls) -> "Action": ...
    
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

    

egraph = EGraph()
current_y, target_y = vars_("current_y target_y", f64)
current_x, target_x = vars_("current_x target_x", f64)
busy, has_tray, slot_empty = vars_("busy has_tray slot_empty", bool)
command = vars_("command", Command)



"""
Registers the rewrite rules for the Warehouse state machine.
Handles safety, fetch (pickup) sequences, and deliver (place) sequences.
"""
egraph.register(
    # If busy, do nothing.
    rewrite(
        WarehouseState(current_y, current_x, has_tray, bool_(True), slot_empty, command).get_action()
    ).to(
        Action.wait()
    ),
    
    # --- FETCH PHASE ---
    
    # Align Y
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        current_y != target_y 
    ),

    # Extend X
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        (current_x != target_x) & (current_y == target_y)
    ),

    # Pick up tray
    rewrite(
        WarehouseState(current_y, current_x, bool_(False), bool_(False), bool_(False), Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.pick_up_from(),
        (current_y == target_y) & (current_x == target_x)
    ),

    # --- DELIVER PHASE ---
    
    # Align Y
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        current_y != target_y 
    ),

    # Extend X
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        (current_x != target_x) & (current_y == target_y)
    ),

    # Place tray
    rewrite(
        WarehouseState(current_y, current_x, bool_(True), bool_(False), bool_(True), Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.place_into(),
        (current_y == target_y) & (current_x == target_x)
    ),

    # If no command, do nothing
    rewrite(
        WarehouseState(current_y, current_x, has_tray, busy, slot_empty, Command.idle()).get_action()
    ).to(
        Action.wait()
    ),
)


def get_next_action_from_egglog(
    curr_y: float,
    curr_x: float,
    is_holding_tray: bool,
    is_busy: bool,
    is_target_empty: bool,
    cmd_type: str,           # "FETCH", "DELIVER", or "IDLE"
    target_x: float = 0.0,
    target_y: float = 0.0
) -> tuple[str, tuple]:      # Returns (function_name, arguments)
    """
    Bridge function: Python -> Egglog -> Python 
    """
    
    # INPUT TO EGGLOG COMMAND
    if cmd_type == "FETCH":
        cmd_expr = Command.fetch_from(f64(target_x), f64(target_y))
    elif cmd_type == "DELIVER":
        cmd_expr = Command.deliver_to(f64(target_x), f64(target_y))
    else:
        cmd_expr = Command.idle()

    state_query = WarehouseState(
        f64(curr_y),
        f64(curr_x),
        bool_(is_holding_tray),
        bool_(is_busy),
        bool_(is_target_empty),
        cmd_expr
    ).get_action()

    
    egraph.let("query", state_query)
    egraph.run(10) # 10 iterations
    best_action = egraph.extract(state_query)

    # TRANSLATE EGGLOG OUTPUT TO PYTHON
    action_str = str(best_action)

    if "update_y_position" in action_str:
        return "update_y_position", (target_y,)
    
    elif "update_x_position" in action_str:
        return "update_x_position", (target_x,)
    
    elif "pick_up_from" in action_str:
        return "pick_up_from", ()
    
    elif "place_into" in action_str:
        return "place_into", ()
        
    else:
        return "wait", ()