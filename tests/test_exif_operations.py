import pytest
from timestamper.main import MainWindow
from PySide6.QtCore import QSettings, QDateTime
from timestamper.constants import EXIF_DATE_TIME_ORIGINAL
import os
from unittest import mock
import exiftool
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize
from unittest.mock import patch, MagicMock

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

# Test populate_exif functionality
def test_populate_exif(qtbot, mock_settings):
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
