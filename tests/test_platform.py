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
    return Slot(position_id="S1", x=0.5, y=1.0)

@pytest.fixture
def full_slot(empty_slot, test_tray):
    empty_slot.add_tray(test_tray)
    return empty_slot

def test_platform_init(platform):
    assert platform.curr_y == 0.0
    assert platform.held_tray is None
    assert platform.is_holding_tray() is False
    pass

def test_is_holding_tray_true(platform, test_tray):
    platform.held_tray = test_tray
    assert platform.is_holding_tray() is True

def test_update_y_position(platform):
    platform.update_y_position(1.23)
    assert platform.curr_y == 1.23

def test_pick_up_success(platform, full_slot, test_tray):
    success = platform.pick_up_from(full_slot)
    
    assert success is True
    assert platform.is_holding_tray() is True
    assert platform.held_tray is test_tray
    assert full_slot.tray is None

def test_pick_up_fail_if_holding(platform, full_slot, another_tray):
    platform.held_tray = another_tray
    
    success = platform.pick_up_from(full_slot)
    
    assert success is False
    assert platform.held_tray is another_tray
    assert full_slot.tray is not None 

def test_pick_up_fail_if_slot_empty(platform, empty_slot):
    success = platform.pick_up_from(empty_slot)
    
    assert success is False
    assert platform.is_holding_tray() is False

def test_place_into_success(platform, empty_slot, test_tray):
    platform.held_tray = test_tray
    
    success = platform.place_into(empty_slot)
    
    assert success is True
    assert platform.is_holding_tray() is False
    assert empty_slot.tray is test_tray

def test_place_into_fail_if_empty(platform, empty_slot):
    success = platform.place_into(empty_slot)
    
    assert success is False
    assert platform.is_holding_tray() is False
    assert empty_slot.tray is None

def test_place_into_fail_if_slot_full(platform, full_slot, another_tray, test_tray):
    platform.held_tray = another_tray
    
    success = platform.place_into(full_slot)
    
    assert success is False
    assert platform.held_tray is another_tray
    assert full_slot.tray is test_tray