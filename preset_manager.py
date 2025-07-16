from PySide6.QtCore import QSettings
from constants import NULL_PRESET_NAME
import logging

logger = logging.getLogger(__name__)

class PresetManager:
    def __init__(self, settings: QSettings, preset_type: str, combo_box, fields_map: dict, status_bar_callback):
        self.settings = settings
        self.preset_type = preset_type # e.g., "cameras" or "lenses"
        self.combo_box = combo_box
        self.fields_map = fields_map # maps preset keys to QLineEdit widgets
        self.status_bar_callback = status_bar_callback # Callback function to update the status bar

        self.presets = []
        self.refresh_presets()

    def refresh_presets(self):
        existing_presets = self.settings.value(f"preset_{self.preset_type}")
        if existing_presets is None:
            existing_presets = []
        self.presets = [{"Name": NULL_PRESET_NAME}] + existing_presets
        while self.combo_box.count() > 0:
            self.combo_box.removeItem(0)
        if self.presets:
            self.combo_box.addItems([x["Name"] for x in self.presets])

    def load_preset(self, item: str):
        if self.presets:
            selected_presets = [x for x in self.presets if x["Name"] == item]
            if selected_presets:
                preset = selected_presets[0]
                for key, widget in self.fields_map.items():
                    value = preset.get(key, "")
                    if widget: # Check if widget exists (e.g., for disabled fields)
                        widget.setText(str(value))

    def add_preset(self, name: str):
        new_preset = {"Name": name}
        for key, widget in self.fields_map.items():
            if widget:
                new_preset[key] = widget.text()

        if self.presets:
            self.presets = [x for x in self.presets if x["Name"] != new_preset["Name"]]
            self.presets = [new_preset] + self.presets
            self.presets.sort(key=lambda x: x["Name"])
        else:
            self.presets = [new_preset]

        self.settings.setValue(f"preset_{self.preset_type}", self._remove_none_preset(self.presets))
        current_name = new_preset["Name"]
        self.refresh_presets()
        message = f"Added preset '{current_name}' for {self.preset_type}."
        logger.info(message)
        self.status_bar_callback(message, 3000)

    def remove_preset(self, name: str):
        if self.presets:
            self.presets = [x for x in self.presets if x["Name"] != name]
        self.settings.setValue(f"preset_{self.preset_type}", self._remove_none_preset(self.presets))
        self.refresh_presets()
        message = f"Removed preset '{name}' for {self.preset_type}."
        logger.info(message)
        self.status_bar_callback(message, 3000)

    def _remove_none_preset(self, presets):
        return [x for x in presets if x["Name"] != NULL_PRESET_NAME]
