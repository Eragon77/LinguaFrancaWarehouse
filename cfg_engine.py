# mypy: disable-error-code="empty-body"
from __future__ import annotations
from egglog import *


# --- Symbolic types ---

class Action(Expr):
    """Possible physical actions the robot arm can take."""
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
    """High-level mission commands issued to the warehouse controller."""
    @classmethod
    def fetch_from(cls, source_x: f64Like, source_y: f64Like) -> Command: ...

    @classmethod
    def deliver_to(cls, dest_x: f64Like, dest_y: f64Like) -> Command: ...
    
    @classmethod
    def idle(cls) -> Command: ...


class WarehouseState(Expr):
    """Snapshot of the warehouse physical state at a given tick."""
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


# --- Variable declarations  ---

current_y, target_y = vars_("current_y target_y", f64)
current_x, target_x = vars_("current_x target_x", f64)
busy, has_tray, slot_empty = vars_("busy has_tray slot_empty", Bool)
command, = vars_("command", Command)

T = Bool(True)
F = Bool(False)


# --- Rewrite rules ---

WAREHOUSE_RULES = (
    # If the arm is busy, always wait
    rewrite(
        WarehouseState(current_y, current_x, has_tray, T, slot_empty, command).get_action()
    ).to(
        Action.wait()
    ),

    # FETCH: move Y first if not at target row
    rewrite(
        WarehouseState(current_y, current_x, F, F, slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        ne(current_y).to(target_y),
    ),

    # FETCH: move X once Y is aligned
    rewrite(
        WarehouseState(current_y, current_x, F, F, slot_empty, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        ne(current_x).to(target_x),
        eq(current_y).to(target_y),
    ),

    # FETCH: pick up when arm is exactly at target position
    rewrite(
        WarehouseState(current_y, current_x, F, F, F, Command.fetch_from(target_x, target_y)).get_action()
    ).to(
        Action.pick_up_from(),
        eq(current_y).to(target_y),
        eq(current_x).to(target_x),
    ),

    # DELIVER: move Y first if not at destination row
    rewrite(
        WarehouseState(current_y, current_x, T, F, slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_y_position(target_y),
        ne(current_y).to(target_y),
    ),

    # DELIVER: move X once Y is aligned
    rewrite(
        WarehouseState(current_y, current_x, T, F, slot_empty, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.update_x_position(target_x),
        ne(current_x).to(target_x),
        eq(current_y).to(target_y),
    ),

    # DELIVER: place tray when at destination and slot is empty
    rewrite(
        WarehouseState(current_y, current_x, T, F, T, Command.deliver_to(target_x, target_y)).get_action()
    ).to(
        Action.place_into(),
        eq(current_y).to(target_y),
        eq(current_x).to(target_x),
    ),

    # IDLE: nothing to do, just wait
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
    cmd_type: str,
    target_x: float = 0.0,
    target_y: float = 0.0
) -> tuple[str, tuple]:
    """Return the next action to execute."""

    # Cast inputs to float
    curr_y   = float(curr_y)
    curr_x   = float(curr_x)
    target_x = float(target_x)
    target_y = float(target_y)

    # Build command
    if cmd_type == "FETCH":
        cmd_expr = Command.fetch_from(f64(target_x), f64(target_y))
    elif cmd_type == "DELIVER":
        cmd_expr = Command.deliver_to(f64(target_x), f64(target_y))
    else:
        cmd_expr = Command.idle()

    # Build query
    state_query = WarehouseState(
        f64(curr_y),
        f64(curr_x),
        Bool(is_holding_tray),
        Bool(is_busy),
        Bool(is_target_empty),
        cmd_expr
    ).get_action()

    # Fresh e-graph per query to avoid cross-call interference
    egraph = EGraph()
    egraph.register(*WAREHOUSE_RULES)
    egraph.let("query", state_query)
    egraph.run(10)
    best_action = egraph.extract(state_query)

    # Map symbolic result back to a Python-friendly action string
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