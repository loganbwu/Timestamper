import pytest
from unittest.mock import patch
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QMessageBox
from src.timestamper.main import MainWindow
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


def test_exiftool_not_found_dialog(qtbot, app):
    """Test that the exiftool not found dialog is shown."""
    settings = QSettings("Test", "Timestamper")
    settings.clear()

    window = MainWindow()
    qtbot.addWidget(window)

    # Simulate that exiftool path is not set
    window.exif_manager = None

    # Add a dummy file to the list to ensure the selection changed handler runs fully
    with patch('PySide6.QtGui.QPixmap'), patch('PySide6.QtGui.QIcon'):
        window.load_files(["/mock/path/to/image.jpg"])
    window.file_list.setCurrentRow(0)

    # Mock QMessageBox to check if it's called
    with patch('PySide6.QtWidgets.QMessageBox.exec') as mock_exec:
        mock_exec.return_value = QMessageBox.Yes
        
        # Mock the settings dialog to prevent it from actually opening
        with patch('src.timestamper.main.SettingsDialog.exec') as mock_settings_exec:
            # Trigger the action that should show the dialog
            window.on_file_selection_changed()

            # Assert that the message box was shown
            mock_exec.assert_called_once()
            
            # Assert that the settings dialog was shown
            mock_settings_exec.assert_called_once()

    settings.clear()
