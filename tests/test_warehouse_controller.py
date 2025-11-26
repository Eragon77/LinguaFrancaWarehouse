import pytest
import logging
from unittest.mock import Mock, patch
from io import StringIO
import sys

from warehouse_controller import WarehouseController
from warehouse import Warehouse
from warehouse_platform import Platform
from slot import Slot
from tray import Tray

logging.basicConfig(level=logging.ERROR, stream=sys.stdout)


@pytest.fixture
def mock_tray():
    tray = Mock(spec=Tray)
    tray.tray_id = "5"
    return tray

@pytest.fixture
def slot_storage(mock_tray):
    slot = Mock(spec=Slot)
    slot.position_id = "storage_L_10"
    slot.x = 0.5
    slot.y = 1.67
    slot.tray = mock_tray
    slot.remove_tray.return_value = mock_tray
    return slot

@pytest.fixture
def slot_queue(mock_tray):
    slot = Mock(spec=Slot)
    slot.position_id = "queue_0"
    slot.x = 0.835
    slot.y = 0.0
    slot.tray = mock_tray
    return slot

@pytest.fixture
def mock_platform():
    platform = Mock(spec=Platform)
    platform.curr_x = 0.0
    platform.curr_y = 0.0
    platform.speed_y = 0.5
    platform.extract_speed = 1.5
    
    platform.update_y_position.return_value = True
    platform.update_x_position.return_value = True
    platform.pick_up_from.return_value = True
    platform.place_into.return_value = True
    return platform

@pytest.fixture
def mock_warehouse(mock_platform, slot_storage, slot_queue):
    warehouse = Mock(spec=Warehouse)
    warehouse.platform = mock_platform
    
    warehouse.find_slot_by_tray_id.return_value = slot_storage
    warehouse.get_empty_queue_slot.return_value = slot_queue
    warehouse.get_occupied_bay_slot.return_value = None
    
    warehouse.set_busy = Mock()
    warehouse.set_idle = Mock()
    return warehouse


@pytest.fixture
def controller(mock_warehouse):
    return WarehouseController(mock_warehouse)


def test_get_time_y_zero_speed(controller, mock_platform):
    mock_platform.speed_y = 0.0
    assert controller._get_time_y(1.0) == 0.0

def test_get_time_x_calculation(controller, mock_platform):
    assert controller._get_time_x(0.835) == pytest.approx(0.5566, rel=1e-3)

def test_build_enqueue_sequence_success(controller, mock_warehouse, slot_storage, slot_queue):
    mock_warehouse.find_slot_by_tray_id.return_value = slot_storage
    
    success = controller.build_enqueue_sequence("5")
    
    assert success is True
    assert len(controller.current_move_sequence) == 8
    
    time, method, args, msg = controller.current_move_sequence[-1]
    assert method == "update_y_position"
    assert args[0] == slot_storage.y

def test_build_enqueue_sequence_fail_queue_full(controller, mock_warehouse):
    mock_warehouse.get_empty_queue_slot.return_value = None
    
    success = controller.build_enqueue_sequence("5")
    
    assert success is False
    assert len(controller.current_move_sequence) == 0

def test_execute_step_success(controller, mock_platform):
    controller.wh.platform.update_y_position.return_value = True
    success = controller.execute_step("update_y_position", (1.5,))
    
    assert success is True
    mock_platform.update_y_position.assert_called_once_with(1.5)

def test_execute_step_fail_attribute_error(controller):
    success = controller.execute_step("non_existent_method", (1,))
    
    assert success is False

def test_execute_step_fail_value_error(controller, mock_platform):
    mock_platform.place_into.side_effect = ValueError("Slot occupied violation")
    
    success = controller.execute_step("place_into", (Mock(spec=Slot),))
    
    assert success is False
    
def test_execute_step_fail_zero_division_error(controller, mock_platform):
    mock_platform.update_y_position.side_effect = ZeroDivisionError("Time calc failed")
    
    success = controller.execute_step("update_y_position", (1.0,))
    
    assert success is False

def test_build_extract_sequence_success(controller, mock_warehouse, slot_queue):
    slot_queue.remove_tray = Mock()
    
    mock_warehouse.get_occupied_queue_slot.return_value = slot_queue
    mock_warehouse.get_tray_bay_slot.return_value = Mock(position_id="in_view", x=0.835, y=0.5, tray=None)
    
    success = controller.build_extract_sequence()
    
    assert success is True
    assert len(controller.current_move_sequence) == 8
    
    # The actual PICKUP action is the 4th step to be executed (index 5 in the reverse list)
    # The list is indexed 0..7. The pickup message is at index 5.
    assert controller.current_move_sequence[5][3].startswith("PICKUP: Tray picked up from queue_0")