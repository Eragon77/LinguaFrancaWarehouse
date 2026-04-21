import pytest
from slot import Slot
from tray import Tray


@pytest.fixture
def empty_slot():
    return Slot(slot_id="test_slot", x=0.5, y=1.0)


@pytest.fixture
def test_tray():
    return Tray(weight=3.0)


def test_add_tray_success(empty_slot, test_tray):
    """Test successful tray addition to empty slot"""
    result = empty_slot.add_tray(test_tray)
    assert result is True
    assert empty_slot.tray is test_tray


def test_add_tray_fail_when_full(empty_slot, test_tray):
    """Test adding tray to already occupied slot raises ValueError"""
    empty_slot.add_tray(test_tray)  # First addition succeeds

    # Second addition should raise ValueError
    another_tray = Tray(weight=4.0)
    with pytest.raises(
        ValueError, match=f"Slot {empty_slot.slot_id} is already occupied"
    ):
        empty_slot.add_tray(another_tray)


def test_remove_tray_success(empty_slot, test_tray):
    """Test successful tray removal from occupied slot"""
    empty_slot.add_tray(test_tray)

    removed = empty_slot.remove_tray()

    assert removed is test_tray
    assert empty_slot.tray is None


def test_remove_tray_fail_when_empty(empty_slot):
    """Test removing tray from empty slot raises ValueError"""
    with pytest.raises(ValueError, match=f"Slot {empty_slot.slot_id} is already empty"):
        empty_slot.remove_tray()


def test_slot_repr_empty(empty_slot):
    """Test string representation of empty slot"""
    assert repr(empty_slot) == f"<Slot ID: '{empty_slot.slot_id}' (Empty)>"


def test_slot_repr_full(empty_slot, test_tray):
    """Test string representation of full slot"""
    empty_slot.add_tray(test_tray)
    assert repr(empty_slot) == f"<Slot ID: '{empty_slot.slot_id}' (Full)>"


def test_slot_attributes(empty_slot):
    """Test slot initialization attributes"""
    assert empty_slot.slot_id == "test_slot"
    assert empty_slot.x == 0.5
    assert empty_slot.y == 1.0
    assert empty_slot.slot_type == "storage"  # Default value
    assert empty_slot.length == 1.62
    assert empty_slot.height == 0.16725
    assert empty_slot.width == 0.7
    assert empty_slot.tray is None


def test_slot_with_custom_type():
    """Test slot creation with custom slot type"""
    slot = Slot(slot_id="queue1", x=0.0, y=0.0, slot_type="queue")
    assert slot.slot_type == "queue"
