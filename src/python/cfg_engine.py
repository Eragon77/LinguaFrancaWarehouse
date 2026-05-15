from __future__ import annotations
from egglog import *


class Tray(Expr):
    """Represents a tray with ID and fullness status."""

    def __init__(self, tray_id: i64Like, is_full: BoolLike) -> None: ...


class Slot(Expr):
    """Represents a warehouse slot with position, type, and optional tray."""

    def __init__(
        self,
        slot_id: StringLike,
        slot_type: SlotType,
        x: f64Like,
        y: f64Like,
        tray: OptionTray,
    ) -> None: ...


class OptionTray(Expr):
    """Optional tray container (none or some)."""

    @classmethod
    def none(cls) -> OptionTray: ...
    @classmethod
    def some(cls, tray: Tray) -> OptionTray: ...


class SlotType(Expr):
    """Type of slot: storage, queue, or bay."""

    @classmethod
    def storage(cls) -> SlotType: ...
    @classmethod
    def queue(cls) -> SlotType: ...
    @classmethod
    def bay(cls) -> SlotType: ...


class MissionPhase(Expr):
    """Explicit mission phase for state tracking."""

    @classmethod
    def fetch(cls) -> MissionPhase: ...
    @classmethod
    def deliver(cls) -> MissionPhase: ...


class LockedTarget(Expr):
    """Declares a slot ID as locked for delivery."""

    def __init__(self, slot_id: StringLike) -> None: ...


class ActionResult(Expr):
    """Typed action result with embedded parameters."""

    @classmethod
    def update_y(cls, val: f64Like) -> ActionResult: ...
    @classmethod
    def update_x(cls, val: f64Like) -> ActionResult: ...
    @classmethod
    def pick(cls) -> ActionResult: ...
    @classmethod
    def place(cls) -> ActionResult: ...
    @classmethod
    def lock(cls, slot_id: StringLike) -> ActionResult: ...
    @classmethod
    def wait(cls) -> ActionResult: ...


class Command(Expr):
    """High-level commands given to the robot."""

    @classmethod
    def fetch_tray(cls, tray_id: i64Like) -> Command: ...
    @classmethod
    def deliver_to(cls, stype: SlotType) -> Command: ...
    @classmethod
    def fetch_any_empty(cls) -> Command: ...
    @classmethod
    def search_target(cls, stype: SlotType) -> Command: ...
    @classmethod
    def idle(cls) -> Command: ...


class RobotState(Expr):
    """Robot state with explicit mission phase."""

    def __init__(
        self,
        curr_y: f64Like,
        curr_x: f64Like,
        holding: BoolLike,
        phase: MissionPhase,
        cmd: Command,
    ) -> None: ...
    def next_action(self) -> ActionResult: ...


cy, cx, sy, sx = vars_("cy cx sy sx", f64)
holding, is_f = vars_("holding is_f", Bool)
(cmd,) = vars_("cmd", Command)
(sid,) = vars_("sid", String)
(stype,) = vars_("stype", SlotType)
(tid,) = vars_("tid", i64)
(result,) = vars_("result", ActionResult)
(phase,) = vars_("phase", MissionPhase)
(locked_id,) = vars_("locked_id", String)

T, F = Bool(True), Bool(False)

