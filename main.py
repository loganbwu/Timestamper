from PySide6.QtCore import Qt, QSettings, QDateTime
from PySide6.QtGui import QAction, QPixmap, QKeySequence, QShortcut, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QMainWindow,
    QFileDialog,
    QListWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QDateTimeEdit,
    QLineEdit,
    QScrollArea,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter
)
from datetime import datetime
from os import path
import os
import logging

from OffsetSpinBox import DoubleOffsetSpinBox
from constants import (
    IMAGE_PREVIEW_MAX_WIDTH,
    IMAGE_PREVIEW_MAX_HEIGHT,
    NULL_PRESET_NAME,
    DONE_ICON,
    DT_CONTROL_LIST,
    FILE_FILTER,
    EXIF_DATE_TIME_ORIGINAL,
    EXIF_EXPOSURE_TIME,
    EXIF_LENS_INFO,
    EXIF_MAKE,
    EXIF_MODEL,
    EXIF_OFFSET_TIME,
    EXIF_OFFSET_TIME_ORIGINAL,
    EXIF_SHUTTER_SPEED
)
from preset_manager import PresetManager
from drag_drop_list_widget import DragDropListWidget

import exiftool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for Timestamper."""

    def __init__(self):
        """Initializes the main window, UI components, and connections."""
        super(MainWindow, self).__init__()

        self.setWindowTitle("Timestamper")

        self.settings = QSettings("Test", "Timestamper")

        self.button_loadfiles = QAction("&Open...", self)
        self.button_loadfiles.setShortcut(QKeySequence.StandardKey.Open)

        action_save = QAction("&Save", self)
        action_save.setShortcut(QKeySequence.StandardKey.Save)
        action_save.triggered.connect(self.save)

        button_clearpresets = QAction("Clear presets", self)
        button_clearpresets.triggered.connect(self.clear_presets)

        action_clear_fields = QAction("Clear Fields", self)
        action_clear_fields.triggered.connect(self.clear_fields)

        self.button_loadfiles.setStatusTip("Select image files to modify")
        self.button_loadfiles.triggered.connect(self.onLoadFilesButtonClick)
        
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        file_menu.addAction(self.button_loadfiles)
        file_menu.addAction(action_save)
        file_menu.addAction(action_clear_fields)
        file_menu.addAction(button_clearpresets)

        # Define main menu widgets
        self.file_list = DragDropListWidget()
        self.file_list.currentTextChanged.connect(self.select_file_from_list)
        file_list_scroll = QScrollArea()
        file_list_scroll.setWidget(self.file_list)
        file_list_scroll.setWidgetResizable(True)
        self.files_done = [] # remember which files in the list have been done
        self.done_icon = DONE_ICON

        self.pic = QLabel("Open pictures to begin.")
        self.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic.setMaximumWidth(IMAGE_PREVIEW_MAX_WIDTH)
        self.pic.setMaximumHeight(IMAGE_PREVIEW_MAX_HEIGHT)
        self.current_path = None
        self.current_exif = None

        self.info = QTreeWidget()
        self.info.setColumnCount(2)
        self.info.setHeaderLabels(["Name", "Value"])
        info_scroll = QScrollArea()
        info_scroll.setWidget(self.info)
        info_scroll.setWidgetResizable(True)

        self.executable = QLineEdit(self.settings.value("exiftool"))
        self.executable.setPlaceholderText("Path ending in .../bin/exiftool, from exiftool.org.") 
        self.executable.textEdited.connect(self.set_executable)

        self.browse_exiftool_button = QPushButton("Browse")
        self.browse_exiftool_button.clicked.connect(self.browse_exiftool_path)

        self.datetime = QDateTimeEdit()
        self.datetime.setDateTime(datetime.now())

        self.offsettime = DoubleOffsetSpinBox()
        self.offsettime.setSingleStep(0.5)
        self.offsettime.setRange(-12, 14)
        self.offsettime.setPrefix("GMT")
        if self.settings.value("offsettime"):
            self.offsettime.setValue(self.settings.value("offsettime"))
        self.offsettime.valueChanged.connect(lambda value: self.settings.setValue("offsettime", value))
        
        ## Control buttons
        dt_buttons = []
        for text, shortcut_key, adjustment_values in DT_CONTROL_LIST:
            button = QPushButton(f"{text} ({shortcut_key})")
            button.setShortcut(QKeySequence(shortcut_key))
            button.setToolTip(f"Hotkey: {shortcut_key}") # Add tooltip
            button.clicked.connect(lambda values=adjustment_values: self.adjust_datetime(values))
            dt_buttons.append(button)

        button_save = QPushButton("Save")
        button_save.setAutoDefault(True)
        button_save.clicked.connect(self.save)
        self.amend_mode = QCheckBox("Load EXIF for Editing") # Renamed for clarity
        self.amend_mode.setToolTip("When checked, re-selecting a 'ticked' photo or any photo will load its EXIF data into the fields.") # Added tooltip
        self.amend_mode.stateChanged.connect(self.populate_exif_onchange)
        dt_buttons.append(self.amend_mode)
        dt_buttons.append(button_save)

        # Other tags (equipment)
        self.make = QLineEdit()
        self.model = QLineEdit()

        self.lensmake = QLineEdit()
        self.lensmodel = QLineEdit()
        self.widefocallength = QLineEdit()
        self.widefocallength.textChanged.connect(self.on_widefocallength_change)
        self.widefocallength.editingFinished.connect(self.on_widefocallength_editingfinished)
        self.longfocallength = QLineEdit()
        self.longfocallength.setDisabled(True)
        self.wideaperturevalue = QLineEdit()
        self.wideaperturevalue.textChanged.connect(self.on_wideaperturevalue_change)
        self.wideaperturevalue.editingFinished.connect(self.on_wideaperturevalue_editingfinished)
        self.longaperturevalue = QLineEdit()
        self.longaperturevalue.setDisabled(True)
        self.lensserialnumber = QLineEdit()

        self.iso = QLineEdit()
        self.exposuretime = QLineEdit()
        self.fnumber = QLineEdit()
        self.focallength = QLineEdit()

        # Preset controls
        self.preset_camera_name = QComboBox(editable=True)
        self.preset_camera_add = QPushButton("Save camera")
        self.preset_camera_remove = QPushButton("Remove camera")

        self.preset_lens_name = QComboBox(editable=True)
        self.preset_lens_add = QPushButton("Save lens")
        self.preset_lens_remove = QPushButton("Remove lens")

        # Initialize Preset Managers
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

        # Define layouts
        layout_gallery = QHBoxLayout()
        layout_hud = QHBoxLayout()
        layout_executable = QHBoxLayout()
        layout_buttons = QGridLayout()
        layout_extra = QGridLayout()
        layout_preset = QGridLayout()
        layout_main = QVBoxLayout()

        # Main horizontal splitter
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(file_list_scroll)
        h_splitter.addWidget(self.pic)
        h_splitter.addWidget(info_scroll)
        h_splitter.setSizes([200, 400, 200])

        layout_main.addWidget(h_splitter)

        layout_hud.addWidget(self.datetime)
        layout_hud.addWidget(self.offsettime)
        layout_main.addLayout(layout_hud)

        layout_executable.addWidget(QLabel("exiftool"))
        layout_executable.addWidget(self.executable)
        layout_executable.addWidget(self.browse_exiftool_button)
        layout_main.addLayout(layout_executable)

        # Add datetime adjustment buttons to grid layout
        for i, x in enumerate(dt_buttons):
            layout_buttons.addWidget(x, i % 2, i // 2)
        layout_main.addLayout(layout_buttons)

        # Extra settings for equipment
        layout_extra.addWidget(QLabel("Camera"), 0, 0, 1, 2)
        layout_extra.addWidget(QLabel("Camera make"), 1, 0)
        layout_extra.addWidget(self.make, 1, 1)
        layout_extra.addWidget(QLabel("Camera model"), 2, 0)
        layout_extra.addWidget(self.model, 2, 1)

        layout_extra.addWidget(QLabel("Lens"), 0, 2, 1, 2)
        layout_extra.addWidget(QLabel("Lens make"), 1, 2)
        layout_extra.addWidget(self.lensmake, 1, 3)
        layout_extra.addWidget(QLabel("Lens model"), 2, 2)
        layout_extra.addWidget(self.lensmodel, 2, 3)
        layout_extra.addWidget(QLabel("Focal range (mm)"), 3, 2)
        layout_lensinfo_focallength = QGridLayout()
        layout_lensinfo_focallength.addWidget(self.widefocallength, 0, 1)
        layout_lensinfo_focallength.addWidget(self.longfocallength, 0, 2)
        layout_extra.addLayout(layout_lensinfo_focallength, 3, 3)
        layout_extra.addWidget(QLabel("Max aperture (f/)"), 4, 2)
        layout_lensinfo_longaperture = QGridLayout()
        layout_lensinfo_longaperture.addWidget(self.wideaperturevalue, 0, 1)
        layout_lensinfo_longaperture.addWidget(self.longaperturevalue, 0, 2)
        layout_extra.addLayout(layout_lensinfo_longaperture, 4, 3)
        layout_extra.addWidget(QLabel("Lens serial no."), 5, 2)
        layout_extra.addWidget(self.lensserialnumber, 5, 3)

        layout_extra.addWidget(QLabel("Exposure"), 0, 4, 1, 2)
        layout_extra.addWidget(QLabel("ISO"), 1, 4)
        layout_extra.addWidget(self.iso, 1, 5)
        layout_extra.addWidget(QLabel("Exposure time (s)"), 2, 4)
        layout_extra.addWidget(self.exposuretime, 2, 5)
        layout_extra.addWidget(QLabel("Focal length (mm)"), 3, 4)
        layout_extra.addWidget(self.focallength, 3, 5)
        layout_extra.addWidget(QLabel("Aperture (f/)"), 4, 4)
        layout_extra.addWidget(self.fnumber, 4, 5)
        
        # Preset controls
        layout_preset.addWidget(QLabel("Camera preset"), 0, 0, 1, 2)
        layout_preset.addWidget(self.preset_camera_name, 1, 0, 1, 2)
        layout_preset.addWidget(self.preset_camera_add, 2, 0)
        layout_preset.addWidget(self.preset_camera_remove, 2, 1)
        layout_preset.addWidget(QLabel("Lens preset"), 0, 2, 1, 2)
        layout_preset.addWidget(self.preset_lens_name, 1, 2, 1, 2)
        layout_preset.addWidget(self.preset_lens_add, 2, 2)
        layout_preset.addWidget(self.preset_lens_remove, 2, 3)

        layout_main.addLayout(layout_extra)
        layout_main.addLayout(layout_preset)
        
        widget = QWidget()
        widget.setLayout(layout_main)
        self.setCentralWidget(widget)

        self.statusBar().showMessage("Ready")
    
    def on_widefocallength_change(self, text: str):
        """Enables or disables the long focal length field based on input."""
        if text:
            self.longfocallength.setEnabled(True)
        else:
            self.longfocallength.setDisabled(True)
            self.longfocallength.setText("")
            
    def on_wideaperturevalue_change(self, text: str):
        """Enables or disables the long aperture value field and prefills the f-number."""
        if text:
            self.longaperturevalue.setEnabled(True)
            if not self.fnumber.text() and not self.longaperturevalue.text():
                self.fnumber.setText(text)
        else:
            self.longaperturevalue.setDisabled(True)
            self.longaperturevalue.setText("")
            
    def on_widefocallength_editingfinished(self):
        """Prefills the focal length field when editing is finished."""
        text = self.widefocallength.text()
        if text and not self.focallength.text() and not self.longfocallength.text():
            self.focallength.setText(text)
            
    def on_wideaperturevalue_editingfinished(self):
        """Prefills the f-number field when editing is finished."""
        text = self.wideaperturevalue.text()
        if text and not self.fnumber.text() and not self.longaperturevalue.text():
            self.fnumber.setText(text)


    def onLoadFilesButtonClick(self):
        """Opens a file dialog to select images or a folder and loads them into the file list."""
        logger.info("Loading files...")
        home_dir = path.expanduser("~")
        
        file_dialog = QFileDialog(self, "Select Images or a Folder", home_dir, FILE_FILTER)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if not selected_files:
                return

            self.files_done = []
            self.file_list.clear()
            self.file_list.addItems(selected_files)
            self.file_list.sortItems()
            self.file_list.setCurrentRow(0)
            self.file_list.setFocus()
    
    def select_file_from_list(self, s: str):
        """Handles the selection of a file from the list."""
        self.current_path, is_done = self._get_clean_path(s)

        if not self.current_path:
            self.pic.setText("No picture selected.")
            return

        if not self._is_exiftool_available():
            return

        self._load_exif_data()
        self._update_exif_info_view()
        self._update_image_preview()

        if (self.amend_mode.isChecked() or is_done) and self.current_exif:
            logger.info("Populating form with existing image EXIF")
            self.populate_exif(self.current_exif)

    def _get_clean_path(self, s: str) -> tuple[str, bool]:
        """Removes the 'done' icon from the path and returns the clean path and a boolean indicating if it was done."""
        is_done = False
        path_str = s
        if len(s) >= len(self.done_icon) and s.startswith(self.done_icon):
            path_str = s[len(self.done_icon):]
            is_done = True
        return path_str, is_done

    def _is_exiftool_available(self) -> bool:
        """Checks if the exiftool executable is available and configured."""
        exiftool_path = self.settings.value("exiftool")
        if not exiftool_path or not path.isfile(exiftool_path):
            error_message = "Error: Could not find exiftool executable. Please check the path."
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            self.current_exif = None
            return False
        return True

    def _load_exif_data(self):
        """Loads EXIF data for the current file."""
        try:
            with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                self.current_exif = et.get_metadata(self.current_path)[0]
                message = f'Opened EXIF for "{self.current_path}"'
                logger.info(message)
                self.statusBar().showMessage(message, 3000)
        except Exception as e:
            error_message = f'Error: Exiftool operation failed for "{self.current_path}". {e}'
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            self.current_exif = None

    def _update_exif_info_view(self):
        """Updates the EXIF info view with the current EXIF data."""
        self.info.clear()
        if not self.current_exif:
            return

        data = {}
        for k, v in sorted(self.current_exif.items()):
            if ":" in k:
                prefix, name = k.split(":")
                if name in ["ShutterSpeedValue", "ExposureTime"]:
                    v = f"{self.float_to_shutterspeed(v)}s"
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

    def _update_image_preview(self):
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
    
    def resizeEvent(self, event):
        """Handles the window resize event to update the image preview."""
        if self.current_path:
            self._update_image_preview()
        super().resizeEvent(event)

    def format_as_offset(self, x: float) -> str:
        """Formats a float as a timezone offset string."""
        x = abs(x)
        hours = int(x)
        minutes = int((x % 1) * 60)
        offset = f"{hours:02d}:{minutes:02d}"
        return offset

    def adjust_datetime(self, x: tuple[int, int, int]):
        """Adjusts the datetime by the given days, hours, and minutes."""
        d, h, m = x
        new_dt = self.datetime.dateTime().addDays(d).addSecs(3600*h+60*m)
        logger.info(f'Setting datetime to {new_dt.toString()}')
        self.datetime.setDateTime(new_dt)
        
    def parse_lensinfo(self, lensinfo: str) -> list[str] | None:
        """Parses the lens info string into a list of its components."""
        elements = lensinfo.split(" ", 3)
        if len(elements) != 4:
            return None
        def can_be_cast_to_float(x):
            if x is None:
                return False
            try:
                float(x)
                return True
            except ValueError:
                return False
        processed_elements = []
        for x in elements:
            if can_be_cast_to_float(x):
                processed_elements.append(x)
            else:
                return None # If any element is not float-castable, return None for the whole thing
        return processed_elements

    def _validate_numeric_input(self, field_name: str, text_value: str) -> bool:
        """Validates that a given text value can be cast to a float."""
        if text_value == "":
            return True # Empty string is allowed, means no value to write
        try:
            float(text_value)
            return True
        except ValueError:
            error_message = f"Error: Invalid numeric input for {field_name}: '{text_value}'"
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            return False

    def save(self):
        """Saves the EXIF data to the current file."""
        if self.file_list.currentItem() is None or not self.current_exif:
            return

        if not self._validate_all_numeric_inputs():
            return

        tags_to_save = self._prepare_exif_tags()
        self._execute_save(tags_to_save)
        self._advance_to_next_file()

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

    def _prepare_exif_tags(self) -> dict:
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

    def _execute_save(self, tags: dict):
        """Executes the save operation using exiftool."""
        try:
            with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                et.set_tags(self.current_path, tags=tags, params=["-overwrite_original"])
            message = f'Saved EXIF to file: {tags}'
            logger.info(message)
            self.statusBar().showMessage(message, 3000)
        except Exception as e:
            error_message = f'Error: Failed to save EXIF to "{self.current_path}". {e}'
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)

    def _advance_to_next_file(self):
        """Advances the selection to the next file in the list that has not been processed."""
        selected_row = self.file_list.currentRow()
        if selected_row not in self.files_done:
            self.file_list.currentItem().setText(self.done_icon + self.file_list.currentItem().text())
            self.files_done.append(selected_row)

        n_files = self.file_list.count()
        if len(self.files_done) < n_files:
            for i in range(1, n_files):
                next_row = (selected_row + i) % n_files
                if next_row not in self.files_done:
                    self.file_list.setCurrentRow(next_row)
                    break
        
        self.file_list.setFocus()
    
    def _populate_fields(self, exif: dict, fields_map: dict):
        """Populates a set of fields from EXIF data."""
        for key, widget in fields_map.items():
            exif_key = f"EXIF:{key}"
            if exif_key in exif:
                value = exif[exif_key]
                if isinstance(value, float):
                    value = round(value, 3)
                widget.setText(str(value))

    def populate_exif(self, exif: dict):
        """Populates the form fields with data from the provided EXIF dictionary."""
        # First, populate all fields from EXIF
        self._populate_fields(exif, self.camera_preset_manager.fields_map)
        self._populate_fields(exif, self.lens_preset_manager.fields_map)

        shutter_keys = [EXIF_EXPOSURE_TIME, EXIF_SHUTTER_SPEED]
        for k in shutter_keys:
            if k in exif:
                self.exposuretime.setText(self.float_to_shutterspeed(exif[k]))
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
            lensinfo_list = self.parse_lensinfo(exif[EXIF_LENS_INFO])
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

    def populate_exif_onchange(self, checked: int):
        """Populates EXIF data when the 'Load EXIF for Editing' checkbox is changed."""
        if checked == 2 and self.current_exif:
            self.populate_exif(self.current_exif)

    def set_executable(self, path: str):
        """Sets the path to the exiftool executable in the application settings."""
        logger.info(f'Setting exiftool path to {path}')
        self.settings.setValue("exiftool", path)

    def browse_exiftool_path(self):
        """Opens a file dialog to browse for the exiftool executable."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executable Files (*)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.executable.setText(selected_file)
            self.set_executable(selected_file)

    def clear_presets(self):
        """Clears all saved camera and lens presets."""
        self.settings.remove("preset_cameras")
        self.settings.remove("preset_lenses")
        logger.info("Cleared presets")
        self.camera_preset_manager.refresh_presets()
        self.lens_preset_manager.refresh_presets()

    def clear_fields(self):
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

    def float_to_shutterspeed(self, value: float) -> str:
        """Converts a float value to a shutter speed string."""
        if float(value) < 1:
            inv_shutterspeed = 1/float(value)
            return(f"1/{inv_shutterspeed:g}s")
        else:
            return(f"{value:g}s")
