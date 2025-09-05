import pytest
from src.timestamper.main import MainWindow
from PySide6.QtCore import QDateTime
from src.timestamper.constants import EXIF_DATE_TIME_ORIGINAL
from src.timestamper.exif_manager import ExifToolNotFound
import os
from unittest import mock
from PySide6.QtGui import QIcon
from unittest.mock import patch, MagicMock, call

@pytest.fixture
def mw(qtbot):
    """Create a MainWindow instance with a mocked ExifManager."""
    with patch('src.timestamper.main.ExifManager') as mock_exif_manager:
        window = MainWindow()
        qtbot.addWidget(window)
        window.exif_manager = mock_exif_manager.return_value
        yield window

def test_select_file_from_list_exiftool_error(mw, qtbot):
    """Test that the settings dialog is shown when loading EXIF fails."""
    mw.exif_manager.load_exif_data.side_effect = ExifToolNotFound

    with patch.object(mw, 'open_settings_dialog') as mock_open_settings:
        with patch('src.timestamper.main.QPixmap'), patch('src.timestamper.main.QIcon', return_value=QIcon()):
            mw.load_files(["/mock/path/to/image.jpg"])
        mw.file_list.setCurrentRow(0)

        mock_open_settings.assert_called_once()
        assert mw.current_exif is None

def test_save_exiftool_error(mw, qtbot):
    """Test that the settings dialog is shown when saving EXIF fails."""
    mw.exif_manager.save_exif_data.side_effect = ExifToolNotFound

    with patch.object(mw, 'open_settings_dialog') as mock_open_settings:
        with patch('src.timestamper.main.QPixmap'), patch('src.timestamper.main.QIcon', return_value=QIcon()):
            mw.load_files(["/mock/path/to/image.jpg"])
        mw.file_list.setCurrentRow(0)
        mw.save()

        mock_open_settings.assert_called_once()

def test_select_file_from_list_no_exiftool_path(mw, qtbot):
    """Test that the settings dialog is shown when exiftool is not configured."""
    mw.exif_manager = None  # Simulate exiftool not being configured

    with patch.object(mw, 'open_settings_dialog') as mock_open_settings:
        with patch('src.timestamper.main.QPixmap'), patch('src.timestamper.main.QIcon', return_value=QIcon()):
            mw.load_files(["/mock/path/to/image.jpg"])
        mw.file_list.setCurrentRow(0)

        mock_open_settings.assert_called_once()
        assert mw.current_exif is None

def test_select_file_from_list_success(mw, qtbot):
    """Test successful loading and display of EXIF data."""
    mock_exif_data = {
        "SourceFile": "/mock/path/to/image.jpg",
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
    }
    mw.exif_manager.load_exif_data.return_value = mock_exif_data

    with patch('src.timestamper.main.QPixmap'), patch('src.timestamper.main.QIcon', return_value=QIcon()):
        mw.load_files(["/mock/path/to/image.jpg"])
    mw.file_list.setCurrentRow(0)

    assert mw.current_path == "/mock/path/to/image.jpg"
    assert mw.current_exif == mock_exif_data
    assert mw.info.topLevelItem(0).text(0) == "EXIF"
    assert mw.info.topLevelItem(0).child(0).text(0) == "DateTimeOriginal"
    assert mw.statusBar().currentMessage() == 'Opened EXIF for "/mock/path/to/image.jpg"'

def test_save_success(mw, qtbot, monkeypatch):
    """Test successful saving of EXIF data."""
    mw.exif_manager.save_exif_data.return_value = True

    with patch('src.timestamper.main.QPixmap'), patch('src.timestamper.main.QIcon', return_value=QIcon()):
        mw.load_files(["/mock/path/to/image.jpg", "/mock/path/to/image2.jpg"])
    mw.file_list.setCurrentRow(0)

    mw.make.setText("TestMake")
    mw.save()

    mw.exif_manager.save_exif_data.assert_called_once()
    assert "TestMake" in mw.exif_manager.save_exif_data.call_args[0][1]['Make']
    assert 0 in mw.files_done
    assert mw.file_list.currentRow() == 1

def test_populate_exif(mw, qtbot):
    """Test populating form fields from EXIF data."""
    mock_exif_data = {
        "EXIF:DateTimeOriginal": "2023:01:15 10:30:00",
        "EXIF:OffsetTimeOriginal": "+08:00",
        "EXIF:Make": "TestMake",
        "EXIF:Model": "TestModel",
        "EXIF:ExposureTime": 0.01, # 1/100s
        "EXIF:LensInfo": "18 55 3.5 5.6"
    }

    mw.populate_exif(mock_exif_data)

    assert mw.make.text() == "TestMake"
    assert mw.model.text() == "TestModel"
    assert mw.exposuretime.text() == "1/100"
    assert mw.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss") == "2023:01:15 10:30:00"
    assert mw.offsettime.value() == 8.0
    assert mw.widefocallength.text() == "18"
    assert mw.longfocallength.text() == "55"
    assert mw.wideaperturevalue.text() == "3.5"
    assert mw.longaperturevalue.text() == "5.6"
