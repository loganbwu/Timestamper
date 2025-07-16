import pytest
from main import MainWindow
from PySide6.QtCore import QSettings, QDateTime
from datetime import datetime
import os
from unittest import mock # Import mock directly

import exiftool # Import exiftool for mocking exceptions

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
def test_float_to_shutterspeed(qtbot): # Use qtbot fixture
    mw = MainWindow()
    qtbot.addWidget(mw) # Add widget to qtbot for proper lifecycle management
    assert mw.float_to_shutterspeed(0.5) == "1/2s"
    assert mw.float_to_shutterspeed(1/60) == "1/60s"
    assert mw.float_to_shutterspeed(1.0) == "1s"
    assert mw.float_to_shutterspeed(2.0) == "2s"
    assert mw.float_to_shutterspeed(0.001) == "1/1000s"

# Test parse_lensinfo
def test_parse_lensinfo(qtbot): # Use qtbot fixture
    mw = MainWindow()
    qtbot.addWidget(mw) # Add widget to qtbot for proper lifecycle management
    assert mw.parse_lensinfo("18 55 3.5 5.6") == ["18", "55", "3.5", "5.6"]

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
        def set_tags(self, path, tags):
            raise Exception("Mock Save Error")
        def get_metadata(self, path):
            return [{}] # Return empty metadata for select_file_from_list to proceed

    monkeypatch.setattr(exiftool, 'ExifToolHelper', MockExifToolHelperSaveError)
    monkeypatch.setattr(mw.settings, 'value', lambda key, default=None: "/mock/path/to/exiftool")
    monkeypatch.setattr(os.path, 'isfile', lambda x: True)

    # Simulate loading a file so current_exif is not None
    mw.current_path = "/mock/path/to/image.jpg"
    mw.current_exif = {"EXIF:DateTimeOriginal": "2023:01:01 12:00:00"}
    
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
