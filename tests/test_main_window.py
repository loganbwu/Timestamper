import pytest
from src.timestamper.main import MainWindow
from PySide6.QtCore import QSettings, QDateTime
from src.timestamper.constants import EXIF_DATE_TIME_ORIGINAL
from src.timestamper.utils import float_to_shutterspeed, parse_lensinfo
from datetime import datetime
import os
from unittest import mock

import exiftool # Import exiftool for mocking exceptions
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QAbstractItemView
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QSize, Qt, QItemSelectionModel
from unittest.mock import patch, MagicMock


# Test _validate_numeric_input
def test_validate_numeric_input(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)
    
    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)

    # Test valid numeric input
    assert mw._validate_numeric_input("ISO", "100") == True
    assert mw._validate_numeric_input("FocalLength", "50.5") == True
    assert mw._validate_numeric_input("Exposure", "") == True # Empty string is valid

    # Test invalid numeric input
    assert mw._validate_numeric_input("ISO", "abc") == False
    mock_show_message.assert_called_with("Error: Invalid numeric input for ISO: 'abc'", 5000)
    mock_show_message.reset_mock()

    assert mw._validate_numeric_input("FNumber", "f/2.8") == False
    mock_show_message.assert_called_with("Error: Invalid numeric input for FNumber: 'f/2.8'", 5000)

