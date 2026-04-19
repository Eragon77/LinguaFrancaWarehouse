import pytest
from tray import Tray

@pytest.fixture(autouse=True)
def reset_tray_counter():
    """Reset the Tray ID counter before each test"""
    Tray._next_id = 1
    yield

def test_tray_default_weight():
    """Test tray created with default weight uses MIN_W"""
    tray = Tray()
    assert tray.get_weight() == Tray.MIN_W

def test_tray_custom_weight():
    """Test tray created with custom weight"""
    custom_weight = 3.5
    tray = Tray(weight=custom_weight)
    assert tray.get_weight() == custom_weight

def test_tray_dimensions():
    """Test tray physical dimensions are correct"""
    tray = Tray()
    assert tray.get_length() == 1.62 
    assert tray.get_height() == 0.16725
    assert tray.get_width() == 0.7

def test_tray_id_increments():
    """Test each new tray gets a unique incremented ID"""
    tray1 = Tray()
    tray2 = Tray()
    tray3 = Tray()
    
    assert tray1.get_tray_id() == 1
    assert tray2.get_tray_id() == 2
    assert tray3.get_tray_id() == 3

def test_tray_is_full_true():
    """Test is_full property returns True when weight > MIN_W + 0.01"""
    heavy_tray = Tray(weight=Tray.MIN_W + 0.02)
    assert heavy_tray.is_full is True

def test_tray_is_full_false():
    """Test is_full property returns False when weight <= MIN_W + 0.01"""
    # Exactly at empty weight
    empty_tray = Tray(weight=Tray.MIN_W)
    assert empty_tray.is_full is False
    
    # Slightly above but within margin
    margin_tray = Tray(weight=Tray.MIN_W + 0.005)
    assert margin_tray.is_full is False

def test_tray_is_full_boundary():
    """Test is_full at the exact boundary (MIN_W + 0.01)"""
    boundary_tray = Tray(weight=Tray.MIN_W + 0.01)
    assert boundary_tray.is_full is False

def test_tray_accepts_out_of_bounds_weight():
    """Test tray accepts weights outside MIN_W/MAX_W range (no validation)"""
    out_of_bounds_weight = 10.0
    tray = Tray(weight=out_of_bounds_weight)
    assert tray.get_weight() == out_of_bounds_weight
    assert tray.is_full is True  # Since 10.0 > MIN_W + 0.01

def test_tray_weight_none():
    """Test passing None as weight uses default MIN_W"""
    tray = Tray(weight=None)
    assert tray.get_weight() == Tray.MIN_W

def test_tray_string_representation():
    """Test tray string representation includes ID and weight"""
    tray = Tray(weight=3.5)
    repr_str = repr(tray)
    assert str(tray.tray_id) in repr_str
    assert str(tray.weight) in repr_str

def test_tray_properties_direct_access():
    """Test direct property access vs getter methods"""
    tray = Tray()
    assert tray.length == tray.get_length()
    assert tray.height == tray.get_height()
    assert tray.width == tray.get_width()