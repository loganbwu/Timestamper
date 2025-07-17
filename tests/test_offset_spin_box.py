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
    # New test cases for more robust parsing
    ("8:30", 8.5),      # No sign, with colon
    ("-5:15", -5.25),    # Single digit hour, with colon
    ("+8", 8.0),        # Single digit hour, no colon
    ("-5", -5.0),       # Single digit hour, no colon
    ("0", 0.0),         # Zero
    ("", 0.0),          # Empty string
    ("invalid", 0.0),   # Invalid string
    ("+08", 8.0),       # With leading zero, no colon
    ("-05", -5.0),      # With leading zero, no colon
    ("8.5", 8.5),       # Decimal input
    ("-5.25", -5.25),   # Decimal input
    ("GMT+05:00", 5.0), # GMT prefix
    ("gmt-03:30", -3.5),# Lowercase GMT prefix
    ("GMT-8", -8.0),    # GMT prefix with no minutes
])
def test_valueFromText(qtbot, text, expected_value):
    spin_box = DoubleOffsetSpinBox()
    qtbot.addWidget(spin_box)
    
    # Test direct conversion
    assert spin_box.valueFromText(text) == expected_value

    # Simulate user typing and losing focus
    spin_box.setFocus()
    spin_box.lineEdit().setText(text) # Set text directly in the line edit
    spin_box.interpretText() # Force the spin box to interpret the text and update its value
    qtbot.wait(10) # Give Qt a moment to process events
    assert spin_box.value() == expected_value


def test_manual_editing_and_focus_loss(qtbot):
    """
    Simulates a user manually editing the text and then losing focus.
    This tests the fix for the bug where manual edits were reverted.
    """
    from PySide6.QtWidgets import QWidget

    # 1. Setup the widgets
    parent = QWidget()
    qtbot.addWidget(parent)
    spin_box = DoubleOffsetSpinBox(parent)
    other_widget = QWidget(parent)  # A widget to steal focus
    parent.show()

    spin_box.setValue(8.0)  # Initial value "+08:00"
    assert spin_box.value() == 8.0
    assert spin_box.text() == "+08:00"

    # 2. Simulate user typing a new value
    # We clear the text first, then type the new one.
    spin_box.setFocus()
    spin_box.lineEdit().clear()
    qtbot.keyClicks(spin_box.lineEdit(), "-05:30")

    # 3. Simulate losing focus
    other_widget.setFocus()

    # 4. Assert the value and text are updated correctly
    assert spin_box.value() == -5.5
    assert spin_box.text() == "-05:30"