# Test on_wideaperturevalue_editingfinished typo fix
def test_on_wideaperturevalue_editingfinished(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    # Set wideaperturevalue and ensure fnumber is updated
    mw.wideaperturevalue.setText("2.8")
    mw.on_wideaperturevalue_editingfinished()
    assert mw.fnumber.text() == "2.8"

    # Ensure fnumber is not overwritten if it already has a value
    mw.fnumber.setText("4.0")
    mw.wideaperturevalue.setText("1.8")
    mw.on_wideaperturevalue_editingfinished()
    assert mw.fnumber.text() == "4.0"

    # Ensure fnumber is not overwritten if longaperturevalue has a value
    mw.fnumber.clear()
    mw.longaperturevalue.setText("5.6")
    mw.wideaperturevalue.setText("1.8")
    mw.on_wideaperturevalue_editingfinished()
    assert mw.fnumber.text() == ""


# Test clear_fields functionality
def test_clear_fields(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    # Set some values in the fields
    mw.make.setText("Canon")
    mw.model.setText("EOS R5")
    mw.datetime.setDateTime(mw.datetime.minimumDateTime())
    mw.offsettime.setValue(5.0)
    mw.iso.setText("400")
    mw.exposuretime.setText("1/1000")
    mw.fnumber.setText("2.8")
    mw.focallength.setText("50")
    mw.widefocallength.setText("24")
    mw.longfocallength.setText("70")
    mw.wideaperturevalue.setText("2.8")
    mw.longaperturevalue.setText("4.0")
    mw.lensserialnumber.setText("12345")

    # Clear the fields
    mw.clear_fields()

    # Assert that all fields are cleared or reset to default
    assert mw.make.text() == ""
    assert mw.model.text() == ""
    # Compare only date and hour/minute, as seconds might differ slightly
    assert mw.datetime.dateTime().toString("yyyy-MM-dd HH:mm") == QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm")
    assert mw.offsettime.value() == 0.0
    assert mw.iso.text() == ""
    assert mw.exposuretime.text() == ""
    assert mw.fnumber.text() == ""
    assert mw.focallength.text() == ""
    assert mw.widefocallength.text() == ""
    assert mw.longfocallength.text() == ""
    assert mw.wideaperturevalue.text() == ""
    assert mw.longaperturevalue.text() == ""
    assert mw.lensserialnumber.text() == ""


def test_onLoadFilesButtonClick(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_selected_files = ["/path/to/image1.jpg", "/path/to/image2.png"]
    monkeypatch.setattr(QFileDialog, 'exec', lambda self: QFileDialog.Accepted)
    monkeypatch.setattr(QFileDialog, 'selectedFiles', lambda self: mock_selected_files)

    mw.files_done = [0] # Simulate a file already marked as done
    mw.file_list.addItem("dummy_item") # Add a dummy item to ensure clear() works

    with mock.patch('PySide6.QtGui.QPixmap'), mock.patch('PySide6.QtGui.QIcon'):
        mw.onLoadFilesButtonClick()

    assert mw.file_list.count() == 2
    assert mw.file_list.item(0).data(Qt.UserRole) == "/path/to/image1.jpg"
    assert mw.file_list.item(1).data(Qt.UserRole) == "/path/to/image2.png"
    assert mw.file_list.item(0).text() == "image1.jpg"
    assert mw.file_list.item(1).text() == "image2.png"
    assert mw.files_done == []
    assert mw.file_list.currentRow() == 0


def test_save_no_current_item(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_set_tags = mock.Mock()
    monkeypatch.setattr(exiftool.ExifToolHelper, 'set_tags', mock_set_tags)

    mw.save()
    mock_set_tags.assert_not_called() # Should not attempt to save if no item selected

def test_save_numeric_validation_failure(qtbot, monkeypatch, mock_settings):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)

    with mock.patch('PySide6.QtGui.QPixmap'), mock.patch('PySide6.QtGui.QIcon'):
        mw.load_files(["/mock/path/to/image.jpg"])
    mw.file_list.setCurrentRow(0)
    mw.current_exif = {"SourceFile": "/mock/path/to/image.jpg"}
    mock_show_message.reset_mock()

    mw.iso.setText("invalid_iso") # Set invalid input

    mw.save()

    mock_show_message.assert_called_with("Error: Invalid numeric input for ISO: 'invalid_iso'", 5000)
    # Ensure save operation is halted
    mock_set_tags = mock.Mock()
    monkeypatch.setattr(exiftool.ExifToolHelper, 'set_tags', mock_set_tags)
    mock_set_tags.assert_not_called()

def test_save_post_save_list_management(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {"SourceFile": "/mock/path/to/image.jpg"}
    class MockExifToolHelperSaveSuccess:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get_metadata(self, path):
            return [mock_exif_data]
        def set_tags(self, path, tags, params):
            pass

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSaveSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    with mock.patch('PySide6.QtGui.QPixmap'), mock.patch('PySide6.QtGui.QIcon'):
        # Scenario 1: Save first file, move to next
        mw.load_files(["file1.jpg", "file2.jpg", "file3.jpg"])
        mw.file_list.setCurrentRow(0)
        mw.current_exif = mock_exif_data
        mw.save()
        assert 0 in mw.files_done
        assert mw.file_list.currentRow() == 1

        # Scenario 2: Save middle file, move to next available (file3)
        mw.load_files(["file1.jpg", "file2.jpg", "file3.jpg"])
        mw.files_done = [0]
        mw.file_list.setCurrentRow(1)
        mw.current_exif = mock_exif_data
        mw.save()
        assert 1 in mw.files_done
        assert mw.file_list.currentRow() == 2 # Should skip file1 and go to file3

        # Scenario 3: Save last file, no next available, move to previous todo
        mw.load_files(["file1.jpg", "file2.jpg", "file3.jpg"])
        mw.files_done = [1]
        mw.file_list.setCurrentRow(2)
        mw.current_exif = mock_exif_data
        mw.save()
        assert 2 in mw.files_done
        assert mw.file_list.currentRow() == 0 # Should go to file1 (previous todo)

        # Scenario 4: Save only file
        mw.load_files(["single_file.jpg"])
        mw.file_list.setCurrentRow(0)
        mw.current_exif = mock_exif_data
        mw.save()
        assert 0 in mw.files_done
        assert mw.file_list.currentRow() == 0 # Stays on the same file

def test_populate_exif_onchange(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "EXIF:Make": "TestMakeOnChange",
        "EXIF:Model": "TestModelOnChange"
    }
    mw.current_exif = mock_exif_data

    # Ensure populate_exif is called when checked
    mw.populate_exif = mock.Mock()
    mw.populate_exif_onchange(2) # Qt.CheckState.Checked
    mw.populate_exif.assert_called_once_with(mock_exif_data)
    mw.populate_exif.reset_mock()

    # Ensure populate_exif is not called when unchecked
    mw.populate_exif_onchange(0) # Qt.CheckState.Unchecked
    mw.populate_exif.assert_not_called()

def test_adjust_datetime(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    initial_dt = QDateTime(2023, 1, 15, 10, 30, 0)
    mw.datetime.setDateTime(initial_dt)

    # Add 1 day, 2 hours, 30 minutes
    mw.adjust_datetime((1, 2, 30))
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == "2023:01:16 13:00:00"

    # Subtract 1 day, 2 hours, 30 minutes
    mw.datetime.setDateTime(initial_dt)
    mw.adjust_datetime((-1, -2, -30))
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == "2023:01:14 08:00:00"

# Test on_widefocallength_change and on_widefocallength_editingfinished
def test_on_widefocallength_change(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mw.longfocallength.setEnabled(False)
    mw.widefocallength.setText("50")
    assert mw.longfocallength.isEnabled()
    mw.widefocallength.clear()
    assert not mw.longfocallength.isEnabled()
    assert mw.longfocallength.text() == ""

def test_on_widefocallength_editingfinished(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    # If focallength is empty and longfocallength is empty, set focallength
    mw.widefocallength.setText("50")
    mw.focallength.clear()
    mw.longfocallength.clear()
    mw.on_widefocallength_editingfinished()
    assert mw.focallength.text() == "50"

    # If focallength is not empty, do not overwrite
    mw.focallength.setText("100")
    mw.widefocallength.setText("50")
    mw.on_widefocallength_editingfinished()
    assert mw.focallength.text() == "100"

    # If longfocallength is not empty, do not overwrite focallength
    mw.focallength.clear()
    mw.longfocallength.setText("70")
    mw.widefocallength.setText("50")
    mw.on_widefocallength_editingfinished()
    assert mw.focallength.text() == ""

# Test set_executable and browse_exiftool_path
def test_set_executable(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_set_value = mock.Mock()
    monkeypatch.setattr(mw.settings, 'setValue', mock_set_value)

    test_path = "/usr/local/bin/exiftool"
    mw.set_executable(test_path)
    mock_set_value.assert_called_once_with("exiftool", test_path)

def test_clear_presets(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_remove = mock.Mock()
    monkeypatch.setattr(mw.settings, 'remove', mock_remove)

    mock_refresh_camera = mock.Mock()
    mock_refresh_lens = mock.Mock()
    monkeypatch.setattr(mw.camera_preset_manager, 'refresh_presets', mock_refresh_camera)
    monkeypatch.setattr(mw.lens_preset_manager, 'refresh_presets', mock_refresh_lens)

    mw.clear_presets()

    mock_remove.assert_any_call("preset_cameras")
    mock_remove.assert_any_call("preset_lenses")
    mock_refresh_camera.assert_called_once()
    mock_refresh_lens.assert_called_once()


@pytest.fixture
def mw_new(qtbot):
    """Create and return a MainWindow instance for new features."""
    window = MainWindow()
    qtbot.addWidget(window)
    # Mock exiftool for all tests in this file
    with mock.patch('exiftool.ExifToolHelper') as mock_exiftool, \
         mock.patch.object(window, '_is_exiftool_available', return_value=True):
        # Configure the mock to return some basic metadata
        mock_instance = mock_exiftool.return_value.__enter__.return_value
        mock_instance.get_metadata.return_value = [{'SourceFile': 'mock.jpg'}]
        # The signal is already connected in the UIManager, no need to reconnect here.
        yield window

def test_apply_to_selected_save(mw_new, qtbot):
    """Test that the save operation applies to all selected files."""
    # Load some mock files
    files = ["/path/to/image1.jpg", "/path/to/image2.jpg", "/path/to/image3.jpg"]
    with mock.patch('src.timestamper.main.QPixmap'), mock.patch('src.timestamper.main.QIcon', return_value=QIcon()):
        mw_new.load_files(files)

    # Select multiple items
    mw_new.file_list.setCurrentRow(0)
    mw_new.file_list.selectionModel().setCurrentIndex(mw_new.file_list.model().index(1, 0), QItemSelectionModel.Select)
    mw_new.file_list.selectionModel().setCurrentIndex(mw_new.file_list.model().index(2, 0), QItemSelectionModel.Select)
    
    # Mock the save execution
    with mock.patch.object(mw_new, '_execute_save', return_value=True) as mock_execute_save:
        mw_new.save()
        # Assert that _execute_save was called for each selected file
        assert mock_execute_save.call_count == 3
        mock_execute_save.assert_any_call(files[0], mock.ANY)
        mock_execute_save.assert_any_call(files[1], mock.ANY)
        mock_execute_save.assert_any_call(files[2], mock.ANY)

def test_thumbnail_view_loading(mw_new, qtbot):
    """Test that files are loaded as thumbnails."""
    files = ["/path/to/image1.jpg"]
    with mock.patch('src.timestamper.main.QPixmap'), mock.patch('src.timestamper.main.QIcon', return_value=QIcon()):
        mw_new.load_files(files)
        assert mw_new.file_list.count() == 1
        item = mw_new.file_list.item(0)
        assert isinstance(item, QListWidgetItem)
        assert item.icon() is not None
        assert item.text() == "image1.jpg"
        assert item.data(Qt.UserRole) == "/path/to/image1.jpg"

def test_selection_change_updates_ui(mw_new, qtbot):
    """Test that selecting a thumbnail updates the UI."""
    files = ["/path/to/image1.jpg", "/path/to/image2.jpg"]
    with mock.patch('src.timestamper.main.QPixmap'), mock.patch('src.timestamper.main.QIcon', return_value=QIcon()):
        mw_new.load_files(files)
    
    with mock.patch.object(mw_new, '_load_exif_data') as mock_load_exif, \
         mock.patch.object(mw_new, '_update_exif_info_view') as mock_update_exif, \
         mock.patch.object(mw_new, '_update_image_preview') as mock_update_preview:
        
        # Reset mocks after initial load
        mock_load_exif.reset_mock()
        mock_update_exif.reset_mock()
        mock_update_preview.reset_mock()

        mw_new.file_list.setCurrentRow(1)
        
        mock_load_exif.assert_called_once()
        mock_update_exif.assert_called_once()
        mock_update_preview.assert_called_once()
        assert mw_new.current_path == "/path/to/image2.jpg"
