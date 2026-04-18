"""
Unit tests for warehouse control system using egglog rewrite rules.
Tests all navigation and tray handling scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Optional
from cfg_engine import get_next_action_from_egglog


class TestWarehouseActions:
    """Test suite for get_next_action_from_egglog function"""

    @pytest.fixture
    def mock_warehouse(self):
        """Create mock warehouse with configurable slots"""
        class MockTray:
            def __init__(self, tray_id: int, is_full: bool):
                self.tray_id = tray_id
                self.is_full = is_full

        class MockSlot:
            def __init__(self, slot_id: str, slot_type: str, x: float, y: float, tray: Optional[MockTray] = None):
                self.slot_id = slot_id
                self.slot_type = slot_type
                self.x = x
                self.y = y
                self.tray = tray

        warehouse = Mock()
        warehouse._get_all_slots = Mock()
        return warehouse, MockSlot, MockTray

    def test_fetch_tray_move_y_first(self, mock_warehouse):
        """Test FETCH command: move Y axis when not aligned"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 5.0, 10.0, MockTray(100, True))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH", target_id=100
        )
        
        assert result[0] == "update_y_position"
        assert result[1][0] == 10.0

    def test_fetch_tray_move_x_after_y(self, mock_warehouse):
        """Test FETCH command: move X axis after Y is aligned"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 5.0, 10.0, MockTray(100, True))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=10.0, curr_x=0.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH", target_id=100
        )
        
        assert result[0] == "update_x_position"
        assert result[1][0] == 5.0

    def test_fetch_tray_pickup_when_aligned(self, mock_warehouse):
        """Test FETCH command: pickup when fully aligned with target slot"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 5.0, 10.0, MockTray(100, True))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=10.0, curr_x=5.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH", target_id=100
        )
        
        assert result[0] == "pick_up_from"
        assert len(result[1]) == 0

    def test_deliver_tray_move_y(self, mock_warehouse):
        """Test DELIVER command: move Y to empty slot position"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 3.0, 7.0, None)
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="storage"
        )
        
        assert result[0] == "update_y_position"
        assert result[1][0] == 7.0

    def test_deliver_tray_move_x(self, mock_warehouse):
        """Test DELIVER command: move X after Y aligned"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 3.0, 7.0, None)
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=7.0, curr_x=0.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="storage"
        )
        
        assert result[0] == "update_x_position"
        assert result[1][0] == 3.0

    def test_deliver_tray_place_when_aligned(self, mock_warehouse):
        """Test DELIVER command: place tray when aligned with empty slot"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 3.0, 7.0, None)
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=7.0, curr_x=3.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="storage"
        )
        
        assert result[0] == "place_into"

    def test_fetch_any_empty_tray_move_y(self, mock_warehouse):
        """Test FETCH_ANY_EMPTY: move Y to slot with empty tray (is_full=False)"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 2.0, 4.0, MockTray(200, False))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH_ANY_EMPTY"
        )
        
        assert result[0] == "update_y_position"
        assert result[1][0] == 4.0

    def test_fetch_any_empty_tray_pickup(self, mock_warehouse):
        """Test FETCH_ANY_EMPTY: pickup when aligned with empty tray slot"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 2.0, 4.0, MockTray(200, False))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=4.0, curr_x=2.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH_ANY_EMPTY"
        )
        
        assert result[0] == "pick_up_from"

    def test_idle_when_busy(self, mock_warehouse):
        """Test IDLE: wait when robot is busy"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = []
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=False,
            is_busy=True, cmd_type="FETCH", target_id=100
        )
        
        assert result[0] == "wait"

    def test_idle_command_explicit(self, mock_warehouse):
        """Test IDLE: wait when idle command is given"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = []
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=5.0, curr_x=5.0, is_holding_tray=True,
            is_busy=False, cmd_type="IDLE"
        )
        
        assert result[0] == "wait"

    def test_deliver_to_queue_type(self, mock_warehouse):
        """Test DELIVER: target queue-type slot"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("queue1", "queue", 1.0, 2.0, None)
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="queue"
        )
        
        assert result[0] == "update_y_position"
        assert result[1][0] == 2.0

    def test_deliver_to_bay_type(self, mock_warehouse):
        """Test DELIVER: target bay-type slot"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("bay1", "bay", 8.0, 9.0, None)
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="bay"
        )
        
        assert result[0] == "update_y_position"
        assert result[1][0] == 9.0

    def test_multiple_slots_selects_first_match(self, mock_warehouse):
        """Test system selects first matching slot when multiple exist"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 1.0, 1.0, MockTray(1, False)),
            MockSlot("slot2", "storage", 10.0, 10.0, MockTray(2, False))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH_ANY_EMPTY"
        )
        
        # Should target first slot found (slot1 at y=1.0)
        assert result[1][0] == 1.0

    def test_fetch_nonexistent_tray(self, mock_warehouse):
        """Test FETCH with non-existent tray ID falls back to wait"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 5.0, 5.0, MockTray(999, True))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=False,
            is_busy=False, cmd_type="FETCH", target_id=100
        )
        
        assert result[0] == "wait"

    def test_deliver_no_empty_slot(self, mock_warehouse):
        """Test DELIVER when no empty slot of target type exists"""
        warehouse, MockSlot, MockTray = mock_warehouse
        warehouse._get_all_slots.return_value = [
            MockSlot("slot1", "storage", 5.0, 5.0, MockTray(1, True))
        ]
        
        result = get_next_action_from_egglog(
            warehouse, curr_y=0.0, curr_x=0.0, is_holding_tray=True,
            is_busy=False, cmd_type="DELIVER", target_type="storage"
        )
        
        assert result[0] == "wait"