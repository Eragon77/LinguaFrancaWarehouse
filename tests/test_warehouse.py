import pytest
from warehouse import Warehouse
from warehouse_platform import Platform
from slot import Slot

# --- Fixtures ---

@pytest.fixture
def warehouse():
    """Returns a new Warehouse instance for each test."""
    return Warehouse()

# --- Tests ---

def test_warehouse_init(warehouse):
    # Check platform creation
    assert isinstance(warehouse.platform, Platform)
    
    # Check initial state
    assert warehouse.is_busy is False
    assert warehouse.is_ready() is True

    # Check slot counts
    num_rows = Warehouse.NUM_ROWS
    assert len(warehouse.storage_slots) == num_rows + (num_rows - 4) # 16
    assert len(warehouse.queued_slots) == 3
    assert warehouse.in_view_slot is not None
    
    total_slots = len(warehouse.storage_slots) + len(warehouse.queued_slots) + 1
    assert total_slots == 20

def test_warehouse_state_methods(warehouse):
    assert warehouse.is_ready() is True
    
    warehouse.set_busy()
    assert warehouse.is_busy is True
    assert warehouse.is_ready() is False
    
    warehouse.set_idle()
    assert warehouse.is_busy is False
    assert warehouse.is_ready() is True

def test_get_all_slots(warehouse):
    all_slots = warehouse.get_all_slots()
    assert len(all_slots) == Warehouse.NUM_ROWS * 2

def test_get_slot_by_id_success(warehouse):
    # Test storage slot
    slot_l5 = warehouse.get_slot_by_id("storage_L_5")
    assert slot_l5 is not None
    assert slot_l5.position_id == "storage_L_5"
    
    # Test queue slot
    slot_q1 = warehouse.get_slot_by_id("queue_1")
    assert slot_q1 is not None
    assert slot_q1.x == Warehouse.X_RIGHT
    
    # Test in_view slot
    slot_v = warehouse.get_slot_by_id("in_view")
    assert slot_v is warehouse.in_view_slot

def test_get_slot_by_id_fail(warehouse):
    # Test non-existent ID
    invalid_slot = warehouse.get_slot_by_id("NON_EXISTENT_ID")
    assert invalid_slot is None