import pytest
from dataclasses import dataclass
from typing import List, Optional
from cfg_engine import get_next_action_from_egglog


@dataclass
class MockTray:
    tray_id: int
    is_full: bool


@dataclass
class MockSlot:
    slot_id: str
    slot_type: str
    x: float
    y: float
    tray: Optional[MockTray] = None


class MockWarehouse:
    def __init__(self, slots: List[MockSlot]):
        self.slots = slots

    def _get_all_slots(self):
        return self.slots


@pytest.fixture
def basic_warehouse():
    """Create basic layout."""
    return MockWarehouse(
        [
            MockSlot("S1", "storage", 10.0, 20.0, MockTray(tray_id=1, is_full=True)),
            MockSlot("Q1", "queue", 50.0, 60.0, None),
        ]
    )


def test_fetch_move_y(basic_warehouse):
    """Test Y-axis movement."""
    action = get_next_action_from_egglog(
        basic_warehouse,
        cy=0.0,
        cx=0.0,
        holding=False,
        phase="fetch",
        cmd_type="FETCH",
        target_id=1,
    )
    assert action["type"] == "update_y"
    assert action["val"] == 20.0


def test_fetch_move_x(basic_warehouse):
    """Test X-axis movement."""
    action = get_next_action_from_egglog(
        basic_warehouse,
        cy=20.0,
        cx=0.0,
        holding=False,
        phase="fetch",
        cmd_type="FETCH",
        target_id=1,
    )
    assert action["type"] == "update_x"
    assert action["val"] == 10.0


def test_fetch_pick(basic_warehouse):
    """Test pick action."""
    action = get_next_action_from_egglog(
        basic_warehouse,
        cy=20.0,
        cx=10.0,
        holding=False,
        phase="fetch",
        cmd_type="FETCH",
        target_id=1,
    )
    assert action["type"] == "pick"


def test_search_lock(basic_warehouse):
    """Test locking empty slot."""
    action = get_next_action_from_egglog(
        basic_warehouse,
        cy=0.0,
        cx=0.0,
        holding=True,
        phase="deliver",
        cmd_type="SEARCH_TARGET",
        target_type="queue",
    )
    assert action["type"] == "lock"
    assert action["slot_id"] == "Q1"


def test_deliver_move_y(basic_warehouse):
    """Test Y-axis movement to locked slot."""
    action = get_next_action_from_egglog(
        basic_warehouse,
        cy=0.0,
        cx=0.0,
        holding=True,
        phase="deliver",
        cmd_type="DELIVER",
        target_type="queue",
        locked_id="Q1",
    )
    assert action["type"] == "update_y"
    assert action["val"] == 60.0
