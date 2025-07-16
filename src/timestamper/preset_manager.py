from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QComboBox, QLineEdit
from typing import Callable
from constants import NULL_PRESET_NAME
import logging

logger = logging.getLogger(__name__)

class PresetManager:
    """Manages loading, adding, and removing presets for cameras and lenses."""
    def __init__(self, settings: QSettings, preset_type: str, combo_box: QComboBox, fields_map: dict[str, QLineEdit], status_bar_callback: Callable[[str, int], None]):
        """
        Initializes the PresetManager.

        Args:
            settings: The QSettings object for storing presets.
            preset_type: The type of preset (e.g., "cameras" or "lenses").
            combo_box: The QComboBox widget for displaying presets.
            fields_map: A dictionary mapping preset keys to QLineEdit widgets.
            status_bar_callback: A callback function to update the status bar.
        """
        self.settings = settings
        self.preset_type = preset_type
        self.combo_box = combo_box
        self.fields_map = fields_map
        self.status_bar_callback = status_bar_callback

        self.presets: list[dict] = []
        self.refresh_presets()

    def refresh_presets(self):
        """Refreshes the list of presets from settings and updates the combo box."""
        existing_presets = self.settings.value(f"preset_{self.preset_type}", [])
        self.presets = [{"Name": NULL_PRESET_NAME}] + existing_presets
        self.combo_box.clear()
        if self.presets:
            self.combo_box.addItems([x["Name"] for x in self.presets])

    def load_preset(self, item: str):
        """Loads the selected preset into the corresponding fields."""
        if not item or not self.presets:
            return
            
        selected_presets = [x for x in self.presets if x["Name"] == item]
        if selected_presets:
            preset = selected_presets[0]
            for key, widget in self.fields_map.items():
                value = preset.get(key, "")
                if widget:
                    widget.setText(str(value))

    def add_preset(self, name: str):
        """Adds or updates a preset."""
        if not name:
            return
            
        new_preset = {"Name": name}
        for key, widget in self.fields_map.items():
            if widget:
                new_preset[key] = widget.text()

        self.presets = [x for x in self.presets if x["Name"] != new_preset["Name"]]
        self.presets.append(new_preset)
        self.presets.sort(key=lambda x: x["Name"])

        self.settings.setValue(f"preset_{self.preset_type}", self._remove_none_preset(self.presets))
        current_name = new_preset["Name"]
        self.refresh_presets()
        self.combo_box.setCurrentText(current_name)
        message = f"Preset '{current_name}' for {self.preset_type} has been added."
        logger.info(message)
        self.status_bar_callback(message, 3000)

    def remove_preset(self, name: str):
        """Removes a preset."""
        if not name or name == NULL_PRESET_NAME:
            return
            
        self.presets = [x for x in self.presets if x["Name"] != name]
        self.settings.setValue(f"preset_{self.preset_type}", self._remove_none_preset(self.presets))
        self.refresh_presets()
        message = f"Preset '{name}' for {self.preset_type} has been removed."
        logger.info(message)
        self.status_bar_callback(message, 3000)

    def _remove_none_preset(self, presets: list[dict]) -> list[dict]:
        """Removes the '(None)' preset from a list of presets."""
        return [x for x in presets if x["Name"] != NULL_PRESET_NAME]

    def find_matching_preset(self, exif_data: dict) -> str | None:
        """
        Finds a preset that matches the given EXIF data.

        Args:
            exif_data: The EXIF data to match against.

        Returns:
            The name of the matching preset, or None if no match is found.
        """
        for preset in self.presets:
            if preset["Name"] == NULL_PRESET_NAME:
                continue

            is_match = True
            for key, field_widget in self.fields_map.items():
                preset_value = preset.get(key)
                exif_key = f"EXIF:{key}"
                exif_value = exif_data.get(exif_key)

                if preset_value and exif_value and str(preset_value) == str(exif_value):
                    continue
                elif preset_value and not exif_value:
                    is_match = False
                    break
                elif not preset_value and exif_value:
                    # This could be a partial match, which we can decide to handle later
                    pass
            
            if is_match:
                return preset["Name"]
        
        return None
