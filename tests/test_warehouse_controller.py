"""
Fundamental tests for WarehouseController core functionality.
Tests mission initialization, state transitions, and basic operations.
"""

import pytest
from unittest.mock import Mock, patch
from enum import Enum
from warehouse_controller import WarehouseController, MissionState


class TestWarehouseControllerFundamentals:
    """Test core controller behavior without complex egglog integration."""

    @pytest.fixture
    def mock_warehouse(self):
        """Create minimal mock warehouse with essential attributes."""
        warehouse = Mock()
        
        # Platform mock
        platform = Mock()
        platform.curr_x = 0.0
        platform.curr_y = 0.0
        platform.is_holding_tray = Mock(return_value=False)
        platform.pick_up_from = Mock(return_value=True)
        platform.place_into = Mock(return_value=True)
        platform.update_y_position = Mock(return_value=True)
        platform.update_x_position = Mock(return_value=True)
        warehouse.platform = platform
        
        # Basic warehouse state
        warehouse.tray_in_bay = 0
        warehouse.has_tray = Mock(return_value=False)
        warehouse.get_tray_bay_slot = Mock(return_value=None)
        warehouse.get_occupied_queue_slot = Mock(return_value=None)
        warehouse.get_occupied_bay_slot = Mock(return_value=None)
        warehouse.get_slot_at = Mock(return_value=None)
        warehouse.get_slot_by_id = Mock(return_value=None)
        
        return warehouse

    @pytest.fixture
    def controller(self, mock_warehouse):
        """Create controller instance with mock warehouse."""
        return WarehouseController(mock_warehouse)

    # ============ INITIALIZATION ============
    
    def test_controller_initializes_idle(self, controller):
        """Controller starts in IDLE state with no mission data."""
        assert controller.state == MissionState.IDLE
        assert controller.is_busy is False
        assert controller.is_ready() is True
        assert controller.source_slot is None
        assert controller.dest_slot is None
        assert controller.target_tray_id is None

    def test_set_idle_resets_all_mission_state(self, controller):
        """set_idle clears all mission-related attributes."""
        # Set various mission state
        controller.state = MissionState.FETCH
        controller.source_slot = Mock()
        controller.dest_slot = Mock()
        controller.dest_type = "storage"
        controller.target_tray_id = 123
        controller.locked_target_id = "locked_456"
        
        controller.set_idle()
        
        assert controller.state == MissionState.IDLE
        assert controller.source_slot is None
        assert controller.dest_slot is None
        assert controller.dest_type is None
        assert controller.target_tray_id is None
        assert controller.locked_target_id is None

    # ============ MISSION INITIALIZATION ============
    
    def test_start_mission_initializes_fetch_phase(self, controller):
        """_start_mission sets FETCH state and stores mission parameters."""
        src_mock = Mock()
        dst_mock = Mock()
        
        controller._start_mission(src_mock, dst_mock, dst_type="queue", tray_id=42)
        
        assert controller.state == MissionState.FETCH
        assert controller.source_slot == src_mock
        assert controller.dest_slot == dst_mock
        assert controller.dest_type == "queue"
        assert controller.target_tray_id == 42

    def test_start_mission_accepts_none_parameters(self, controller):
        """_start_mission works with None values for optional parameters."""
        controller._start_mission(None, None, dst_type=None, tray_id=None)
        
        assert controller.state == MissionState.FETCH
        assert controller.source_slot is None
        assert controller.dest_slot is None
        assert controller.dest_type is None
        assert controller.target_tray_id is None

    # ============ ENQUEUE MISSION ============
    
    def test_enqueue_starts_when_tray_exists(self, controller, mock_warehouse):
        """enqueue initializes mission when tray exists in warehouse."""
        mock_warehouse.has_tray.return_value = True
        
        result = controller.enqueue(100)
        
        assert result is True
        assert controller.state == MissionState.FETCH
        assert controller.target_tray_id == 100
        assert controller.dest_type == "queue"
        mock_warehouse.has_tray.assert_called_with(100)

    def test_enqueue_fails_when_tray_not_found(self, controller, mock_warehouse):
        """enqueue returns False and does not start mission if tray missing."""
        mock_warehouse.has_tray.return_value = False
        
        result = controller.enqueue(999)
        
        assert result is False
        assert controller.state == MissionState.IDLE
        assert controller.target_tray_id is None

    # ============ EXTRACT MISSION ============
    
    def test_extract_with_tray_number_requires_empty_bay(self, controller, mock_warehouse):
        """extract with specific tray needs empty bay slot."""
        bay_slot = Mock()
        bay_slot.tray = None
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        mock_warehouse.has_tray.return_value = True
        
        result = controller.extract(100)
        
        assert result is True
        assert controller.state == MissionState.FETCH
        assert controller.target_tray_id == 100
        assert controller.dest_slot == bay_slot

    def test_extract_with_tray_fails_if_bay_occupied(self, controller, mock_warehouse):
        """extract cannot start if bay already has a tray."""
        bay_slot = Mock()
        bay_slot.tray = Mock()  # Occupied
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        
        result = controller.extract(100)
        
        assert result is False
        assert controller.state == MissionState.IDLE

    def test_extract_from_queue_requires_occupied_queue(self, controller, mock_warehouse):
        """extract without tray number fetches from occupied queue slot."""
        bay_slot = Mock()
        bay_slot.tray = None
        queue_slot = Mock()
        queue_slot.tray = Mock()  # Occupied
        
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        mock_warehouse.get_occupied_queue_slot.return_value = queue_slot
        
        result = controller.extract()  # No tray number
        
        assert result is True
        assert controller.state == MissionState.FETCH
        assert controller.source_slot == queue_slot
        assert controller.dest_slot == bay_slot

    def test_extract_from_queue_fails_if_queue_empty(self, controller, mock_warehouse):
        """extract without tray number fails when no queue slot occupied."""
        bay_slot = Mock()
        bay_slot.tray = None
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        mock_warehouse.get_occupied_queue_slot.return_value = None
        
        result = controller.extract()
        
        assert result is False
        assert controller.state == MissionState.IDLE

    # ============ SENDBACK MISSION ============
    
    def test_sendback_starts_when_bay_occupied(self, controller, mock_warehouse):
        """sendback moves tray from occupied bay to storage."""
        bay_slot = Mock()
        bay_slot.tray = Mock()  # Has tray
        mock_warehouse.get_occupied_bay_slot.return_value = bay_slot
        
        result = controller.sendback()
        
        assert result is True
        assert controller.state == MissionState.FETCH
        assert controller.source_slot == bay_slot
        assert controller.dest_type == "storage"

    def test_sendback_fails_if_bay_empty(self, controller, mock_warehouse):
        """sendback cannot start when bay is empty."""
        mock_warehouse.get_occupied_bay_slot.return_value = None
        
        result = controller.sendback()
        
        assert result is False
        assert controller.state == MissionState.IDLE

    # ============ FETCH ANY EMPTY ============
    
    def test_fetch_any_empty_starts_when_bay_empty(self, controller, mock_warehouse):
        """fetch_any_empty initializes mission to get empty tray to bay."""
        bay_slot = Mock()
        bay_slot.tray = None
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        
        result = controller.fetch_any_empty()
        
        assert result is True
        assert controller.state == MissionState.FETCH
        assert controller.dest_slot == bay_slot

    def test_fetch_any_empty_fails_if_bay_occupied(self, controller, mock_warehouse):
        """fetch_any_empty cannot start when bay already has a tray."""
        bay_slot = Mock()
        bay_slot.tray = Mock()  # Occupied
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        
        result = controller.fetch_any_empty()
        
        assert result is False
        assert controller.state == MissionState.IDLE

    # ============ BUSY STATE ============
    
    def test_is_busy_returns_true_during_mission(self, controller):
        """is_busy reflects active mission state."""
        assert controller.is_busy is False
        
        controller.state = MissionState.FETCH
        assert controller.is_busy is True
        
        controller.state = MissionState.DELIVER
        assert controller.is_busy is True

    def test_is_ready_returns_true_only_when_idle(self, controller):
        """is_ready indicates controller can accept new missions."""
        assert controller.is_ready() is True
        
        controller.state = MissionState.FETCH
        assert controller.is_ready() is False

    # ============ BAY INFO ============
    
    def test_request_info_bay_returns_json_empty(self, controller, mock_warehouse):
        """requestInfoBay returns JSON with Empty status when no tray."""
        mock_warehouse.tray_in_bay = 0
        
        import json
        result = controller.requestInfoBay()
        data = json.loads(result)
        
        assert data["status"] == "Empty"
        assert data["tray_id"] == 0

    def test_request_info_bay_returns_json_occupied(self, controller, mock_warehouse):
        """requestInfoBay returns JSON with Occupied status when tray present."""
        mock_warehouse.tray_in_bay = 42
        
        import json
        result = controller.requestInfoBay()
        data = json.loads(result)
        
        assert data["status"] == "Occupied"
        assert data["tray_id"] == 42

    # ============ CLEAR BAY ============
    
    def test_clear_bay_removes_tray_if_present(self, controller, mock_warehouse):
        """clearBay removes tray from bay slot."""
        bay_slot = Mock()
        bay_slot.tray = Mock()
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        
        result = controller.clearBay()
        
        assert result is True
        bay_slot.remove_tray.assert_called_once()

    def test_clear_bay_does_nothing_if_bay_empty(self, controller, mock_warehouse):
        """clearBay returns True even when bay is empty."""
        bay_slot = Mock()
        bay_slot.tray = None
        mock_warehouse.get_tray_bay_slot.return_value = bay_slot
        
        result = controller.clearBay()
        
        assert result is True
        bay_slot.remove_tray.assert_not_called()

    # ============ TICK BEHAVIOR ============
    
    def test_tick_returns_false_when_idle(self, controller):
        """tick does nothing and returns False when controller is idle."""
        result = controller.tick()
        
        assert result is False

    @patch('warehouse_controller.get_next_action_from_egglog')
    def test_tick_processes_lock_action(self, mock_get_action, controller, mock_warehouse):
        """tick handles lock action by storing locked_target_id."""
        mock_get_action.return_value = {"type": "lock", "slot_id": "SLOT_001"}
        controller.state = MissionState.FETCH
        controller.target_tray_id = 100
        
        result = controller.tick()
        
        assert result is True
        assert controller.locked_target_id == "SLOT_001"

    @patch('warehouse_controller.get_next_action_from_egglog')
    def test_tick_transitions_to_deliver_after_pick(self, mock_get_action, controller, mock_warehouse):
        """tick transitions from FETCH to DELIVER after successful pick."""
        mock_get_action.return_value = {"type": "pick"}
        controller.state = MissionState.FETCH
        controller.source_slot = None
        
        # Mock platform and current position
        mock_warehouse.platform.curr_x = 5.0
        mock_warehouse.platform.curr_y = 5.0
        current_slot = Mock()
        mock_warehouse.get_slot_at.return_value = current_slot
        
        result = controller.tick()
        
        assert result is True
        assert controller.state == MissionState.DELIVER
        assert controller.source_slot == current_slot

    @patch('warehouse_controller.get_next_action_from_egglog')
    def test_tick_completes_mission_after_place(self, mock_get_action, controller, mock_warehouse):
        """tick sets controller to IDLE after successful place in DELIVER phase."""
        mock_get_action.return_value = {"type": "place"}
        controller.state = MissionState.DELIVER
        
        # Setup required state for place action
        dest_slot = Mock()
        dest_slot.slot_id = "TEST_SLOT"
        controller.dest_slot = dest_slot
        mock_warehouse.get_slot_by_id.return_value = dest_slot
        
        result = controller.tick()
        
        assert result is True
        assert controller.state == MissionState.IDLE
        assert controller.source_slot is None
        assert controller.dest_slot is None
        assert controller.locked_target_id is None

    @patch('warehouse_controller.get_next_action_from_egglog')
    def test_tick_resets_on_action_failure(self, mock_get_action, controller, mock_warehouse):
        """tick resets controller to IDLE if action execution fails."""
        mock_get_action.return_value = {"type": "update_y", "val": 10.0}
        mock_warehouse.platform.update_y_position.return_value = False  # Action fails
        controller.state = MissionState.FETCH
        controller.target_tray_id = 100
        
        result = controller.tick()
        
        assert result is False
        assert controller.state == MissionState.IDLE

    @patch('warehouse_controller.get_next_action_from_egglog')
    def test_tick_ignores_wait_action(self, mock_get_action, controller):
        """tick returns False without changing state on wait action."""
        mock_get_action.return_value = {"type": "wait"}
        controller.state = MissionState.FETCH
        
        result = controller.tick()
        
        assert result is False
        assert controller.state == MissionState.FETCH  # State unchanged