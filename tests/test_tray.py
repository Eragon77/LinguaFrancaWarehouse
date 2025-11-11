import pytest
from tray import Tray

def test_tray_default_weight():
    tray=Tray()
    assert tray.get_weight() == Tray.MIN_W

def test_tray_custom_weight():
    custom_weight = 3.5
    tray = Tray(weight=custom_weight)
    assert tray.get_weight() == custom_weight

def test_tray_dimensions():
    tray = Tray()
    assert tray.get_length() == 2.134
    assert tray.get_height() == 0.16725
    assert tray.width == 0.83

def test_tray_is_stupid():
    out_of_bounds_weight = 10.0  # Weight outside the defined min/max range
    tray=Tray(weight=out_of_bounds_weight)

    assert tray.get_weight() == out_of_bounds_weight

def tesst_tray_weight_none():
    tray = Tray(weight=None)
    assert tray.get_weight() == Tray.MIN_W