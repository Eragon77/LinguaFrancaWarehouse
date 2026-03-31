# mypy: disable-error-code="empty-body"
from __future__ import annotations
from egglog import *

class Action(Expr):
    @classmethod
    def update_y_position(cls, target_y: f64Like) -> Action: ...
    
    @classmethod
    def update_x_position(cls, target_x: f64Like) -> Action: ...
    
    @classmethod
    def pick_up_from(cls) -> Action: ...
    
    @classmethod
    def place_into(cls) -> Action: ...
    
    @classmethod
    def wait(cls) -> Action: ...


class Command(Expr):
    @classmethod
    def fetch_from(cls, source_x: f64Like, source_y: f64Like) -> Command: ...

    @classmethod
    def deliver_to(cls, dest_x: f64Like, dest_y: f64Like) -> Command: ...
    
    @classmethod
    def idle(cls) -> Command: ...


class WarehouseState(Expr):
    def __init__(
        self, 
        curr_y: f64Like,             
        curr_x: f64Like,             
        is_holding_tray: BoolLike,      
        is_busy: BoolLike,              
        is_target_slot_empty: BoolLike, 
        cmd: Command
    ) -> None: ...
    
    def get_action(self) -> Action: ...


egraph = EGraph()
current_y, target_y = vars_("current_y target_y", f64)
current_x, target_x = vars_("current_x target_x", f64)
busy, has_tray, slot_empty = vars_("busy has_tray slot_empty", Bool)
command, = vars_("command", Command)

T = Bool(True)
F = Bool(False)

egraph.register(
    # Busy: do nothing.
    rewrite(
        WarehouseState(current_y, current_x, has_tray, T, slot_empty, command).get_action()
    ).to(
        Action.wait()
    ),

    # FETCH 1: align Y before extending on X.
    rewrite(
        WarehouseState(current_y, current_x, F, F, slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        ne(current_y).to(target_y),
    ),

    # FETCH 2: extend X once Y is aligned.
    rewrite(
        WarehouseState(current_y, current_x, F, F, slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        ne(current_x).to(target_x),
        eq(current_y).to(target_y),
    ),

    # FETCH 3: pick up tray when positioned and slot is occupied.
    rewrite(
        WarehouseState(current_y, current_x, F, F, F, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.pick_up_from(),
        eq(current_y).to(target_y),
        eq(current_x).to(target_x),
    ),

    # DELIVER 1: align Y.
    rewrite(
        WarehouseState(current_y, current_x, T, F, slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        ne(current_y).to(target_y),
    ),

    # DELIVER 2: extend X once Y is aligned.
    rewrite(
        WarehouseState(current_y, current_x, T, F, slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        ne(current_x).to(target_x),
        eq(current_y).to(target_y),
    ),

    # DELIVER 3: place tray when fully positioned and destination slot is empty.
    rewrite(
        WarehouseState(current_y, current_x, T, F, T, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.place_into(),
        eq(current_y).to(target_y),
        eq(current_x).to(target_x),
    ),

    # No command: stay idle.
    rewrite(
        WarehouseState(current_y, current_x, has_tray, busy, slot_empty, Command.idle()).get_action()
    ).to(
        Action.wait()
    ),
)


# Unique name per call — egraph.let() names must not collide across calls.
_query_counter = 0

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
    global _query_counter

    curr_y   = float(curr_y)
    curr_x   = float(curr_x)
    target_x = float(target_x)
    target_y = float(target_y)

    if cmd_type == "FETCH":
        cmd_expr = Command.fetch_from(f64(target_x), f64(target_y))
    elif cmd_type == "DELIVER":
        cmd_expr = Command.deliver_to(f64(target_x), f64(target_y))
    else:
        cmd_expr = Command.idle()

    state_query = WarehouseState(
        f64(curr_y),
        f64(curr_x),
        Bool(is_holding_tray),
        Bool(is_busy),
        Bool(is_target_empty),
        cmd_expr
    ).get_action()

    query_name = f"query_{_query_counter}"
    _query_counter += 1

    egraph.let(query_name, state_query)
    egraph.run(10)
    best_action = egraph.extract(state_query)

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