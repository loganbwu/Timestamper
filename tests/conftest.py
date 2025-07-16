import pytest
from PySide6.QtCore import QSettings

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
