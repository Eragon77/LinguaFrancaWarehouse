from cfg_engine import get_next_action_from_egglog

# ---------------------------------------------------------
# 1. OVERRIDE & IDLE STATES
# ---------------------------------------------------------

def test_busy_state_forces_wait():
    """If the hardware is busy, the engine must return 'wait' regardless of the mission."""
    action, args = get_next_action_from_egglog(
        curr_y=0, curr_x=0, target_y=10, target_x=10,
        is_holding_tray=False, 
        is_busy=True, # <--- System is busy
        is_target_empty=False, 
        cmd_type="FETCH"
    )
    assert action == "wait"
    assert args == ()

def test_idle_command_forces_wait():
    """If the command type is IDLE, the engine must return 'wait'."""
    action, args = get_next_action_from_egglog(
        curr_y=0, curr_x=0, target_y=10, target_x=10,
        is_holding_tray=False, 
        is_busy=False, 
        is_target_empty=False, 
        cmd_type="IDLE" # <--- IDLE command
    )
    assert action == "wait"
    assert args == ()

# ---------------------------------------------------------
# 2. FETCH SEQUENCE
# ---------------------------------------------------------

def test_fetch_move_y_first():
    """FETCH: If Y is not aligned, the robot must move Y first."""
    action, args = get_next_action_from_egglog(
        curr_y=2.0, curr_x=5.0, 
        target_y=10.0, target_x=15.0, # Target Y is different
        is_holding_tray=False, is_busy=False, is_target_empty=False, 
        cmd_type="FETCH"
    )
    assert action == "update_y_position"
    assert args == (10.0,)

def test_fetch_move_x_when_y_aligned():
    """FETCH: If Y is aligned but X is not, the robot must move X."""
    action, args = get_next_action_from_egglog(
        curr_y=10.0, curr_x=5.0,  # Y is at target
        target_y=10.0, target_x=15.0, # Target X is different
        is_holding_tray=False, is_busy=False, is_target_empty=False, 
        cmd_type="FETCH"
    )
    assert action == "update_x_position"
    assert args == (15.0,)

def test_fetch_pick_up_when_fully_aligned():
    """FETCH: If X and Y are aligned, and the slot is NOT empty, pick up the tray."""
    action, args = get_next_action_from_egglog(
        curr_y=10.0, curr_x=15.0, 
        target_y=10.0, target_x=15.0, # Fully aligned
        is_holding_tray=False, is_busy=False, 
        is_target_empty=False, # <--- Tray is there
        cmd_type="FETCH"
    )
    assert action == "pick_up_from"
    assert args == ()

# ---------------------------------------------------------
# 3. DELIVER SEQUENCE
# ---------------------------------------------------------

def test_deliver_move_y_first():
    """DELIVER: If holding a tray and Y is not aligned, move Y first."""
    action, args = get_next_action_from_egglog(
        curr_y=10.0, curr_x=15.0, 
        target_y=20.0, target_x=25.0, # Target Y is different
        is_holding_tray=True, # <--- Holding tray
        is_busy=False, is_target_empty=True, 
        cmd_type="DELIVER"
    )
    assert action == "update_y_position"
    assert args == (20.0,)

def test_deliver_move_x_when_y_aligned():
    """DELIVER: If holding a tray and Y is aligned, move X."""
    action, args = get_next_action_from_egglog(
        curr_y=20.0, curr_x=15.0, # Y is at target
        target_y=20.0, target_x=25.0, # Target X is different
        is_holding_tray=True, # <--- Holding tray
        is_busy=False, is_target_empty=True, 
        cmd_type="DELIVER"
    )
    assert action == "update_x_position"
    assert args == (25.0,)

def test_deliver_place_into_when_fully_aligned():
    """DELIVER: If fully aligned and slot is empty, place the tray."""
    action, args = get_next_action_from_egglog(
        curr_y=20.0, curr_x=25.0, 
        target_y=20.0, target_x=25.0, # Fully aligned
        is_holding_tray=True, is_busy=False, 
        is_target_empty=True, # <--- Destination is empty
        cmd_type="DELIVER"
    )
    assert action == "place_into"
    assert args == ()