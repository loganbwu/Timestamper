import pytest
from src.timestamper.main import MainWindow
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QKeySequence

def test_datetime_adjustment_hotkeys(qtbot):
    """Test that hotkeys correctly adjust the datetime field."""
    mw = MainWindow()
    qtbot.addWidget(mw)

    initial_dt = QDateTime(2023, 1, 15, 10, 30, 0)
    mw.datetime.setDateTime(initial_dt)

    # Find the buttons by their text, ensuring they are QPushButtons
    def find_button(text_prefix):
        from PySide6.QtWidgets import QPushButton # Import QPushButton locally for type checking
        for button in mw.dt_buttons:
            if isinstance(button, QPushButton) and button.text().startswith(text_prefix):
                return button
        return None

    # Test '+00:01' (O) button click
    button_plus_1m = find_button("+00:01")
    assert button_plus_1m is not None
    qtbot.mouseClick(button_plus_1m, Qt.LeftButton)
    expected_dt_o = QDateTime(2023, 1, 15, 10, 31, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_o.toString("yyyy:MM:dd HH:mm:ss")

    # Reset and test '-00:01' (L) button click
    mw.datetime.setDateTime(initial_dt)
    button_minus_1m = find_button("-00:01")
    assert button_minus_1m is not None
    qtbot.mouseClick(button_minus_1m, Qt.LeftButton)
    expected_dt_l = QDateTime(2023, 1, 15, 10, 29, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_l.toString("yyyy:MM:dd HH:mm:ss")

    # Reset and test '+01:00' (U) button click
    mw.datetime.setDateTime(initial_dt)
    button_plus_1h = find_button("+01:00")
    assert button_plus_1h is not None
    qtbot.mouseClick(button_plus_1h, Qt.LeftButton)
    expected_dt_u = QDateTime(2023, 1, 15, 11, 30, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_u.toString("yyyy:MM:dd HH:mm:ss")

    # Reset and test '-01:00' (J) button click
    mw.datetime.setDateTime(initial_dt)
    button_minus_1h = find_button("-01:00")
    assert button_minus_1h is not None
    qtbot.mouseClick(button_minus_1h, Qt.LeftButton)
    expected_dt_j = QDateTime(2023, 1, 15, 9, 30, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_j.toString("yyyy:MM:dd HH:mm:ss")

    # Reset and test '+1d' (Y) button click
    mw.datetime.setDateTime(initial_dt)
    button_plus_1d = find_button("+1d")
    assert button_plus_1d is not None
    qtbot.mouseClick(button_plus_1d, Qt.LeftButton)
    expected_dt_y = QDateTime(2023, 1, 16, 10, 30, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_y.toString("yyyy:MM:dd HH:mm:ss")

    # Reset and test '-1d' (H) button click
    mw.datetime.setDateTime(initial_dt)
    button_minus_1d = find_button("-1d")
    assert button_minus_1d is not None
    qtbot.mouseClick(button_minus_1d, Qt.LeftButton)
    expected_dt_h = QDateTime(2023, 1, 14, 10, 30, 0)
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == expected_dt_h.toString("yyyy:MM:dd HH:mm:ss")
