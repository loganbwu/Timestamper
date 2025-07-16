import pytest
from timestamper.main import MainWindow
from PySide6.QtCore import QSettings, QDateTime
from timestamper.constants import EXIF_DATE_TIME_ORIGINAL
from timestamper.utils import float_to_shutterspeed, parse_lensinfo
from datetime import datetime
import os
from unittest import mock

import exiftool # Import exiftool for mocking exceptions
import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize
from unittest.mock import patch, MagicMock

# Mock QSettings for testing
@pytest.fixture
def mock_settings(monkeypatch):
    class MockQSettings:
        def __init__(self, org, app):
            self._data = {}
        
        def value(self, key, default=None):
            return self._data.get(key, default)
        
        def setValue(self, key, value):
            self._data[key] = value
            
        def remove(self, key):
            if key in self._data:
                del self._data[key]

    monkeypatch.setattr(QSettings, '__init__', MockQSettings.__init__)
    monkeypatch.setattr(QSettings, 'value', MockQSettings.value)
    monkeypatch.setattr(QSettings, 'setValue', MockQSettings.setValue)
    monkeypatch.setattr(QSettings, 'remove', MockQSettings.remove)
    return MockQSettings("Test", "Timestamper")

# Test float_to_shutterspeed
def test_float_to_shutterspeed():
    assert float_to_shutterspeed(0.5) == "1/2"
    assert float_to_shutterspeed(1/60) == "1/60"
    assert float_to_shutterspeed(1.0) == "1"
    assert float_to_shutterspeed(2.0) == "2"
    assert float_to_shutterspeed(0.001) == "1/1000"

# Test parse_lensinfo
def test_parse_lensinfo():
    assert parse_lensinfo("18 55 3.5 5.6") == ["18", "55", "3.5", "5.6"]

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

# Test Exiftool error handling in select_file_from_list
def test_select_file_from_list_exiftool_error(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)
    
    # Mock exiftool.ExifToolHelper to raise an error
    class MockExifToolHelperError:
        def __init__(self, executable):
            pass
        def __enter__(self):
            raise Exception("Mock Exiftool Error")
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperError)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True) # Pretend exiftool exists

    mw.current_path = "/mock/path/to/image.jpg"
    mw.select_file_from_list("/mock/path/to/image.jpg")

    mock_show_message.assert_called_with('Error: Exiftool operation failed for "/mock/path/to/image.jpg". Mock Exiftool Error', 5000)
    assert mw.current_exif is None

# Test Exiftool error handling in save
def test_save_exiftool_error(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)
    
    # Mock exiftool.ExifToolHelper to raise an error on set_tags
    class MockExifToolHelperSaveError:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def set_tags(self, path, tags, params): # Added params argument
            raise Exception("Mock Save Error")
        def get_metadata(self, path):
            return [{}] # Return empty metadata for select_file_from_list to proceed

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSaveError)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    # Simulate loading a file so current_exif is not None
    mw.current_path = "/mock/path/to/image.jpg"
    mw.current_exif = {EXIF_DATE_TIME_ORIGINAL: "2023:01:01 12:00:00"}
    
    # Mock currentItem for save function
    mock_list_item = mock.Mock()
    mock_list_item.text.return_value = "/mock/path/to/image.jpg"
    monkeypatch.setattr(mw.file_list, 'currentItem', lambda: mock_list_item)

    mw.save()

    mock_show_message.assert_called_with('Error: Failed to save EXIF to "/mock/path/to/image.jpg". Mock Save Error', 5000)

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

