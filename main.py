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
from OffsetSpinBox import DoubleOffsetSpinBox

import exiftool

null_preset_name = "(None)"

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Timestamper")

        self.settings = QSettings("Test", "Timestamper")

        button_loadfiles = QAction("&Open...", self)
        button_loadfiles.setShortcut(QKeySequence.StandardKey.Open)

        button_clearpresets = QAction("Clear presets", self)
        button_clearpresets.triggered.connect(self.clear_presets)

        button_loadfiles.setStatusTip("Select image files to modify")
        button_loadfiles.triggered.connect(self.onLoadFilesButtonClick)
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        file_menu.addAction(button_loadfiles)
        file_menu.addAction(button_clearpresets)

        # Define main menu widgets
        self.file_list = QListWidget()
        self.file_list.currentTextChanged.connect(self.select_file_from_list)
        file_list_scroll = QScrollArea()
        file_list_scroll.setWidget(self.file_list)
        file_list_scroll.setWidgetResizable(True)
        self.files_done = [] # remember which files in the list have been done
        self.done_icon = "✓ "

        self.pic = QLabel("Open pictures to begin.")
        self.pic.setMaximumWidth(560)
        self.pic.setMaximumHeight(480)
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
        dt_control_list = [
            ["+1d", "Y", [1, 0, 0]],
            ["-1d", "H", (-1, 0, 0)],
            ["+01:00", "U", (0, 1, 0)],
            ["-01:00", "J", (0, -1, 0)],
            ["+00:10", "I", (0, 0, 10)],
            ["-00:10", "K", (0, 0, -10)],
            ["+00:01", "O", (0, 0, 1)],
            ["-00:01", "L", (0, 0, -1)],
        ]
        dt_buttons = [QPushButton(f"{x[0]} ({x[1]})") for x in dt_control_list]
        for i in range(len(dt_buttons)):
            dt_buttons[i].setShortcut(QKeySequence(dt_control_list[i][1]))
        # Dunno why this doesn't work in a for loop when the rest does
        dt_buttons[0].clicked.connect(lambda: self.adjust_datetime(dt_control_list[0][2]))
        dt_buttons[1].clicked.connect(lambda: self.adjust_datetime(dt_control_list[1][2]))
        dt_buttons[2].clicked.connect(lambda: self.adjust_datetime(dt_control_list[2][2]))
        dt_buttons[3].clicked.connect(lambda: self.adjust_datetime(dt_control_list[3][2]))
        dt_buttons[4].clicked.connect(lambda: self.adjust_datetime(dt_control_list[4][2]))
        dt_buttons[5].clicked.connect(lambda: self.adjust_datetime(dt_control_list[5][2]))
        dt_buttons[6].clicked.connect(lambda: self.adjust_datetime(dt_control_list[6][2]))
        dt_buttons[7].clicked.connect(lambda: self.adjust_datetime(dt_control_list[7][2]))

        button_save = QPushButton("Save")
        button_save.setShortcut(QKeySequence.StandardKey.Save)
        button_save.setAutoDefault(True)
        button_save.clicked.connect(self.save)
        self.amend_mode = QCheckBox("Amend mode")
        self.amend_mode.stateChanged.connect(self.populate_exif_onchange)
        dt_buttons.append(self.amend_mode)
        dt_buttons.append(button_save)

        # Other tags (equipment)
        self.make = QLineEdit()
        self.model = QLineEdit()

        self.lensmake = QLineEdit()
        self.lensmodel = QLineEdit()
        self.focallength = QLineEdit()
        self.maxaperturevalue = QLineEdit()
        self.lensserialnumber = QLineEdit()

        self.iso = QLineEdit()
        self.exposuretime = QLineEdit()
        self.fnumber = QLineEdit()

        # Preset controls
        self.preset_camera_name = QComboBox(editable=True)
        self.preset_camera_name.currentTextChanged.connect(self.load_preset_camera)
        self.refresh_preset_camera()
        self.preset_camera_add = QPushButton("Save camera")
        self.preset_camera_add.clicked.connect(self.add_preset_camera)
        self.preset_camera_remove = QPushButton("Remove camera")
        self.preset_camera_remove.clicked.connect(self.remove_preset_camera)

        self.preset_lens_name = QComboBox(editable=True)
        self.preset_lens_name.currentTextChanged.connect(self.load_preset_lens)
        self.refresh_preset_lens()
        self.preset_lens_add = QPushButton("Save lens")
        self.preset_lens_add.clicked.connect(self.add_preset_lens)
        self.preset_lens_remove = QPushButton("Remove lens")
        self.preset_lens_remove.clicked.connect(self.remove_preset_lens)

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

        # Add datetime adjustment buttons to grid layout
        for i, x in enumerate(dt_buttons):
            layout_buttons.addWidget(x, i % 2, i // 2)

        # Extra settings for equipment
        layout_extra.addWidget(QLabel("Camera make"), 0, 0)
        layout_extra.addWidget(self.make, 0, 1)
        layout_extra.addWidget(QLabel("Camera model"), 1, 0)
        layout_extra.addWidget(self.model, 1, 1)

        layout_extra.addWidget(QLabel("Lens make"), 0, 2)
        layout_extra.addWidget(self.lensmake, 0, 3)
        layout_extra.addWidget(QLabel("Lens model"), 1, 2)
        layout_extra.addWidget(self.lensmodel, 1, 3)
        layout_extra.addWidget(QLabel("Focal length"), 2, 2)
        layout_extra.addWidget(self.focallength, 2, 3)
        layout_extra.addWidget(QLabel("Max aperture"), 3, 2)
        layout_extra.addWidget(self.maxaperturevalue, 3, 3)
        layout_extra.addWidget(QLabel("Lens serial no."), 4, 2)
        layout_extra.addWidget(self.lensserialnumber, 4, 3)

        layout_extra.addWidget(QLabel("ISO"), 0, 4)
        layout_extra.addWidget(self.iso, 0, 5)
        layout_extra.addWidget(QLabel("Exposure time"), 1, 4)
        layout_extra.addWidget(self.exposuretime, 1, 5)
        layout_extra.addWidget(QLabel("Aperture"), 2, 4)
        layout_extra.addWidget(self.fnumber, 2, 5)
        
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


    def onLoadFilesButtonClick(self):
        print("Loading files...")
        file_selection = QFileDialog.getOpenFileNames(self, caption="Select images", filter="Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        self.files_done = [] # Reset markings for complete files
        self.file_list.clear()
        self.file_list.addItems(file_selection[0])
        self.file_list.setCurrentRow(0)
        self.file_list.setFocus()
    
    def select_file_from_list(self, s):
        
        # Remove the 'done' tick from the name if present
        # Files that are 'done' will always have amend_mode used
        if len(s) >= len(self.done_icon) and s[0:2] == self.done_icon:
            self.current_path = s[len(self.done_icon):len(s)]
            is_done = True
        else:
            self.current_path = s
            is_done = False

        if self.current_path == "":
            print("No picture selected.")
            self.pic.setText("No picture selected.")

        elif not path.isfile(self.settings.value("exiftool")):
            print("Could not find exiftool at the current path")

        # Update data view
        else:
            try:
                # "/Users/<USER>/Pictures/Lightroom/Plugins/LensTagger-1.9.2.lrplugin/bin/exiftool"
                with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                    self.current_exif = et.get_metadata(self.current_path)[0]
                    print(f'Opened EXIF for "{self.current_path}"')
            except Exception as e:
                print(f'Could not open EXIF for "{self.current_path}"')
                print(e)
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
                self.pic.setPixmap(QPixmap(self.current_path).scaled(560, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except:
                self.pic.setText("No picture selected.")
    
    def format_as_offset(self, x):
        x = abs(x)
        hours = int(x)
        minutes = int((x % 1) * 60)
        offset = f"{hours:02d}:{minutes:02d}"
        return offset

    def adjust_datetime(self, x):
        d, h, m = x
        new_dt = self.datetime.dateTime().addDays(d).addSecs(3600*h+60*m)
        print(f'Setting datetime to {new_dt.toString()}')
        self.datetime.setDateTime(new_dt)

    def save(self):
        if self.current_exif:
            dt = self.datetime.dateTime().toString("yyyy:MM:dd HH:mm:00")
            tags = {
                    "DateTimeOriginal": dt,
                    "OffsetTimeOriginal": self.offsettime.textFromValue(self.offsettime.value()),
                    "OffsetTime": self.offsettime.textFromValue(self.offsettime.value()),
                    "Make": self.make.text(),
                    "Model": self.model.text(),
                    "MaxApertureValue": self.maxaperturevalue.text(),
                    "ISO": self.iso.text(),
                    "LensMake": self.lensmake.text(),
                    "LensModel": self.lensmodel.text(),
                    "FocalLength": self.focallength.text(),
                    "FNumber": self.fnumber.text(),
                    "ExposureTime": self.exposuretime.text(),
                    "ShutterSpeedValue": self.exposuretime.text(),
                    "LensSerialNumber": self.lensserialnumber.text()
                }
            tags_filtered = {k: v for k, v in tags.items() if v != "" and v != None}
            with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                et.set_tags(self.current_path, tags = tags_filtered)
            print(f'Saved EXIF to file: {tags_filtered}')

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
    
    # Use EXIF to populated userform fields
    def populate_exif(self, exif):
        # Handle simple text fields
        text_fields = {
            "Make": self.make,
            "Model": self.model,
            "MaxApertureValue": self.maxaperturevalue,
            "ISO": self.iso,
            "LensMake": self.lensmake,
            "LensModel": self.lensmodel,
            "FocalLength": self.focallength,
            "FNumber": self.fnumber,
            "LensSerialNumber": self.lensserialnumber
        }
        for k, v in text_fields.items():
            if 'EXIF:' + k in exif.keys():
                value = exif[f"EXIF:{k}"]
                if isinstance(value, float):
                    value = round(value, 3) # remove weird FP digits
                v.setText(str(value))

        # Handle more complicated fields
        shutter_keys = ["EXIF:ExposureTime", "EXIF:ShutterSpeedValue"]
        for k in shutter_keys:
            if k in exif.keys():
                self.exposuretime.setText(self.float_to_shutterspeed(exif[k]))
                break

        if "EXIF:DateTimeOriginal" in exif.keys():
            iso_dt = exif["EXIF:DateTimeOriginal"].replace(":", "-", 2)
            q_dt = QDateTime.fromString(iso_dt, format=Qt.DateFormat.ISODate)
            self.datetime.setDateTime(q_dt)
        
        offsettime_keys = ["EXIF:OffsetTimeOriginal", "EXIF:OffsetTime"]
        for k in offsettime_keys:
            if k in exif.keys():
                self.offsettime.setValue(self.offsettime.valueFromText(exif[k]))
                break

        # Clear preset names. In future could make it try to find a matching preset.
        self.preset_camera_name.setCurrentText(null_preset_name)
        self.preset_lens_name.setCurrentText(null_preset_name)

    def populate_exif_onchange(self, checked):
        if checked == 2 and self.current_exif:
            self.populate_exif(self.current_exif)

    def set_executable(self, path):
        print(f'Setting exiftool path to {path}')
        self.settings.setValue("exiftool", path)

    def load_preset_camera(self, item):
        if self.preset_cameras:
            selected_presets = [x for x in self.preset_cameras if x["Name"] == item]
            if selected_presets:
                preset = selected_presets[0]
                print(preset)
                def get_preset(key):
                    return preset[key] if key in preset.keys() else ""
                self.make.setText(get_preset("Make"))
                self.model.setText(get_preset("Model"))

    def refresh_preset_camera(self):
        existing_presets = self.settings.value("preset_cameras")
        if existing_presets is None:
            existing_presets = []
        self.preset_cameras = [{"Name": null_preset_name}] + existing_presets
        while self.preset_camera_name.count() > 0:
            self.preset_camera_name.removeItem(0)
        if self.preset_cameras:
            self.preset_camera_name.addItems([x["Name"] for x in self.preset_cameras])

    def remove_preset_camera(self):
        to_remove = self.preset_camera_name.currentText()
        if self.preset_cameras:
            self.preset_cameras = [x for x in self.preset_cameras if x["Name"] != to_remove]
        self.settings.setValue("preset_cameras", self.remove_none_preset(self.preset_cameras))
        self.refresh_preset_camera()
    
    def add_preset_camera(self):
        new_camera = {
            "Name": self.preset_camera_name.currentText(),
            "Make": self.make.text(),
            "Model": self.model.text()
        }
        if self.preset_cameras:
            self.preset_cameras = [x for x in self.preset_cameras if x["Name"] != new_camera["Name"]]
            self.preset_cameras = [new_camera] + self.preset_cameras
            self.preset_cameras.sort(key=lambda x: x["Name"]) 
        else:
            self.preset_cameras = [new_camera]

        self.settings.setValue("preset_cameras", self.remove_none_preset(self.preset_cameras))
        current_name = new_camera["Name"]
        self.refresh_preset_camera()
        self.preset_camera_name.setCurrentText(current_name)

    def load_preset_lens(self, item):
        if self.preset_lenses:
            selected_presets = [x for x in self.preset_lenses if x["Name"] == item]
            if selected_presets:
                preset = selected_presets[0]
                def get_preset(key):
                    return preset[key] if key in preset.keys() else ""
                self.lensmake.setText(get_preset("LensMake"))
                self.lensmodel.setText(get_preset("LensModel"))
                self.focallength.setText(get_preset("FocalLength"))
                self.maxaperturevalue.setText(get_preset("MaxApertureValue"))
                self.lensserialnumber.setText(get_preset("LensSerialNumber"))

    # Remove any presets in the list then add from the current saved presets
    def refresh_preset_lens(self):
        existing_presets = self.settings.value("preset_lenses")
        if existing_presets is None:
            existing_presets = []
        self.preset_lenses = [{"Name": null_preset_name}] + existing_presets
        while self.preset_lens_name.count() > 0:
            self.preset_lens_name.removeItem(0)
        if self.preset_lenses:
            self.preset_lens_name.addItems([x["Name"] for x in self.preset_lenses])

    # Remove the currently selected lens preset
    def remove_preset_lens(self):
        to_remove = self.preset_lens_name.currentText()
        if self.preset_lenses:
            self.preset_lenses = [x for x in self.preset_lenses if x["Name"] != to_remove]
        self.settings.setValue("preset_lenses", self.remove_none_preset(self.preset_lenses))
        self.refresh_preset_lens()
    
    # Add a new preset to the list
    def add_preset_lens(self):
        new_lens = {
            "Name": self.preset_lens_name.currentText(),
            "LensMake": self.lensmake.text(),
            "LensModel": self.lensmodel.text(),
            "FocalLength": self.focallength.text(),
            "MaxApertureValue": self.maxaperturevalue.text(),
            "LensSerialNumber": self.lensserialnumber.text()
        }
        print(f'Adding preset {new_lens["Name"]}')
        if self.preset_lenses:
            self.preset_lenses = [x for x in self.preset_lenses if x["Name"] != new_lens["Name"]]
            self.preset_lenses = [new_lens] + self.preset_lenses
            self.preset_lenses.sort(key=lambda x: x["Name"]) 
        else:
            self.preset_lenses = [new_lens]
        self.settings.setValue("preset_lenses", self.remove_none_preset(self.preset_lenses))
        current_name = new_lens["Name"]
        self.refresh_preset_lens()
        self.preset_lens_name.setCurrentText(current_name)

    def clear_presets(self):
        self.settings.remove("preset_cameras")
        self.settings.remove("preset_lenses")
        print("Cleared presets")
        self.refresh_preset_camera()

    # Remove 'none' elements from presets, mostly before saving
    def remove_none_preset(self, presets):
        return [x for x in presets if x["Name"] != null_preset_name]

    def float_to_shutterspeed(self, value):
        if float(value) < 1:
            inv_shutterspeed = 1/float(value)
            return(f"1/{inv_shutterspeed:g}")
        else:
            return(f"{value:g}")
