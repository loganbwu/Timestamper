import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QPushButton
from src.timestamper.settings_dialog import SettingsDialog

@pytest.fixture
def app(qtbot):
    """Create a QApplication instance."""
    test_app = QApplication.instance()
    if test_app is None:
        test_app = QApplication([])
    return test_app

def test_settings_dialog(qtbot, app):
    """Test the SettingsDialog."""
    # Clear settings before test
    settings = QSettings("Test", "Timestamper")
    settings.clear()

    dialog = SettingsDialog()
    qtbot.addWidget(dialog)

    # Check that the line edit is initially empty
    assert dialog.exiftool_path_edit.text() == ""

    # Set a path and save
    test_path = "/usr/local/bin/exiftool"
    dialog.exiftool_path_edit.setText(test_path)
    
    save_button = dialog.findChild(QPushButton, "save_button")
    assert save_button is not None
    qtbot.mouseClick(save_button, Qt.LeftButton)

    # Check that the setting was saved
    assert settings.value("exiftool") == test_path

    # Re-open the dialog and check that the path is loaded
    dialog2 = SettingsDialog()
    qtbot.addWidget(dialog2)
    assert dialog2.exiftool_path_edit.text() == test_path

    # Clean up
    settings.clear()