# Test PresetManager functionality
def test_preset_manager_add_load_remove_camera(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    # Mock QSettings to control saved presets
    mock_settings_data = {}
    def mock_settings_value(key, default=None):
        return mock_settings_data.get(key, default)
    def mock_settings_set_value(key, value):
        mock_settings_data[key] = value
    def mock_settings_remove(key):
        if key in mock_settings_data:
            del mock_settings_data[key]

    monkeypatch.setattr(mw.settings, 'value', mock_settings_value)
    monkeypatch.setattr(mw.settings, 'setValue', mock_settings_set_value)
    monkeypatch.setattr(mw.settings, 'remove', mock_settings_remove)

    # Re-initialize preset managers after mocking settings
    mw.camera_preset_manager.refresh_presets()
    mw.lens_preset_manager.refresh_presets()

    # Test adding a camera preset
    mw.make.setText("Nikon")
    mw.model.setText("D850")
    mw.preset_camera_name.setEditText("My Nikon")
    mw.camera_preset_manager.add_preset("My Nikon")

    assert {"Name": "My Nikon", "Make": "Nikon", "Model": "D850"} in mock_settings_data["preset_cameras"]
    assert mw.preset_camera_name.findText("My Nikon") != -1

    # Test loading a camera preset
    mw.make.clear()
    mw.model.clear()
    mw.preset_camera_name.setCurrentText("My Nikon")
    assert mw.make.text() == "Nikon"
    assert mw.model.text() == "D850"

    # Test removing a camera preset
    mw.camera_preset_manager.remove_preset("My Nikon")
    assert {"Name": "My Nikon", "Make": "Nikon", "Model": "D850"} not in mock_settings_data["preset_cameras"]
    assert mw.preset_camera_name.findText("My Nikon") == -1

def test_preset_manager_add_load_remove_lens(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    # Mock QSettings to control saved presets
    mock_settings_data = {}
    def mock_settings_value(key, default=None):
        return mock_settings_data.get(key, default)
    def mock_settings_set_value(key, value):
        mock_settings_data[key] = value
    def mock_settings_remove(key):
        if key in mock_settings_data:
            del mock_settings_data[key]

    monkeypatch.setattr(mw.settings, 'value', mock_settings_value)
    monkeypatch.setattr(mw.settings, 'setValue', mock_settings_set_value)
    monkeypatch.setattr(mw.settings, 'remove', mock_settings_remove)

    # Re-initialize preset managers after mocking settings
    mw.camera_preset_manager.refresh_presets()
    mw.lens_preset_manager.refresh_presets()

    # Test adding a lens preset
    mw.lensmake.setText("Sigma")
    mw.lensmodel.setText("35mm Art")
    mw.widefocallength.setText("35")
    mw.longfocallength.setText("35")
    mw.wideaperturevalue.setText("1.4")
    mw.longaperturevalue.setText("1.4")
    mw.lensserialnumber.setText("SN12345")
    mw.preset_lens_name.setEditText("My Sigma 35mm")
    mw.lens_preset_manager.add_preset("My Sigma 35mm")

    expected_lens_preset = {
        "Name": "My Sigma 35mm",
        "LensMake": "Sigma",
        "LensModel": "35mm Art",
        "WideFocalLength": "35",
        "LongFocalLength": "35",
        "WideApertureValue": "1.4",
        "LongApertureValue": "1.4",
        "LensSerialNumber": "SN12345"
    }
    assert expected_lens_preset in mock_settings_data["preset_lenses"]
    assert mw.preset_lens_name.findText("My Sigma 35mm") != -1

    # Test loading a lens preset
    mw.lensmake.clear()
    mw.lensmodel.clear()
    mw.widefocallength.clear()
    mw.longfocallength.clear()
    mw.wideaperturevalue.clear()
    mw.longaperturevalue.clear()
    mw.lensserialnumber.clear()
    mw.preset_lens_name.setCurrentText("My Sigma 35mm")
    assert mw.lensmake.text() == "Sigma"
    assert mw.lensmodel.text() == "35mm Art"
    assert mw.widefocallength.text() == "35"
    assert mw.longfocallength.text() == "35"
    assert mw.wideaperturevalue.text() == "1.4"
    assert mw.longaperturevalue.text() == "1.4"
    assert mw.lensserialnumber.text() == "SN12345"

    # Test removing a lens preset
    mw.lens_preset_manager.remove_preset("My Sigma 35mm")
    assert expected_lens_preset not in mock_settings_data["preset_lenses"]
    assert mw.preset_lens_name.findText("My Sigma 35mm") == -1

def test_onLoadFilesButtonClick(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_file_dialog_result = (["/path/to/image1.jpg", "/path/to/image2.png"], "Images (*.jpg *.png)")
    monkeypatch.setattr(QFileDialog, 'getOpenFileNames', lambda *args, **kwargs: mock_file_dialog_result)

    mw.files_done = [0] # Simulate a file already marked as done
    mw.file_list.addItem("dummy_item") # Add a dummy item to ensure clear() works

    mw.onLoadFilesButtonClick()

    assert mw.file_list.count() == 2
    assert mw.file_list.item(0).text() == "/path/to/image1.jpg"
    assert mw.file_list.item(1).text() == "/path/to/image2.png"
    assert mw.files_done == []
    assert mw.file_list.currentRow() == 0

# Test select_file_from_list functionality
def test_select_file_from_list_success(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "SourceFile": "/mock/path/to/image.jpg",
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
        "EXIF:OffsetTimeOriginal": "+08:00",
        "EXIF:Make": "TestMake",
        "EXIF:Model": "TestModel",
        "EXIF:ExposureTime": 0.01,
        "EXIF:LensInfo": "18 55 3.5 5.6"
    }

    class MockExifToolHelperSuccess:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get_metadata(self, path):
            return [mock_exif_data]

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    # Mock QPixmap to prevent actual image loading errors
    mock_pixmap = MagicMock(spec=QPixmap)
    mock_pixmap.scaled.return_value = mock_pixmap
    monkeypatch.setattr(QPixmap, '__init__', lambda *args, **kwargs: None)
    monkeypatch.setattr(QPixmap, 'scaled', lambda *args, **kwargs: mock_pixmap)
    monkeypatch.setattr(QPixmap, 'size', lambda *args, **kwargs: QSize(100, 100))

    mw.select_file_from_list("/mock/path/to/image.jpg")

    assert mw.current_path == "/mock/path/to/image.jpg"
    assert mw.current_exif == mock_exif_data
    assert mw.info.topLevelItem(0).text(0) == "EXIF"
    assert mw.info.topLevelItem(0).child(0).text(0) == "DateTimeOriginal"
    assert mw.info.topLevelItem(0).child(0).text(1) == "2023:01:15 10:30:00"
    assert mw.statusBar().currentMessage() == 'Opened EXIF for "/mock/path/to/image.jpg"'

def test_select_file_from_list_amend_mode(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "SourceFile": "/mock/path/to/image.jpg",
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
        "EXIF:OffsetTimeOriginal": "+08:00",
        "EXIF:Make": "TestMake",
        "EXIF:Model": "TestModel",
        "EXIF:ExposureTime": 0.01,
        "EXIF:LensInfo": "18 55 3.5 5.6"
    }

    class MockExifToolHelperSuccess:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get_metadata(self, path):
            return [mock_exif_data]

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mock_pixmap = MagicMock(spec=QPixmap)
    mock_pixmap.scaled.return_value = mock_pixmap
    monkeypatch.setattr(QPixmap, '__init__', lambda *args, **kwargs: None)
    monkeypatch.setattr(QPixmap, 'scaled', lambda *args, **kwargs: mock_pixmap)
    monkeypatch.setattr(QPixmap, 'size', lambda *args, **kwargs: QSize(100, 100))

    mw.amend_mode.setChecked(True)
    mw.select_file_from_list("/mock/path/to/image.jpg")

    assert mw.make.text() == "TestMake"
    assert mw.model.text() == "TestModel"
    assert mw.exposuretime.text() == "1/100s"
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == "2023:01:15 10:30:00"
    assert mw.offsettime.value() == 8.0

    # Test with a "done" file
    mw.make.clear()
    mw.model.clear()
    mw.amend_mode.setChecked(False) # Ensure amend_mode is off
    mw.select_file_from_list(mw.done_icon + "/mock/path/to/image.jpg")
    assert mw.make.text() == "TestMake"
    assert mw.model.text() == "TestModel"

def test_select_file_from_list_no_exiftool_path(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "") # No exiftool path
    monkeypatch.setattr(os.path, 'isfile', lambda x: False) # exiftool does not exist

    mw.select_file_from_list("/mock/path/to/image.jpg")

    mock_show_message.assert_called_with("Error: Could not find exiftool executable. Please check the path.", 5000)
    assert mw.current_exif is None

def test_select_file_from_list_image_load_error(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "SourceFile": "/mock/path/to/image.jpg",
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00"
    }

    class MockExifToolHelperSuccess:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get_metadata(self, path):
            return [mock_exif_data]

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    # Mock QPixmap to raise an error
    def mock_pixmap_init_error(*args, **kwargs):
        raise Exception("Mock Image Load Error")
    monkeypatch.setattr(QPixmap, '__init__', mock_pixmap_init_error)

    mw.select_file_from_list("/mock/path/to/invalid_image.jpg")

    assert mw.pic.text() == "No picture selected."

# Test save functionality
def test_save_success(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "SourceFile": "/mock/path/to/image.jpg",
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
        "EXIF:OffsetTimeOriginal": "+08:00"
    }

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
            assert path == "/mock/path/to/image.jpg"
            assert tags["DateTimeOriginal"] == "2024:07:16 15:00:00"
            assert tags["Make"] == "TestMake"
            assert tags["LensInfo"] == "24 70 2.8 4.0"
            assert "-overwrite_original" in params

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSaveSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    # Simulate loading a file
    mw.current_path = "/mock/path/to/image.jpg"
    mw.current_exif = mock_exif_data
    mw.file_list.addItem("/mock/path/to/image.jpg")
    mw.file_list.addItem("/mock/path/to/image2.jpg")
    mw.file_list.setCurrentRow(0)

    # Set some values
    mw.datetime.setDateTime(QDateTime(2024, 7, 16, 15, 0, 0))
    mw.offsettime.setValue(0.0)
    mw.make.setText("TestMake")
    mw.widefocallength.setText("24")
    mw.longfocallength.setText("70")
    mw.wideaperturevalue.setText("2.8")
    mw.longaperturevalue.setText("4.0")

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)

    mw.save()

    expected_tags = {
        "DateTimeOriginal": "2024:07:16 15:00:00",
        "OffsetTimeOriginal": "+00:00",
        "OffsetTime": "+00:00",
        "Make": "TestMake",
        "MaxApertureValue": "2.8",
        "LensInfo": "24 70 2.8 4.0",
        "FNumber": "2.8"
    }
    saved_call = mock.call(f"Saved EXIF to file: {expected_tags}", 3000)
    assert saved_call in mock_show_message.call_args_list
    assert mw.file_list.item(0).text().startswith(mw.done_icon)
    assert mw.file_list.currentRow() == 1 # Should move to the next file

def test_save_no_current_item(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_set_tags = mock.Mock()
    monkeypatch.setattr(exiftool.ExifToolHelper, 'set_tags', mock_set_tags)

    mw.save()
    mock_set_tags.assert_not_called() # Should not attempt to save if no item selected

def test_save_numeric_validation_failure(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_show_message = mock.Mock()
    monkeypatch.setattr(mw.statusBar(), 'showMessage', mock_show_message)

    mw.current_path = "/mock/path/to/image.jpg"
    mw.current_exif = {}
    mw.file_list.addItem("/mock/path/to/image.jpg")
    mw.file_list.setCurrentRow(0)

    mw.iso.setText("invalid_iso") # Set invalid input

    mw.save()

    mock_show_message.assert_called_with("Error: Invalid numeric input for ISO: 'invalid_iso'", 5000)
    # Ensure save operation is halted
    mock_set_tags = mock.Mock()
    monkeypatch.setattr(exiftool.ExifToolHelper, 'set_tags', mock_set_tags)
    mock_set_tags.assert_not_called()

def test_save_lensinfo_logic(qtbot, monkeypatch):
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
            assert tags["LensInfo"] == expected_lensinfo

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSaveSuccess)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    mw.current_path = "/mock/path/to/image.jpg"
    mw.current_exif = mock_exif_data
    mw.file_list.addItem("/mock/path/to/image.jpg")
    mw.file_list.setCurrentRow(0)

    # Case 1: Only wide focal length and wide aperture
    mw.widefocallength.setText("50")
    mw.wideaperturevalue.setText("1.8")
    mw.longfocallength.clear()
    mw.longaperturevalue.clear()
    expected_lensinfo = "50 50 1.8 1.8"
    mw.save()

    # Case 2: All lens info fields
    mw.widefocallength.setText("24")
    mw.longfocallength.setText("70")
    mw.wideaperturevalue.setText("2.8")
    mw.longaperturevalue.setText("4.0")
    expected_lensinfo = "24 70 2.8 4.0"
    mw.save()

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

    # Scenario 1: Save first file, move to next
    mw.file_list.clear()
    mw.file_list.addItems(["file1.jpg", "file2.jpg", "file3.jpg"])
    mw.file_list.setCurrentRow(0)
    mw.current_path = "file1.jpg"
    mw.current_exif = mock_exif_data
    mw.save()
    assert mw.file_list.item(0).text().startswith(mw.done_icon)
    assert mw.file_list.currentRow() == 1

    # Scenario 2: Save middle file, move to next available (file3)
    mw.file_list.clear()
    mw.files_done = []
    mw.file_list.addItems(["file1.jpg", "file2.jpg", "file3.jpg"])
    mw.file_list.item(0).setText(mw.done_icon + "file1.jpg") # Mark file1 as done
    mw.files_done.append(0)
    mw.file_list.setCurrentRow(1)
    mw.current_path = "file2.jpg"
    mw.current_exif = mock_exif_data
    mw.save()
    assert mw.file_list.item(1).text().startswith(mw.done_icon)
    assert mw.file_list.currentRow() == 2 # Should skip file1 and go to file3

    # Scenario 3: Save last file, no next available, move to previous todo
    mw.file_list.clear()
    mw.files_done = []
    mw.file_list.addItems(["file1.jpg", "file2.jpg", "file3.jpg"])
    mw.file_list.item(1).setText(mw.done_icon + "file2.jpg") # Mark file2 as done
    mw.files_done.append(1)
    mw.file_list.setCurrentRow(2)
    mw.current_path = "file3.jpg"
    mw.current_exif = mock_exif_data
    mw.save()
    assert mw.file_list.item(2).text().startswith(mw.done_icon)
    assert mw.file_list.currentRow() == 0 # Should go to file1 (previous todo)

    # Scenario 4: Save only file
    mw.file_list.clear()
    mw.files_done = []
    mw.file_list.addItem("single_file.jpg")
    mw.file_list.setCurrentRow(0)
    mw.current_path = "single_file.jpg"
    mw.current_exif = mock_exif_data
    mw.save()
    assert mw.file_list.item(0).text().startswith(mw.done_icon)
    assert mw.file_list.currentRow() == 0 # Stays on the same file

# Test populate_exif functionality
def test_populate_exif(qtbot):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_exif_data = {
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
        "EXIF:OffsetTimeOriginal": "+08:00",
        "EXIF:Make": "TestMake",
        "EXIF:Model": "TestModel",
        "EXIF:ExposureTime": 0.01, # 1/100s
        "EXIF:ShutterSpeedValue": 0.005, # 1/200s, should be overridden by ExposureTime
        "EXIF:LensMake": "TestLensMake",
        "EXIF:LensModel": "TestLensModel",
        "EXIF:WideFocalLength": 24.0,
        "EXIF:LongFocalLength": 70.0,
        "EXIF:WideApertureValue": 2.8,
        "EXIF:LongApertureValue": 4.0,
        "EXIF:LensSerialNumber": "SN12345",
        "EXIF:LensInfo": "18 55 3.5 5.6" # Should be parsed
    }

    mw.populate_exif(mock_exif_data)

    assert mw.make.text() == "TestMake"
    assert mw.model.text() == "TestModel"
    assert mw.lensmake.text() == "TestLensMake"
    assert mw.lensmodel.text() == "TestLensModel"
    assert mw.lensserialnumber.text() == "SN12345"
    assert mw.exposuretime.text() == "1/100s"
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == "2023:01:15 10:30:00"
    assert mw.offsettime.value() == 8.0
    assert mw.widefocallength.text() == "18"
    assert mw.longfocallength.text() == "55"
    assert mw.wideaperturevalue.text() == "3.5"
    assert mw.longaperturevalue.text() == "5.6"
    assert mw.preset_camera_name.currentText() == "(None)"
    assert mw.preset_lens_name.currentText() == "(None)"

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

def test_browse_exiftool_path(qtbot, monkeypatch):
    mw = MainWindow()
    qtbot.addWidget(mw)

    mock_file_dialog_exec = mock.Mock(return_value=QFileDialog.Accepted)
    mock_file_dialog_selected_files = mock.Mock(return_value=["/new/path/to/exiftool"])
    
    monkeypatch.setattr(QFileDialog, 'exec', mock_file_dialog_exec)
    monkeypatch.setattr(QFileDialog, 'selectedFiles', mock_file_dialog_selected_files)
    
    mock_set_executable = mock.Mock()
    monkeypatch.setattr(mw, 'set_executable', mock_set_executable)

    mw.browse_exiftool_path()

    assert mw.executable.text() == "/new/path/to/exiftool"
    mock_set_executable.assert_called_once_with("/new/path/to/exiftool")

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
