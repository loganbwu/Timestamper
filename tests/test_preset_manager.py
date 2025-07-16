import pytest
from timestamper.main import MainWindow

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
    mw.preset_camera_name.setCurrentText("(None)")
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
    mw.preset_lens_name.setCurrentText("(None)")
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
