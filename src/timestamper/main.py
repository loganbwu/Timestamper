# This file is manually maintained. Do not overwrite.
from PySide6.QtCore import Qt, QSettings, QDateTime, QSize
from PySide6.QtGui import QAction, QPixmap, QKeySequence, QResizeEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QFileDialog, QTreeWidgetItem, QListWidgetItem, QMessageBox
from datetime import datetime
from os import path
import logging
from typing import Dict, Tuple, Any

from .constants import (
    NULL_PRESET_NAME,
    FILE_FILTER,
    EXIF_DATE_TIME_ORIGINAL,
    EXIF_EXPOSURE_TIME,
    EXIF_LENS_INFO,
    EXIF_OFFSET_TIME,
    EXIF_OFFSET_TIME_ORIGINAL,
    EXIF_SHUTTER_SPEED
)
from .preset_manager import PresetManager
from .ui_manager import UIManager
from .exif_manager import ExifManager, ExifToolNotFound
from .utils import validate_numeric_input, float_to_shutterspeed, parse_lensinfo
from .settings_dialog import SettingsDialog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for Timestamper."""

    def __init__(self) -> None:
        """Initializes the main window, UI components, and connections."""
        super(MainWindow, self).__init__()

        self.setWindowTitle("Timestamper")
        self.settings = QSettings("Test", "Timestamper")

        # Initialize managers
        self.ui_manager = UIManager(self)
        self._init_exif_manager()

        # Set up menu bar
        self._setup_menu_bar()

        # Create UI components
        self.ui_manager.create_widgets()
        self.ui_manager.setup_layouts()

        # Initialize preset managers
        self._setup_preset_managers()

        self.statusBar().showMessage("Ready")

    def _setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        self.button_loadfiles = QAction("&Open...", self)
        self.button_loadfiles.setShortcut(QKeySequence.StandardKey.Open)
        self.button_loadfiles.setStatusTip("Select image files to modify")
        self.button_loadfiles.triggered.connect(self.onLoadFilesButtonClick)

        action_save = QAction("&Save", self)
        action_save.setShortcut(QKeySequence.StandardKey.Save)
        action_save.triggered.connect(self.save)

        button_clearpresets = QAction("Clear presets", self)
        button_clearpresets.triggered.connect(self.clear_presets)

        action_clear_fields = QAction("Clear Fields", self)
        action_clear_fields.triggered.connect(self.clear_fields)

        action_settings = QAction("Settings...", self)
        action_settings.setShortcut(QKeySequence.StandardKey.Preferences)
        action_settings.triggered.connect(self.open_settings_dialog)

        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.setObjectName("File") # Add this line
        file_menu.addAction(self.button_loadfiles)
        file_menu.addAction(action_save)
        file_menu.addAction(action_clear_fields)
        file_menu.addAction(button_clearpresets)
        file_menu.addSeparator()
        file_menu.addAction(action_settings)

    def _setup_preset_managers(self) -> None:
        """Initialize the preset managers for cameras and lenses."""
        self.camera_fields = {
            "Make": self.make,
            "Model": self.model
        }
        self.camera_preset_manager = PresetManager(
            self.settings, "cameras", self.preset_camera_name, self.camera_fields, self.statusBar().showMessage
        )
        self.preset_camera_name.currentTextChanged.connect(self.camera_preset_manager.load_preset)
        self.preset_camera_add.clicked.connect(lambda: self.camera_preset_manager.add_preset(self.preset_camera_name.currentText()))
        self.preset_camera_remove.clicked.connect(lambda: self.camera_preset_manager.remove_preset(self.preset_camera_name.currentText()))

        self.lens_fields = {
            "LensMake": self.lensmake,
            "LensModel": self.lensmodel,
            "WideFocalLength": self.widefocallength,
            "LongFocalLength": self.longfocallength,
            "WideApertureValue": self.wideaperturevalue,
            "LongApertureValue": self.longaperturevalue,
            "LensSerialNumber": self.lensserialnumber
        }
        self.lens_preset_manager = PresetManager(
            self.settings, "lenses", self.preset_lens_name, self.lens_fields, self.statusBar().showMessage
        )
        self.preset_lens_name.currentTextChanged.connect(self.lens_preset_manager.load_preset)
        self.preset_lens_add.clicked.connect(lambda: self.lens_preset_manager.add_preset(self.preset_lens_name.currentText()))
        self.preset_lens_remove.clicked.connect(lambda: self.lens_preset_manager.remove_preset(self.preset_lens_name.currentText()))
    
    def on_widefocallength_change(self, text: str) -> None:
        """Enables or disables the long focal length field based on input."""
        if text:
            self.longfocallength.setEnabled(True)
        else:
            self.longfocallength.setDisabled(True)
            self.longfocallength.setText("")
            
    def on_wideaperturevalue_change(self, text: str) -> None:
        """Enables or disables the long aperture value field and prefills the f-number."""
        if text:
            self.longaperturevalue.setEnabled(True)
            if not self.fnumber.text() and not self.longaperturevalue.text():
                self.fnumber.setText(text)
        else:
            self.longaperturevalue.setDisabled(True)
            self.longaperturevalue.setText("")
            
    def on_widefocallength_editingfinished(self) -> None:
        """Prefills the focal length field when editing is finished."""
        text = self.widefocallength.text()
        if text and not self.focallength.text() and not self.longfocallength.text():
            self.focallength.setText(text)
            
    def on_wideaperturevalue_editingfinished(self) -> None:
        """Prefills the f-number field when editing is finished."""
        text = self.wideaperturevalue.text()
        if text and not self.fnumber.text() and not self.longaperturevalue.text():
            self.fnumber.setText(text)


    def onLoadFilesButtonClick(self) -> None:
        """Opens a file dialog to select images or a folder and loads them into the file list."""
        logger.info("Loading files...")
        home_dir = path.expanduser("~")
        
        file_dialog = QFileDialog(self, "Select Images or a Folder", home_dir, FILE_FILTER)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        
        if file_dialog.exec():
            selected_paths = file_dialog.selectedFiles()
            selected_files = []
            import os
            for p in selected_paths:
                if os.path.isdir(p):
                    for file in os.listdir(p):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                            selected_files.append(os.path.join(p, file))
                else:
                    if p.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                        selected_files.append(p)
            self.load_files(selected_files)

    def onFilesDropped(self, files: list[str]) -> None:
        """Handles files dropped onto the file list."""
        self.load_files(files)

    def load_files(self, files: list[str]) -> None:
        """Loads a list of files into the file list as thumbnails."""
        if not files:
            return

        self.files_done = []
        self.file_list.clear()
        
        for file_path in sorted(files):
            pixmap = QPixmap(file_path)
            icon = QIcon(pixmap)
            item = QListWidgetItem(icon, path.basename(file_path))
            item.setData(Qt.UserRole, file_path)  # Store full path
            item.setData(Qt.UserRole + 1, False) # Initialize 'done' status to False
            item.setSizeHint(QSize(100, 80))
            self.file_list.addItem(item)

        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
        self.file_list.setFocus()

    def on_file_selection_changed(self) -> None:
        """Handles the selection of a file from the list."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.pic.setText("No picture selected.")
            self.current_path = None
            return

        # Use the first selected item for display purposes
        item = selected_items[0]
        file_path = item.data(Qt.UserRole)
        is_done = self.file_list.row(item) in self.files_done
        
        self.current_path = file_path

        if not self.exif_manager:
            self.open_settings_dialog()
            return

        self._load_exif_data()
        self._update_exif_info_view()
        self._update_image_preview()

        if (self.amend_mode.isChecked() or is_done) and self.current_exif:
            logger.info("Populating form with existing image EXIF")
            self.populate_exif(self.current_exif)

    def _get_clean_path(self, item: QListWidgetItem) -> Tuple[str, bool]:
        """Gets the clean path from a list item and checks if it's marked as done."""
        file_path = item.data(Qt.UserRole)
        is_done = self.file_list.row(item) in self.files_done
        return file_path, is_done

    def _init_exif_manager(self):
        """Initializes the ExifManager with the path from settings."""
        exiftool_path = self.settings.value("exiftool")
        if exiftool_path and path.isfile(exiftool_path):
            try:
                self.exif_manager = ExifManager(exiftool_path)
            except ExifToolNotFound:
                self.exif_manager = None
        else:
            self.exif_manager = None

    def _load_exif_data(self) -> None:
        """Loads EXIF data for the current file."""
        try:
            self.current_exif = self.exif_manager.load_exif_data(self.current_path)
            if self.current_exif:
                message = f'Opened EXIF for "{self.current_path}"'
                logger.info(message)
                self.statusBar().showMessage(message, 3000)
        except ExifToolNotFound:
            self.open_settings_dialog()
            self.current_exif = None
        except Exception as e:
            error_message = f'Error: Exiftool operation failed for "{self.current_path}". {e}'
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            self.current_exif = None

    def _update_exif_info_view(self) -> None:
        """Updates the EXIF info view with the current EXIF data."""
        self.info.clear()
        if not self.current_exif:
            return

        data = {}
        for k, v in sorted(self.current_exif.items()):
            if ":" in k:
                prefix, name = k.split(":")
                if name in ["ShutterSpeedValue", "ExposureTime"]:
                    v = f"{float_to_shutterspeed(v)}s"
                if prefix in data:
                    data[prefix].append([name, v])
                else:
                    data[prefix] = [[name, v]]
        
        if "EXIF" in data:
            data = {"EXIF": data.pop("EXIF"), **data}

        items = []
        for key, tags in data.items():
            item = QTreeWidgetItem([key])
            for tag in tags:
                child = QTreeWidgetItem([tag[0], str(tag[1])])
                item.addChild(child)
            items.append(item)

        self.info.addTopLevelItems(items)
        if items:
            self.info.topLevelItem(0).setExpanded(True)

    def _update_image_preview(self) -> None:
        """Updates the image preview with the current image."""
        try:
            pixmap = QPixmap(self.current_path)
            if pixmap.isNull():
                raise ValueError("Could not load image.")
            self.pic.setPixmap(pixmap.scaled(
                self.pic.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        except Exception as e:
            logger.error(f"Could not load image: {e}")
            self.pic.setText("No picture selected.")
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handles the window resize event to update the image preview."""
        if self.current_path:
            self._update_image_preview()
        super().resizeEvent(event)

    def adjust_datetime(self, d: int, h: int, m: int) -> None:
        """Adjusts the datetime by the given days, hours, and minutes."""
        new_dt = self.datetime.dateTime().addDays(d).addSecs(3600*h+60*m)
        logger.info(f'Setting datetime to {new_dt.toString()}')
        self.datetime.setDateTime(new_dt)

    def adjust_datetime_plus_1d(self):
        self.adjust_datetime(1, 0, 0)

    def adjust_datetime_minus_1d(self):
        self.adjust_datetime(-1, 0, 0)

    def adjust_datetime_plus_1h(self):
        self.adjust_datetime(0, 1, 0)

    def adjust_datetime_minus_1h(self):
        self.adjust_datetime(0, -1, 0)

    def adjust_datetime_plus_10m(self):
        self.adjust_datetime(0, 0, 10)

    def adjust_datetime_minus_10m(self):
        self.adjust_datetime(0, 0, -10)

    def adjust_datetime_plus_1m(self):
        self.adjust_datetime(0, 0, 1)

    def adjust_datetime_minus_1m(self):
        self.adjust_datetime(0, 0, -1)

    def _validate_numeric_input(self, field_name: str, text_value: str) -> bool:
        """Validates that a given text value can be cast to a float."""
        if not validate_numeric_input(field_name, text_value):
            self.statusBar().showMessage(f"Error: Invalid numeric input for {field_name}: '{text_value}'", 5000)
            return False
        return True

    def save(self) -> None:
        """Saves the EXIF data to the selected file(s)."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.statusBar().showMessage("No files selected.", 3000)
            return

        if not self._validate_all_numeric_inputs():
            return

        tags_to_save = self._prepare_exif_tags()
        
        saved_rows = []
        for item in selected_items:
            file_path, _ = self._get_clean_path(item)
            if self._execute_save(file_path, tags_to_save):
                saved_rows.append(self.file_list.row(item))

        if saved_rows:
            self._advance_to_next_file(saved_rows)

    def _validate_all_numeric_inputs(self) -> bool:
        """Validates all numeric input fields."""
        numeric_fields = {
            "ISO": self.iso.text(),
            "ExposureTime": self.exposuretime.text(),
            "FNumber": self.fnumber.text(),
            "FocalLength": self.focallength.text().removesuffix("mm"),
            "WideFocalLength": self.widefocallength.text(),
            "LongFocalLength": self.longfocallength.text(),
            "WideApertureValue": self.wideaperturevalue.text(),
            "LongApertureValue": self.longaperturevalue.text()
        }
        for field_name, value in numeric_fields.items():
            if not self._validate_numeric_input(field_name, value):
                return False
        return True

    def _prepare_exif_tags(self) -> Dict[str, str]:
        """Prepares a dictionary of EXIF tags to be saved."""
        a = self.widefocallength.text()
        b = self.longfocallength.text()
        if a and not b: b = a
        c = self.wideaperturevalue.text()
        d = self.longaperturevalue.text()
        if c and not d: d = c
        lensinfo = f"{a} {b} {c} {d}"
        logger.info(f"LensInfo: {lensinfo}")

        tags = {
            "DateTimeOriginal": self.datetime.dateTime().toString("yyyy:MM:dd HH:mm:00"),
            "OffsetTimeOriginal": self.offsettime.textFromValue(self.offsettime.value()),
            "OffsetTime": self.offsettime.textFromValue(self.offsettime.value()),
            "Make": self.make.text(),
            "Model": self.model.text(),
            "MaxApertureValue": self.wideaperturevalue.text(),
            "ISO": self.iso.text(),
            "LensMake": self.lensmake.text(),
            "LensModel": self.lensmodel.text(),
            "LensInfo": lensinfo,
            "LensSerialNumber": self.lensserialnumber.text(),
            "FocalLength": self.focallength.text().removesuffix("mm"),
            "FNumber": self.fnumber.text(),
            "ExposureTime": self.exposuretime.text(),
            "ShutterSpeedValue": self.exposuretime.text()
        }
        return {k: v for k, v in tags.items() if v}

    def _execute_save(self, file_path: str, tags: Dict[str, str]) -> bool:
        """Executes the save operation using exiftool."""
        if not self.exif_manager:
            self.open_settings_dialog()
            return False
        try:
            if self.exif_manager.save_exif_data(file_path, tags):
                message = f'Saved EXIF to file: {file_path}'
                logger.info(message)
                self.statusBar().showMessage(message, 3000)
                return True
            return False
        except ExifToolNotFound:
            self.open_settings_dialog()
            return False
        except Exception as e:
            error_message = f'Error: Failed to save EXIF to "{file_path}". {e}'
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            return False

    def _advance_to_next_file(self, saved_rows: list[int]) -> None:
        """Advances the selection to the next file in the list that has not been processed."""
        last_saved_row = -1
        for row in saved_rows:
            if row not in self.files_done:
                item = self.file_list.item(row)
                item.setData(Qt.UserRole + 1, True) # Mark item as done
                self.file_list.model().dataChanged.emit(self.file_list.model().index(row, 0), self.file_list.model().index(row, 0), [Qt.UserRole + 1])
                self.files_done.append(row)
            last_saved_row = max(last_saved_row, row)

        n_files = self.file_list.count()
        if len(self.files_done) < n_files:
            start_row = last_saved_row if last_saved_row != -1 else self.file_list.currentRow()
            for i in range(1, n_files):
                next_row = (start_row + i) % n_files
                if next_row not in self.files_done:
                    self.file_list.setCurrentRow(next_row)
                    break
        
        self.file_list.setFocus()
    
    def _populate_fields(self, exif: Dict[str, Any], fields_map: Dict[str, Any]) -> None:
        """Populates a set of fields from EXIF data."""
        for key, widget in fields_map.items():
            exif_key = f"EXIF:{key}"
            if exif_key in exif:
                value = exif[exif_key]
                if isinstance(value, float):
                    value = round(value, 3)
                widget.setText(str(value))

    def populate_exif(self, exif: Dict[str, Any]) -> None:
        """Populates the form fields with data from the provided EXIF dictionary."""
        # First, populate all fields from EXIF
        self._populate_fields(exif, self.camera_preset_manager.fields_map)
        self._populate_fields(exif, self.lens_preset_manager.fields_map)

        shutter_keys = [EXIF_EXPOSURE_TIME, EXIF_SHUTTER_SPEED]
        for k in shutter_keys:
            if k in exif:
                self.exposuretime.setText(float_to_shutterspeed(exif[k]))
                break

        if EXIF_DATE_TIME_ORIGINAL in exif:
            iso_dt = exif[EXIF_DATE_TIME_ORIGINAL].replace(":", "-", 2)
            q_dt = QDateTime.fromString(iso_dt, format=Qt.DateFormat.ISODate)
            self.datetime.setDateTime(q_dt)

        offsettime_keys = [EXIF_OFFSET_TIME_ORIGINAL, EXIF_OFFSET_TIME]
        for k in offsettime_keys:
            if k in exif:
                self.offsettime.setValue(self.offsettime.valueFromText(exif[k]))
                break

        if EXIF_LENS_INFO in exif:
            lensinfo_list = parse_lensinfo(exif[EXIF_LENS_INFO])
            if lensinfo_list and len(lensinfo_list) == 4:
                self.widefocallength.setText(lensinfo_list[0])
                self.longfocallength.setText(lensinfo_list[1])
                self.wideaperturevalue.setText(lensinfo_list[2])
                self.longaperturevalue.setText(lensinfo_list[3])

        # Then, try to match and set presets
        matching_camera = self.camera_preset_manager.find_matching_preset(exif)
        if matching_camera:
            self.preset_camera_name.setCurrentText(matching_camera)
        else:
            self.preset_camera_name.setCurrentText(NULL_PRESET_NAME)

        matching_lens = self.lens_preset_manager.find_matching_preset(exif)
        if matching_lens:
            self.preset_lens_name.setCurrentText(matching_lens)
        else:
            self.preset_lens_name.setCurrentText(NULL_PRESET_NAME)

    def populate_exif_onchange(self, checked: int) -> None:
        """Populates EXIF data when the 'Load EXIF for Editing' checkbox is changed."""
        if checked == 2 and self.current_exif:
            self.populate_exif(self.current_exif)

    def set_executable(self, path: str) -> None:
        """Sets the path to the exiftool executable in the application settings."""
        logger.info(f'Setting exiftool path to {path}')
        self.settings.setValue("exiftool", path)

    def open_settings_dialog(self) -> None:
        """Opens the settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self._init_exif_manager()

    def clear_presets(self) -> None:
        """Clears all saved camera and lens presets."""
        self.settings.remove("preset_cameras")
        self.settings.remove("preset_lenses")
        logger.info("Cleared presets")
        self.camera_preset_manager.refresh_presets()
        self.lens_preset_manager.refresh_presets()

    def clear_fields(self) -> None:
        """Clears all input fields to their default states."""
        for field in [self.make, self.model, self.lensmake, self.lensmodel,
                       self.widefocallength, self.longfocallength,
                       self.wideaperturevalue, self.longaperturevalue,
                       self.lensserialnumber, self.iso, self.exposuretime,
                       self.fnumber, self.focallength]:
            field.clear()
        
        self.datetime.setDateTime(datetime.now())
        self.offsettime.setValue(0.0)
        
        logger.info("Cleared all input fields.")
        self.statusBar().showMessage("All input fields cleared.", 3000)
