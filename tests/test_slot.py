import pytest
from slot import Slot
from tray import Tray

@pytest.fixture
def empty_slot():
    return Slot(position_id="test_slot", x=0.5, y=1.0)

@pytest.fixture
def test_tray():
    return Tray(weight=3.0)

def test_add_tray_success(empty_slot, test_tray):
    result=empty_slot.add_tray(test_tray)
    assert result is True
