import pytest
from timestamper.OffsetSpinBox import DoubleOffsetSpinBox
# No need to import QApplication directly when using qtbot

def test_textFromValue(qtbot): # Use qtbot fixture
    spin_box = DoubleOffsetSpinBox()
    qtbot.addWidget(spin_box) # Add widget to qtbot
    assert spin_box.textFromValue(8.5) == "+08:30"
    assert spin_box.textFromValue(-5.25) == "-05:15"
    assert spin_box.textFromValue(0.0) == "+00:00"
    assert spin_box.textFromValue(1.0) == "+01:00"
    assert spin_box.textFromValue(-12.0) == "-12:00"
    assert spin_box.textFromValue(14.0) == "+14:00"

def test_valueFromText(qtbot): # Use qtbot fixture
    spin_box = DoubleOffsetSpinBox()
    qtbot.addWidget(spin_box) # Add widget to qtbot
    assert spin_box.valueFromText("+08:30") == 8.5
    assert spin_box.valueFromText("-05:15") == -5.25
    assert spin_box.valueFromText("+00:00") == 0.0
    assert spin_box.valueFromText("+01:00") == 1.0
    assert spin_box.valueFromText("-12:00") == -12.0
    assert spin_box.valueFromText("+14:00") == 14.0
