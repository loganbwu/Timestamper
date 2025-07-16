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
    QTreeWidgetItem
)
from datetime import datetime
from os import path
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

import exiftool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self):
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
        self.file_list = QListWidget()
        self.file_list.currentTextChanged.connect(self.select_file_from_list)
        file_list_scroll = QScrollArea()
        file_list_scroll.setWidget(self.file_list)
        file_list_scroll.setWidgetResizable(True)
        self.files_done = [] # remember which files in the list have been done
        self.done_icon = DONE_ICON

        self.pic = QLabel("Open pictures to begin.")
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
        # self.wideaperturevalue.editingFinished.connect(self.on_wideaperturevalue_editingfinished)
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

        layout_gallery.addWidget(file_list_scroll)
        layout_gallery.addWidget(self.pic)
        layout_gallery.addWidget(info_scroll)

        layout_hud.addWidget(self.datetime)
        layout_hud.addWidget(self.offsettime)

        layout_executable.addWidget(QLabel("exiftool"))
        layout_executable.addWidget(self.executable)
        layout_executable.addWidget(self.browse_exiftool_button)

        # Add datetime adjustment buttons to grid layout
        for i, x in enumerate(dt_buttons):
            layout_buttons.addWidget(x, i % 2, i // 2)

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

        layout_main.addLayout(layout_gallery)
        layout_main.addLayout(layout_hud)
        layout_main.addLayout(layout_executable)
        layout_main.addLayout(layout_buttons)
        layout_main.addLayout(layout_extra)
        layout_main.addLayout(layout_preset)
        
        widget = QWidget()
        widget.setLayout(layout_main)
        self.setCentralWidget(widget)

        self.statusBar().showMessage("Ready")
    
    def on_widefocallength_change(self, text):
        if text:
            self.longfocallength.setEnabled(True)
        else:
            self.longfocallength.setDisabled(True)
            self.longfocallength.setText("")
            
    def on_wideaperturevalue_change(self, text):
        if text:
            self.longaperturevalue.setEnabled(True)
            if not self.fnumber.text() and not self.longaperturevalue.text():
                self.fnumber.setText(text)
        else:
            self.longaperturevalue.setDisabled(True)
            self.longaperturevalue.setText("")
            
    def on_widefocallength_editingfinished(self):
        text = self.widefocallength.text()
        if text and not self.focallength.text() and not self.longfocallength.text():
            self.focallength.setText(text)
            
    def on_wideaperturevalue_editingfinished(self):
        text = self.wideaperturevalue.text()
        if text and not self.fnumber.text() and not self.longaperturevalue.text():
            self.fnumber.setText(text)


    def onLoadFilesButtonClick(self):
        logger.info("Loading files...")
        file_selection = QFileDialog.getOpenFileNames(self, caption="Select images", filter=FILE_FILTER)
        self.files_done = [] # Reset markings for complete files
        self.file_list.clear()
        self.file_list.addItems(file_selection[0])
        self.file_list.sortItems()
        self.file_list.setCurrentRow(0)
        self.file_list.setFocus()
    
    def select_file_from_list(self, s):
        
        # Remove the 'done' tick from the name if present
        # Files that are 'done' will always have amend_mode used
        is_done = False
        self.current_path = s
        if len(s) >= len(self.done_icon) and s[0:2] == self.done_icon:
            self.current_path = s[len(self.done_icon):len(s)]
            is_done = True

        if self.current_path == "":
            logger.info("No picture selected.")
            self.pic.setText("No picture selected.")

        elif not path.isfile(self.settings.value("exiftool")):
            error_message = "Error: Could not find exiftool executable. Please check the path."
            logger.error(error_message)
            self.statusBar().showMessage(error_message, 5000)
            self.current_exif = None # Ensure current_exif is None if exiftool is not found

        # Update data view
        else:
            try:
                with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                    self.current_exif = et.get_metadata(self.current_path)[0]
                    message = f'Opened EXIF for "{self.current_path}"'
                    logger.info(message)
                    self.statusBar().showMessage(message, 3000)
            except Exception as e: # Catch generic Exception for now
                error_message = f'Error: Exiftool operation failed for "{self.current_path}". {e}'
                logger.error(error_message)
                self.statusBar().showMessage(error_message, 5000)
                self.current_exif = None
            finally:
                # Set metadata
                self.info.clear()
                data = {}
                if self.current_exif is not None:
                    for k, v in sorted(self.current_exif.items()):
                        if ":" in k:
                            prefix, name = k.split(":")
                            if name in ["ShutterSpeedValue", "ExposureTime"]:
                                v = f"{self.float_to_shutterspeed(v)}s"
                            if prefix in data.keys():
                                data[prefix].append([name, v])
                            else:
                                data[prefix] = [[name, v]]
                    # EXIF is always first
                    if "EXIF" in data.keys():
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
                
                    if (self.amend_mode.checkState() == Qt.CheckState.Checked or is_done) and self.current_exif:
                        print("Populating form with existing image EXIF")
                        self.populate_exif(self.current_exif)

            # Update image
            try:
                self.pic.setPixmap(QPixmap(self.current_path).scaled(IMAGE_PREVIEW_MAX_WIDTH, IMAGE_PREVIEW_MAX_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except Exception as e:
                logger.error(f"Could not load image: {e}")
                self.pic.setText("No picture selected.")
    
    def resizeEvent(self, event):
        # Override resizeEvent to update image preview when window resizes
        if self.current_path:
            try:
                self.pic.setPixmap(QPixmap(self.current_path).scaled(
                    self.pic.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            except Exception as e:
                logger.error(f"Error resizing image: {e}")
        super().resizeEvent(event)

    def format_as_offset(self, x):
        x = abs(x)
        hours = int(x)
        minutes = int((x % 1) * 60)
        offset = f"{hours:02d}:{minutes:02d}"
        return offset

    def adjust_datetime(self, x):
        d, h, m = x
        new_dt = self.datetime.dateTime().addDays(d).addSecs(3600*h+60*m)
        logger.info(f'Setting datetime to {new_dt.toString()}')
        self.datetime.setDateTime(new_dt)
        
    def parse_lensinfo(self, lensinfo):
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

    def _validate_numeric_input(self, field_name, text_value):
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
        if self.file_list.currentItem() is None:
            return

        # Validate numeric inputs
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
                return # Stop saving if any validation fails

        # Process LensInfo
        a = self.widefocallength.text()
        b = self.longfocallength.text()
        if a and not b:
            b = a
        c = self.wideaperturevalue.text()
        d = self.longaperturevalue.text()
        if c and not d:
            d = c
        lensinfo = f"{a} {b} {c} {d}"
        logger.info(f"LensInfo: {lensinfo}")
        
        if self.current_exif:
            dt = self.datetime.dateTime().toString("yyyy:MM:dd HH:mm:00")
            tags = {
                    "DateTimeOriginal": dt,
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
            tags_filtered = {k: v for k, v in tags.items() if v != "" and v != None}
            try:
                with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                    et.set_tags(self.current_path, tags = tags_filtered, params=["-overwrite_original"])
                message = f'Saved EXIF to file: {tags_filtered}'
                logger.info(message)
                self.statusBar().showMessage(message, 3000)
            except Exception as e: # Catch generic Exception for now
                error_message = f'Error: Failed to save EXIF to "{self.current_path}". {e}'
                logger.error(error_message)
                self.statusBar().showMessage(error_message, 5000)

        # Manage post-save list
        selected_row = self.file_list.currentRow()
        if selected_row not in self.files_done:
            self.file_list.currentItem().setText(self.done_icon + self.file_list.currentItem().text())
            self.files_done.append(selected_row) # Mark as done
        n_files = self.file_list.count()
        prev_row = selected_row - 1
        next_row = selected_row + 1
        prev_is_todo = prev_row >= 0 and prev_row not in self.files_done
        next_is_todo = next_row < n_files and next_row not in self.files_done
        if next_is_todo:
            self.file_list.setCurrentRow(next_row)
        elif prev_is_todo:
            self.file_list.setCurrentRow(prev_row)
        elif next_row < n_files:
            self.file_list.setCurrentRow(next_row)

        # Set focus to the file list
        self.file_list.setFocus()
    
    def _populate_fields(self, exif, fields_map):
        for key, widget in fields_map.items():
            exif_key = f"EXIF:{key}"
            if exif_key in exif:
                value = exif[exif_key]
                if isinstance(value, float):
                    value = round(value, 3)
                widget.setText(str(value))

    # Use EXIF to populated userform fields
    def populate_exif(self, exif):
        # Clear preset names. In future could make it try to find a matching preset.
        self.preset_camera_name.setCurrentText(NULL_PRESET_NAME)
        self.preset_lens_name.setCurrentText(NULL_PRESET_NAME)

        # Handle simple text fields
        self._populate_fields(exif, self.camera_preset_manager.fields_map)
        self._populate_fields(exif, self.lens_preset_manager.fields_map)

        # Handle more complicated fields
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
            if lensinfo_list and len(lensinfo_list) == 4: # Ensure lensinfo_list is not None and has 4 elements
                if lensinfo_list[0]:
                    self.widefocallength.setText(lensinfo_list[0])
                if lensinfo_list[1]:
                    self.longfocallength.setText(lensinfo_list[1])
                if lensinfo_list[2]:
                    self.wideaperturevalue.setText(lensinfo_list[2])
                if lensinfo_list[3]:
                    self.longaperturevalue.setText(lensinfo_list[3])

    def populate_exif_onchange(self, checked):
        if checked == 2 and self.current_exif:
            self.populate_exif(self.current_exif)

    def set_executable(self, path):
        logger.info(f'Setting exiftool path to {path}')
        self.settings.setValue("exiftool", path)

    def browse_exiftool_path(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executable Files (*)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.executable.setText(selected_file)
            self.set_executable(selected_file)

    def clear_presets(self):
        self.settings.remove("preset_cameras")
        self.settings.remove("preset_lenses")
        logger.info("Cleared presets")
        self.camera_preset_manager.refresh_presets()
        self.lens_preset_manager.refresh_presets()

    def clear_fields(self):
        # Clear QLineEdit fields
        for field in [self.make, self.model, self.lensmake, self.lensmodel,
                       self.widefocallength, self.longfocallength,
                       self.wideaperturevalue, self.longaperturevalue,
                       self.lensserialnumber, self.iso, self.exposuretime,
                       self.fnumber, self.focallength]:
            field.clear()
        
        # Reset QDateTimeEdit to current time
        self.datetime.setDateTime(datetime.now())
        
        # Reset OffsetSpinBox to default (0.0)
        self.offsettime.setValue(0.0)
        
        logger.info("Cleared all input fields.")
        self.statusBar().showMessage("All input fields cleared.", 3000)

    def float_to_shutterspeed(self, value):
        if float(value) < 1:
            inv_shutterspeed = 1/float(value)
            return(f"1/{inv_shutterspeed:g}s")
        else:
            return(f"{value:g}s")
