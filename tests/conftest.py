import pytest
from PySide6.QtCore import QSettings
import os
from unittest.mock import MagicMock

# Mock QSettings for testing
@pytest.fixture
def mock_settings(monkeypatch):
    class MockQSettings:
        def __init__(self, org, app):
            self._data = {}
            # Set a default mocked exiftool path
            self._data["exiftool"] = "/mock/path/to/exiftool"
        
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

# Global fixture to mock external dependencies like exiftool and file system checks
@pytest.fixture(autouse=True)
def mock_external_dependencies(monkeypatch):
    # Mock exiftool.ExifToolHelper
    class MockExifToolHelper:
        def __init__(self, executable):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get_metadata(self, path):
            # Return a basic dict for any file, as expected by _update_exif_info_view
            return {'SourceFile': path}
        def set_tags(self, path, tags, params):
            pass

    monkeypatch.setattr('exiftool.ExifToolHelper', MockExifToolHelper)

    # Mock os.path.isfile to prevent actual file system checks
    original_isfile = os.path.isfile
    def mock_isfile(path_to_check):
        if path_to_check == "/mock/path/to/exiftool":
            return True
        # Assume any path ending with image extensions exists for testing purposes
        if path_to_check.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
            return True
        return original_isfile(path_to_check) # Fallback for other real files

    monkeypatch.setattr(os.path, 'isfile', mock_isfile)

    # Mock os.path.isdir for QFileDialog
    original_isdir = os.path.isdir
    def mock_isdir(path_to_check):
        if path_to_check == "/mock/path/to/folder":
            return True
        return original_isdir(path_to_check)
    monkeypatch.setattr(os.path, 'isdir', mock_isdir)

    # Mock QPixmap and QIcon to prevent loading actual images and their potential errors
    # QPixmap needs to return an object that has an isNull method
    mock_pixmap_instance = MagicMock()
    mock_pixmap_instance.isNull.return_value = False
    mock_pixmap_instance.scaled.return_value = mock_pixmap_instance # scaled should return a pixmap too
    monkeypatch.setattr('PySide6.QtGui.QPixmap', MagicMock(return_value=mock_pixmap_instance))
    monkeypatch.setattr('PySide6.QtGui.QIcon', MagicMock(return_value=MagicMock()))

    # Mock QMessageBox.exec to prevent popups
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.exec', MagicMock(return_value=0)) # Return 0 for No/Cancel