WAREHOUSE_RULES = (
    # SEARCH TARGET: lock empty slot
    rule(
        eq(result).to(
            RobotState(cy, cx, T, phase, Command.search_target(stype)).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.none()),
    ).then(union(result).with_(ActionResult.lock(sid))),
    
    # FETCH: retract X
    rule(
        eq(result).to(
            RobotState(
                cy, cx, F, MissionPhase.fetch(), Command.fetch_tray(tid)
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, is_f))),
        cy != sy,
        cx != f64(0.0),
    ).then(union(result).with_(ActionResult.update_x(f64(0.0)))),

    # FETCH: move Y
    rule(
        eq(result).to(
            RobotState(
                cy, cx, F, MissionPhase.fetch(), Command.fetch_tray(tid)
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, is_f))),
        cy != sy,
        cx == f64(0.0),
    ).then(union(result).with_(ActionResult.update_y(sy))),

    # FETCH: move X
    rule(
        eq(result).to(
            RobotState(
                sy, cx, F, MissionPhase.fetch(), Command.fetch_tray(tid)
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, is_f))),
        cx != sx,
    ).then(union(result).with_(ActionResult.update_x(sx))),

    # FETCH: pick
    rule(
        eq(result).to(
            RobotState(
                sy, sx, F, MissionPhase.fetch(), Command.fetch_tray(tid)
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, is_f))),
    ).then(union(result).with_(ActionResult.pick())),

    # FETCH_ANY_EMPTY: retract X
    rule(
        eq(result).to(
            RobotState(
                cy, cx, F, MissionPhase.fetch(), Command.fetch_any_empty()
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, F))),
        cy != sy,
        cx != f64(0.0),
    ).then(union(result).with_(ActionResult.update_x(f64(0.0)))),

    # FETCH_ANY_EMPTY: move Y
    rule(
        eq(result).to(
            RobotState(
                cy, cx, F, MissionPhase.fetch(), Command.fetch_any_empty()
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, F))),
        cy != sy,
        cx == f64(0.0),
    ).then(union(result).with_(ActionResult.update_y(sy))),

    # FETCH_ANY_EMPTY: move X
    rule(
        eq(result).to(
            RobotState(
                sy, cx, F, MissionPhase.fetch(), Command.fetch_any_empty()
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, F))),
        cx != sx,
    ).then(union(result).with_(ActionResult.update_x(sx))),

    # FETCH_ANY_EMPTY: pick
    rule(
        eq(result).to(
            RobotState(
                sy, sx, F, MissionPhase.fetch(), Command.fetch_any_empty()
            ).next_action()
        ),
        Slot(sid, stype, sx, sy, OptionTray.some(Tray(tid, F))),
    ).then(union(result).with_(ActionResult.pick())),

    # DELIVER: retract X
    rule(
        eq(result).to(
            RobotState(
                cy, cx, T, MissionPhase.deliver(), Command.deliver_to(stype)
            ).next_action()
        ),
        LockedTarget(locked_id),
        Slot(locked_id, stype, sx, sy, OptionTray.none()),
        cy != sy,
        cx != f64(0.0),
    ).then(union(result).with_(ActionResult.update_x(f64(0.0)))),

    # DELIVER: move Y
    rule(
        eq(result).to(
            RobotState(
                cy, cx, T, MissionPhase.deliver(), Command.deliver_to(stype)
            ).next_action()
        ),
        LockedTarget(locked_id),
        Slot(locked_id, stype, sx, sy, OptionTray.none()),
        cy != sy,
        cx == f64(0.0),
    ).then(union(result).with_(ActionResult.update_y(sy))),

    # DELIVER: move X
    rule(
        eq(result).to(
            RobotState(
                sy, cx, T, MissionPhase.deliver(), Command.deliver_to(stype)
            ).next_action()
        ),
        LockedTarget(locked_id),
        Slot(locked_id, stype, sx, sy, OptionTray.none()),
        cx != sx,
    ).then(union(result).with_(ActionResult.update_x(sx))),

    # DELIVER: place
    rule(
        eq(result).to(
            RobotState(
                sy, sx, T, MissionPhase.deliver(), Command.deliver_to(stype)
            ).next_action()
        ),
        LockedTarget(locked_id),
        Slot(locked_id, stype, sx, sy, OptionTray.none()),
    ).then(union(result).with_(ActionResult.place())),
    
    # IDLE: wait
    rewrite(RobotState(cy, cx, holding, phase, Command.idle()).next_action()).to(
        ActionResult.wait()
    ),
)

def get_next_action_from_egglog(
    warehouse,
    cy: float,
    cx: float,
    holding: bool,
    phase: str,
    cmd_type: str,
    target_id: int = 0,
    target_type: str = "",
    locked_id: str = "",
) -> dict:
    """
    Query egglog for next action. Returns {type, args} with typed fields.
    Phase must be 'fetch' or 'deliver'.
    """
    egraph = EGraph()
    egraph.register(*WAREHOUSE_RULES)

    for s in warehouse._get_all_slots():
        egg_tray = OptionTray.none()
        if s.tray:
            egg_tray = OptionTray.some(Tray(int(s.tray.tray_id), Bool(s.tray.is_full)))

        stype_expr = (
            SlotType.queue()
            if s.slot_type == "queue"
            else SlotType.bay()
            if s.slot_type == "bay"
            else SlotType.storage()
        )
        egraph.register(Slot(s.slot_id, stype_expr, f64(s.x), f64(s.y), egg_tray))

    if locked_id:
        egraph.register(LockedTarget(String(locked_id)))

    phase_expr = MissionPhase.deliver() if phase == "deliver" else MissionPhase.fetch()

    if cmd_type == "FETCH":
        cmd_expr = Command.fetch_tray(i64(target_id))
    elif cmd_type == "DELIVER":
        st_expr = (
            SlotType.queue()
            if target_type == "queue"
            else SlotType.bay()
            if target_type == "bay"
            else SlotType.storage()
        )
        cmd_expr = Command.deliver_to(st_expr)
    elif cmd_type == "FETCH_ANY_EMPTY":
        cmd_expr = Command.fetch_any_empty()
    elif cmd_type == "SEARCH_TARGET":
        st_expr = (
            SlotType.queue()
            if target_type == "queue"
            else SlotType.bay()
            if target_type == "bay"
            else SlotType.storage()
        )
        cmd_expr = Command.search_target(st_expr)
    else:
        cmd_expr = Command.idle()

    query = RobotState(
        f64(cy), f64(cx), Bool(holding), phase_expr, cmd_expr
    ).next_action()
    egraph.register(query)
    egraph.run(10)

    try:
        best = egraph.extract(query)
        s = str(best)

        if "update_y(" in s:
            val = float(
                [
                    x
                    for x in s.replace("(", " ").replace(")", " ").split()
                    if x.replace(".", "").replace("-", "").isdigit()
                ][0]
            )
            return {"type": "update_y", "val": val}
        elif "update_x(" in s:
            val = float(
                [
                    x
                    for x in s.replace("(", " ").replace(")", " ").split()
                    if x.replace(".", "").replace("-", "").isdigit()
                ][0]
            )
            return {"type": "update_x", "val": val}
        elif "pick(" in s:
            return {"type": "pick"}
        elif "place(" in s:
            return {"type": "place"}
        elif "lock(" in s:
            import re

            m = re.search(r'"([^"]*)"', s)
            return {"type": "lock", "slot_id": m.group(1) if m else ""}
        return {"type": "wait"}
    except Exception as e:
        logging.error(f"Egglog extraction failed: {e}")
        return {"type": "wait"}
