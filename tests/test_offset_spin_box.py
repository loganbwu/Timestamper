import pytest
from src.timestamper.OffsetSpinBox import DoubleOffsetSpinBox
# No need to import QApplication directly when using qtbot

@pytest.mark.parametrize("value, expected_text", [
    (8.5, "+08:30"),
    (-5.25, "-05:15"),
    (0.0, "+00:00"),
    (1.0, "+01:00"),
    (-12.0, "-12:00"),
    (14.0, "+14:00"),
])
def test_textFromValue(qtbot, value, expected_text):
    spin_box = DoubleOffsetSpinBox()
    qtbot.addWidget(spin_box)
    assert spin_box.textFromValue(value) == expected_text

@pytest.mark.parametrize("text, expected_value", [
    ("+08:30", 8.5),
    ("-05:15", -5.25),
    ("+00:00", 0.0),
    ("+01:00", 1.0),
    ("-12:00", -12.0),
    ("+14:00", 14.0),
])
def test_valueFromText(qtbot, text, expected_value):
    spin_box = DoubleOffsetSpinBox()
    qtbot.addWidget(spin_box)
    assert spin_box.valueFromText(text) == expected_value
