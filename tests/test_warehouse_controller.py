import pytest
from unittest.mock import Mock, patch
from warehouse_controller import WarehouseController
from slot import Slot
from tray import Tray

# ---------------------------------------------------------
# FIXTURES (Mocks)
# ---------------------------------------------------------

@pytest.fixture
def mock_platform():
    """
    Provides a mocked Platform object with default coordinate values
    and pre-configured return values for hardware-simulation methods.
    """
    platform = Mock()
    platform.curr_x = 0.0
    platform.curr_y = 0.0
    platform.is_holding_tray.return_value = False
    
    platform.update_y_position.return_value = True
    platform.update_x_position.return_value = True
    platform.pick_up_from.return_value = True
    platform.place_into.return_value = True
    return platform

@pytest.fixture
def mock_warehouse(mock_platform):
    """
    Provides a mocked Warehouse object containing the mocked platform.
    """
    warehouse = Mock()
    warehouse.platform = mock_platform
    return warehouse

@pytest.fixture
def controller(mock_warehouse):
    """
    Provides a WarehouseController instance initialized with mocked dependencies.
    """
    return WarehouseController(mock_warehouse)

@pytest.fixture
def dummy_slot_with_tray():
    """
    Provides a mocked Slot object occupied by a Tray with ID '105'.
    """
    slot = Mock(spec=Slot)
    slot.slot_id = "storage_0"
    slot.slot_type = "storage"
    slot.tray = Mock(spec=Tray)
    slot.tray.tray_id = "105"
    return slot

@pytest.fixture
def dummy_empty_slot():
    """
    Provides an empty mocked Slot object of type 'queue'.
    """
    slot = Mock(spec=Slot)
    slot.slot_id = "queue_0"
    slot.slot_type = "queue"
    slot.tray = None
    return slot

# ---------------------------------------------------------
# TESTS: STATE AND BUILDERS
# ---------------------------------------------------------

def test_initial_state(controller):
    """
    Verifies that the controller starts in IDLE state with no active missions.
    """
    assert controller.current_mission == "IDLE"
    assert controller.is_busy is False
    assert controller.is_ready() is True

def test_build_enqueue_sequence_success(controller, mock_warehouse, dummy_slot_with_tray, dummy_empty_slot):
    """
    Tests if build_enqueue_sequence correctly identifies source/destination slots
    and transitions the controller mission to FETCH.
    """
    mock_warehouse.find_slot_by_tray_id.return_value = dummy_slot_with_tray
    mock_warehouse.get_empty_queue_slot.return_value = dummy_empty_slot
    
    success = controller.build_enqueue_sequence("105")
    
    assert success is True
    assert controller.current_mission == "FETCH"
    assert controller.source_slot == dummy_slot_with_tray
    assert controller.dest_slot == dummy_empty_slot
    assert controller.is_busy is True

def test_build_fetch_any_empty_sequence(controller, mock_warehouse, dummy_empty_slot):
    """
    Verifies that the autonomous empty tray search mission initializes correctly
    with a placeholder source slot (None) and a valid destination.
    """
    mock_warehouse.get_empty_storage_slot.return_value = dummy_empty_slot
    
    success = controller.build_fetch_any_empty_sequence()
    
    assert success is True
    assert controller.current_mission == "FETCH"
    assert controller.source_slot is None 
    assert controller.dest_slot == dummy_empty_slot

# ---------------------------------------------------------
# TESTS: TICK AND EGGLOG
# ---------------------------------------------------------

def test_tick_returns_false_when_idle(controller):
    """
    Ensures that the tick method immediately returns False if no mission is active.
    """
    assert controller.tick() is False

@patch("warehouse_controller.get_next_action_from_egglog")
def test_tick_executes_movement(mock_egglog, controller, mock_warehouse, dummy_slot_with_tray):
    """
    Verifies that when Egglog suggests a movement action, the controller 
    triggers the corresponding method on the physical platform.
    """
    controller.current_mission = "FETCH"
    controller.source_slot = dummy_slot_with_tray
    
    mock_egglog.return_value = ("update_y_position", (3.5,))
    
    result = controller.tick()
    
    assert result is True
    mock_warehouse.platform.update_y_position.assert_called_once_with(3.5)
    assert controller.current_mission == "FETCH" 

@patch("warehouse_controller.get_next_action_from_egglog")
def test_tick_switches_to_deliver_on_pickup(mock_egglog, controller, mock_warehouse, dummy_slot_with_tray):
    """
    Tests the transition from FETCH to DELIVER state once a pick_up_from 
    action is successfully commanded by the logic engine.
    """
    controller.current_mission = "FETCH"
    controller.source_slot = dummy_slot_with_tray
    
    mock_egglog.return_value = ("pick_up_from", ())
    
    controller.tick()
    
    mock_warehouse.platform.pick_up_from.assert_called_once_with(dummy_slot_with_tray)
    assert controller.current_mission == "DELIVER"

@patch("warehouse_controller.get_next_action_from_egglog")
def test_tick_autonomous_fetch_updates_source_slot(mock_egglog, controller, mock_warehouse):
    """
    Verifies that during an autonomous search (FETCH_ANY_EMPTY), the controller
    identifies and assigns the source_slot based on current platform position at pickup.
    """
    controller.current_mission = "FETCH"
    controller.source_slot = None
    
    found_slot = Mock(spec=Slot)
    mock_warehouse.get_slot_at.return_value = found_slot
    
    mock_egglog.return_value = ("pick_up_from", ())
    
    controller.tick()
    
    assert controller.source_slot == found_slot
    assert controller.current_mission == "DELIVER"
    mock_warehouse.platform.pick_up_from.assert_called_once_with(found_slot)

@patch("warehouse_controller.get_next_action_from_egglog")
def test_tick_finishes_mission_on_place(mock_egglog, controller, mock_warehouse, dummy_empty_slot):
    """
    Tests the completion of a mission, ensuring the controller resets to 
    IDLE and clears slot references after a place_into action.
    """
    controller.current_mission = "DELIVER"
    controller.dest_slot = dummy_empty_slot
    
    mock_egglog.return_value = ("place_into", ())
    
    controller.tick()
    
    mock_warehouse.platform.place_into.assert_called_once_with(dummy_empty_slot)
    assert controller.current_mission == "IDLE"
    assert controller.source_slot is None
    assert controller.dest_slot is None

# ---------------------------------------------------------
# TESTS: EXCEPTION HANDLING
# ---------------------------------------------------------

def test_execute_step_handles_exceptions(controller, mock_warehouse, dummy_slot_with_tray):
    """
    Ensures that hardware-level exceptions are caught by execute_step,
    preventing application crashes and returning a failure status.
    """
    mock_warehouse.platform.pick_up_from.side_effect = Exception("Hardware Fault")
    
    controller.source_slot = dummy_slot_with_tray
    
    success = controller.execute_step("pick_up_from", ())
    
    assert success is False