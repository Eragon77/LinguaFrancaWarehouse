import pytest
from warehouse_platform import Platform
from slot import Slot
from tray import Tray

@pytest.fixture
def platform():
    return Platform()

@pytest.fixture
def test_tray():
    return Tray(weight=3.0)

@pytest.fixture
def another_tray():
    return Tray(weight=4.0)

@pytest.fixture
def empty_slot():
    return Slot(slot_id="S1", x=0.5, y=1.0)

@pytest.fixture
def full_slot(empty_slot, test_tray):
    empty_slot.add_tray(test_tray)
    return empty_slot

def test_platform_init(platform):
    """Test platform initial state"""
    assert platform.curr_x == 0.0
    assert platform.curr_y == 0.0
    assert platform.held_tray is None
    assert platform.is_holding_tray() is False

def test_is_holding_tray_true(platform, test_tray):
    """Test is_holding_tray returns True when holding a tray"""
    platform.held_tray = test_tray
    assert platform.is_holding_tray() is True

def test_update_y_position(platform):
    """Test Y axis movement with speed limit"""
    platform.update_y_position(1.23)
    # With dt=0.05 and speed_y=0.2, max step is 0.01 per call
    assert platform.curr_y == pytest.approx(0.01)

def test_update_y_position_multiple_steps(platform):
    """Test Y axis reaches target after multiple updates"""
    target = 1.23
    for _ in range(150):
        platform.update_y_position(target)
    assert platform.curr_y == pytest.approx(target)

def test_update_x_position(platform):
    """Test X axis movement with speed limit"""
    platform.update_x_position(1.23)
    assert platform.curr_x == pytest.approx(0.0075)

def test_update_x_position_multiple_steps(platform):
    """Test X axis reaches target after multiple updates"""
    target = 1.23
    for _ in range(200):
        platform.update_x_position(target)
    assert platform.curr_x == pytest.approx(target)

def test_pick_up_success(platform, full_slot, test_tray):
    """Test successful tray pickup"""
    success = platform.pick_up_from(full_slot)
    
    assert success is True
    assert platform.is_holding_tray() is True
    assert platform.held_tray is test_tray
    assert full_slot.tray is None

def test_pick_up_fail_if_holding(platform, full_slot, another_tray):
    """Test pickup fails when already holding a tray"""
    platform.held_tray = another_tray
    
    success = platform.pick_up_from(full_slot)
    
    assert success is False
    assert platform.held_tray is another_tray
    assert full_slot.tray is not None 

def test_pick_up_fail_if_slot_empty(platform, empty_slot):
    """Test pickup fails when slot is empty"""
    success = platform.pick_up_from(empty_slot)
    
    assert success is False
    assert platform.is_holding_tray() is False

def test_place_into_success(platform, empty_slot, test_tray):
    """Test successful tray placement"""
    platform.held_tray = test_tray
    
    success = platform.place_into(empty_slot)
    
    assert success is True
    assert platform.is_holding_tray() is False
    assert empty_slot.tray is test_tray

def test_place_into_fail_if_empty(platform, empty_slot):
    """Test placement fails when not holding a tray"""
    success = platform.place_into(empty_slot)
    
    assert success is False
    assert platform.is_holding_tray() is False
    assert empty_slot.tray is None

def test_place_into_fail_if_slot_full(platform, full_slot, another_tray, test_tray):
    """Test placement fails when target slot is full"""
    platform.held_tray = another_tray
    
    success = platform.place_into(full_slot)
    
    assert success is False
    assert platform.held_tray is another_tray
    assert full_slot.tray is test_tray

def test_update_y_position_precision(platform):
    """Test Y movement stops exactly at target"""
    target = 0.005
    platform.update_y_position(target)
    # Should reach exactly because step (0.01) > distance (0.005)
    assert platform.curr_y == target

def test_update_x_position_precision(platform):
    """Test X movement stops exactly at target"""
    target = 0.003
    platform.update_x_position(target)
    # Should reach exactly because step (0.0075) > distance (0.003)
    assert platform.curr_x == target

def test_sequential_operations(platform, full_slot, empty_slot, test_tray, another_tray):
    """Test complete workflow: pickup, move, place"""
    # Pickup from full slot
    assert platform.pick_up_from(full_slot) is True
    assert platform.held_tray is test_tray
    assert full_slot.tray is None
    
    # Move platform
    platform.update_y_position(2.0)
    platform.update_x_position(1.0)
    
    # Place into empty slot
    assert platform.place_into(empty_slot) is True
    assert platform.held_tray is None
    assert empty_slot.tray is test_tray