import logging
from typing import Optional
from enum import Enum
from slot import Slot
from cfg_engine import get_next_action_from_egglog


class MissionState(Enum):
    """Mission states."""

    IDLE = "idle"
    FETCH = "fetch"
    DELIVER = "deliver"


class WarehouseController:
    """Controller for warehouse robot missions using egglog planning."""

    def __init__(self, warehouse):
        """Initialize controller with warehouse reference."""
        self.wh = warehouse
        self.state = MissionState.IDLE
        self.source_slot: Optional[Slot] = None
        self.dest_slot: Optional[Slot] = None
        self.dest_type: Optional[str] = None
        self.locked_target_id: Optional[str] = None
        self.target_tray_id: Optional[int] = None

    @property
    def is_busy(self) -> bool:
        """Return True if a mission is active."""
        return self.state != MissionState.IDLE

    def _start_mission(
        self,
        src: Optional[Slot],
        dst: Optional[Slot],
        dst_type: Optional[str] = None,
        tray_id: Optional[int] = None,
    ):
        """Initialize mission: source/dest slots, phase, lock status."""
        self.source_slot = src
        self.dest_slot = dst
        self.dest_type = dst_type
        self.target_tray_id = tray_id
        self.state = MissionState.FETCH

    # TODO: enqueue any empty tray?
    def build_enqueue_sequence(self, tray_number: int) -> bool:
        """Move tray from storage to empty queue slot."""
        if not self.wh.has_tray(tray_number):
            logging.error(f"Tray {tray_number} non trovato. Impossibile accodare.")
            return False
        logging.info(f"Starting ENQUEUE for tray {tray_number}")
        self._start_mission(None, None, dst_type="queue", tray_id=tray_number)
        return True

    def build_extract_sequence(self, tray_number: int | None = 0) -> bool:
        """If tray_number > 0, extract that tray. Else, extract from queue"""
        dst = self.wh.get_tray_bay_slot()
        if not dst or dst.tray is not None:
            return False

        if tray_number:
            if not self.wh.has_tray(tray_number):
                logging.error(f"Tray {tray_number} not found in warehouse")
                return False
            logging.info(f"Starting EXTRACT of tray {tray_number} from anywhere")
            self._start_mission(None, dst, tray_id=tray_number)
        else:
            src = self.wh.get_occupied_queue_slot()
            if not src:
                return False
            logging.info(f"Starting EXTRACT from queue: {src.slot_id} -> {dst.slot_id}")
            self._start_mission(src, dst)
        return True

    def build_sendback_sequence(self) -> bool:
        """Move tray from bay to any storage slot."""
        src = self.wh.get_occupied_bay_slot()
        if not src:
            logging.error("[REJECTED] SendBack: Bay is empty")
            return False
        logging.info(f"Starting SENDBACK: {src.slot_id} -> storage")
        self._start_mission(src, None, "storage")
        return True

    def build_fetch_any_empty_sequence(self) -> bool:
        """Fetch empty tray and deliver to bay."""
        dst = self.wh.get_tray_bay_slot()
        if not dst or dst.tray is not None:
            return False
        logging.info("Starting FETCH_ANY_EMPTY")
        self._start_mission(None, dst)
        return True

    def tick(self) -> bool:
        """Execute one mission step: query egglog and run action."""
        if not self.is_busy:
            print("Controller IDLE")
            return False

        plat = self.wh.platform
        result = self._get_next_action(plat)

        if result["type"] == "lock":
            self.locked_target_id = result.get("slot_id", "")
            if self.locked_target_id:
                logging.info(f"Locked target: {self.locked_target_id}")
            return True

        if result["type"] == "wait":
            return False

        if not self._execute_action(result, plat):
            logging.error(f"Action failed: {result['type']}")
            self.set_idle()
            return False

        if result["type"] == "pick" and self.state == MissionState.FETCH:
            if not self.source_slot:
                self.source_slot = self.wh.get_slot_at(plat.curr_x, plat.curr_y)
            self.state = MissionState.DELIVER
            logging.info("Transitioned to DELIVER phase")
            return True

        if result["type"] == "place" and self.state == MissionState.DELIVER:
            logging.info("Mission complete")
            self.set_idle()
            return True

        return True

    def _get_next_action(self, plat) -> dict:
        phase = "deliver" if self.state == MissionState.DELIVER else "fetch"

        if self.target_tray_id is not None:
            tid = self.target_tray_id
        elif self.source_slot and self.source_slot.tray:
            tid = int(self.source_slot.tray.tray_id)
        else:
            tid = 0

        if self.dest_slot:
            ttype = self.dest_slot.slot_type
        elif self.locked_target_id:
            locked_slot = self.wh.get_slot_by_id(self.locked_target_id)
            ttype = locked_slot.slot_type if locked_slot else ""
        else:
            ttype = self.dest_type or ""

        if self.state == MissionState.FETCH and (
            self.target_tray_id is not None
            or (self.source_slot and self.source_slot.tray)
        ):
            cmd = "FETCH"
            effective_locked_id = self.locked_target_id or ""
        elif self.state == MissionState.FETCH:
            cmd = "FETCH_ANY_EMPTY"
            effective_locked_id = self.locked_target_id or ""
        elif self.state == MissionState.DELIVER and self.dest_slot:
            cmd = "DELIVER"
            effective_locked_id = self.dest_slot.slot_id
        elif self.state == MissionState.DELIVER and not self.locked_target_id:
            cmd = "SEARCH_TARGET"
            effective_locked_id = ""
        else:
            cmd = "DELIVER"
            effective_locked_id = self.locked_target_id or ""

        return get_next_action_from_egglog(
            warehouse=self.wh,
            cy=plat.curr_y,
            cx=plat.curr_x,
            holding=plat.is_holding_tray(),
            phase=phase,
            cmd_type=cmd,
            target_id=tid,
            target_type=ttype,
            locked_id=effective_locked_id,
        )

    def _execute_action(self, action: dict, plat) -> bool:
        """Execute physical action on platform."""
        try:
            atype = action["type"]

            if atype == "pick":
                target = self.source_slot or self.wh.get_slot_at(
                    plat.curr_x, plat.curr_y
                )
                if not target:
                    logging.error("No slot to pick from")
                    return False
                return plat.pick_up_from(target)

            elif atype == "place":
                target = (
                    self.dest_slot
                    or (
                        self.wh.get_slot_by_id(self.locked_target_id)
                        if self.locked_target_id
                        else None
                    )
                    or self.wh.get_slot_at(plat.curr_x, plat.curr_y)
                )
                if not target:
                    logging.error("No slot to place into")
                    return False
                success = plat.place_into(target)
                if success:
                    self.locked_target_id = None
                return success

            elif atype == "update_y":
                return plat.update_y_position(action["val"])
            elif atype == "update_x":
                return plat.update_x_position(action["val"])

            return True
        except Exception as e:
            logging.error(f"[EXECUTION FAIL] {action['type']}: {e}")
            return False

    def set_idle(self):
        """Reset mission state."""
        self.state = MissionState.IDLE
        self.source_slot = None
        self.dest_slot = None
        self.dest_type = None
        self.target_tray_id = None
        self.locked_target_id = None

    def is_ready(self) -> bool:
        """Return True if idle and can accept new missions."""
        return not self.is_busy

    def extract(self, TrayNumber: int | None = 0) -> bool:
        """Public wrapper for extract mission."""
        return self.build_extract_sequence(TrayNumber)

    def enqueue(self, TrayNumber: int) -> bool:
        """Public wrapper for enqueue mission."""
        return self.build_enqueue_sequence(TrayNumber)

    def sendback(self, TrayNumber: int = 0) -> bool:
        """Public wrapper for sendback mission."""
        return self.build_sendback_sequence()

    def fetch_any_empty(self) -> bool:
        """Public wrapper for fetch_any_empty mission."""
        return self.build_fetch_any_empty_sequence()

    def requestInfoBay(self) -> str:
        """Return bay status as JSON."""
        import json

        return json.dumps(
            {
                "status": "Occupied" if self.wh.tray_in_bay > 0 else "Empty",
                "tray_id": self.wh.tray_in_bay,
            }
        )

    def clearBay(self) -> bool:
        """Remove tray from bay."""
        bay = self.wh.get_tray_bay_slot()
        if bay and bay.tray:
            bay.remove_tray()
        return True
