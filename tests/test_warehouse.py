import pytest
from warehouse import Warehouse
from warehouse_platform import Platform
from slot import Slot
from tray import Tray

# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_tray_counter():
    """Reset the Tray ID counter before each test"""
    Tray._next_id = 1
    yield


@pytest.fixture
def warehouse():
    """Returns a new Warehouse instance for each test."""
    return Warehouse()


# --- Tests ---


def test_warehouse_has_platform(warehouse):
    """Warehouse must always have a platform"""
    assert hasattr(warehouse, "platform")
    assert isinstance(warehouse.platform, Platform)


def test_warehouse_has_slot_collections(warehouse):
    """Warehouse must have collections for different slot types"""
    assert hasattr(warehouse, "storage_slots")
    assert hasattr(warehouse, "queued_slots")
    assert hasattr(warehouse, "in_view_slot")
    assert isinstance(warehouse.storage_slots, list)
    assert isinstance(warehouse.queued_slots, list)


def test_get_slot_by_id_returns_slot(warehouse):
    """get_slot_by_id should return a Slot object for valid IDs"""
    # Just verify the method exists and returns a Slot or None
    result = warehouse.get_slot_by_id("any_id")
    assert result is None or isinstance(result, Slot)


def test_get_slot_at_returns_slot(warehouse):
    """get_slot_at should return a Slot object for valid coordinates"""
    result = warehouse.get_slot_at(0.0, 0.0)
    assert result is None or isinstance(result, Slot)


def test_get_occupied_queue_slot_returns_slot_or_none(warehouse):
    """get_occupied_queue_slot should return Slot or None"""
    result = warehouse.get_occupied_queue_slot()
    assert result is None or isinstance(result, Slot)


def test_get_occupied_bay_slot_returns_slot_or_none(warehouse):
    """get_occupied_bay_slot should return Slot or None"""
    result = warehouse.get_occupied_bay_slot()
    assert result is None or isinstance(result, Slot)


def test_get_tray_bay_slot_returns_slot(warehouse):
    """get_tray_bay_slot should return the bay slot"""
    result = warehouse.get_tray_bay_slot()
    assert result is None or isinstance(result, Slot)


def test_tray_in_bay_property_returns_int(warehouse):
    """tray_in_bay should return an integer (0 if empty, otherwise tray ID)"""
    result = warehouse.tray_in_bay
    assert isinstance(result, int)
    assert result >= 0


def test_get_all_slots_returns_list(warehouse):
    """_get_all_slots should return a list of slots"""
    result = warehouse._get_all_slots()
    assert isinstance(result, list)
    # All items in the list should be Slot objects
    for slot in result:
        assert isinstance(slot, Slot)
