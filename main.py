from PySide6.QtCore import Qt, QSettings, QDateTime
from PySide6.QtGui import QAction, QPixmap, QKeySequence, QShortcut
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
    QDoubleSpinBox,
    QLineEdit,
    QScrollArea,
    QComboBox
)
from datetime import datetime

import exiftool

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
        # self.file_list.addItems(["/Users/wu.l/Desktop/2023-09-08/IMG_" + x + ".jpg" for x in ["0", "3696", "3697-Edit", "3697", "3708"]])
        self.file_list.currentTextChanged.connect(self.select_file_from_list)
        file_list_scroll = QScrollArea()
        file_list_scroll.setWidget(self.file_list)
        file_list_scroll.setWidgetResizable(True)
        
        file_list_down = QShortcut(QKeySequence("key_down"), self)
        file_list_down.activated.connect(lambda inc=1: self.adjust_file(inc))
        file_list_up = QShortcut(QKeySequence("key_down"), self)
        file_list_up.activated.connect(lambda inc=-1: self.adjust_file(inc))

        self.pic = QLabel("Picture")
        self.pic.setMaximumWidth(560)
        self.pic.setMaximumHeight(480)
        self.current_path = None
        self.current_exif = None

        self.info = QLabel("Info")
        info_scroll = QScrollArea()
        info_scroll.setWidget(self.info)
        info_scroll.setWidgetResizable(True)

        self.executable = QLineEdit(self.settings.value("exiftool"))
        self.executable.textEdited.connect(self.set_executable)

        self.datetime = QDateTimeEdit()
        self.datetime.setDateTime(datetime.now())

        self.offsettime = QDoubleSpinBox()
        self.offsettime.setSingleStep(0.5)
        self.offsettime.setPrefix("GMT+")
        if self.settings.value("offsettime"):
            self.offsettime.setValue(self.settings.value("offsettime"))
        self.offsettime.valueChanged.connect(self.save_offsettime)
        
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
        dt_buttons = [QPushButton(x[0] + " (" + x[1] + ")") for x in dt_control_list]
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
        self.preset_camera_add = QPushButton("Save")
        self.preset_camera_add.clicked.connect(self.add_preset_camera)
        self.preset_camera_remove = QPushButton("Remove")
        self.preset_camera_remove.clicked.connect(self.remove_preset_camera)

        self.preset_lens_name = QComboBox(editable=True)
        self.preset_lens_name.currentTextChanged.connect(self.load_preset_lens)
        self.refresh_preset_lens()
        self.preset_lens_add = QPushButton("Save")
        self.preset_lens_add.clicked.connect(self.add_preset_lens)
        self.preset_lens_remove = QPushButton("Remove")
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

        layout_executable.addWidget(QLabel("exiftool path"))
        layout_executable.addWidget(self.executable)

        # Add datetime adjustment buttons to grid layout
        for i, x in enumerate(dt_buttons):
            layout_buttons.addWidget(x, i % 2, i // 2)

        # Extra settings for equipment
        layout_extra.addWidget(QLabel("Make"), 0, 0)
        layout_extra.addWidget(self.make, 0, 1)
        layout_extra.addWidget(QLabel("Model"), 1, 0)
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
        self.file_list.clear()
        self.file_list.addItems(file_selection[0])
        self.file_list.setCurrentRow(0)
        self.file_list.setFocus()
    
    def select_file_from_list(self, s):
        # Update image
        self.current_path = s
        try:
            # "/Users/wu.l/Pictures/Lightroom/Plugins/LensTagger-1.9.2.lrplugin/bin/exiftool"
            print(f'Using {self.settings.value("exiftool")}')
            with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                self.current_exif = et.get_metadata(self.current_path)[0]
                print(f'Opened EXIF for "{self.current_path}"')
        except Exception as e:
            print(f'Could not open EXIF for "{self.current_path}"')
            print(e)
            self.current_exif = None

        self.pic.setPixmap(QPixmap(s).scaled(560, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.info.setText(self.exif_to_text(self.current_exif))
        print
        if self.amend_mode.checkState() == Qt.CheckState.Checked and self.current_exif:
            print("Populating form with existing image EXIF")
            self.populate_exif(self.current_exif)

    def adjust_file(self, inc):
        selected_row = self.file_list.currentRow()
        new_row = selected_row + inc
        n_files = self.file_list.count()
        if new_row >= 0 and new_row < n_files:
            self.file_list.setCurrentRow(new_row)
            self.file_list.setFocus()
    
    def format_as_offset(self, x):
        sign = "+" if x >= 0 else "-"
        x = abs(x)
        hours = int(x)
        minutes = int((x % 1) * 60)
        offset = f"{sign}{hours:02d}:{minutes:02d}"
        return offset

    def adjust_datetime(self, x):
        print(x)
        d, h, m = x
        new_dt = self.datetime.dateTime().addDays(d).addSecs(3600*h+60*m)
        print(f'Setting datetime to {new_dt.toString()}')
        self.datetime.setDateTime(new_dt)

    def save(self):
        if self.current_exif:
            dt = self.datetime.dateTime().toString("yyyy:MM:dd HH:mm:ss")
            offset = self.format_as_offset(self.offsettime.value())
            tags = {
                    "DateTimeOriginal": dt,
                    "OffsetTimeOriginal": offset,
                    "OffsetTime": offset,
                    "Make": self.make.text(),
                    "Model": self.model.text(),
                    "MaxApertureValue": self.maxaperturevalue.text(),
                    "ISO": self.iso.text(),
                    "LensMake": self.lensmake.text(),
                    "LensModel": self.lensmodel.text(),
                    "FocalLength": self.focallength.text(),
                    "FNumber": self.fnumber.text(),
                    "ExposureTime": self.exposuretime.text(),
                    "LensSerialNumber": self.lensserialnumber.text()
                }
            tags_filtered = {k: v for k, v in tags.items() if v != "" and v != None}
            with exiftool.ExifToolHelper(executable=self.settings.value("exiftool")) as et:
                et.set_tags(self.current_path, tags = tags_filtered)
            print(f'Saved EXIF to file.')
            print(tags_filtered)

        # Manage post-save list
        selected_row = self.file_list.currentRow()
        n_files = self.file_list.count()
        if n_files == 1:
            pass
        # If selection was last, select the previous one
        elif selected_row+1 == n_files:
            self.adjust_file(-1)
        else:
            self.adjust_file(+1)
        # Remove selection
        self.file_list.takeItem(selected_row)
    
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
            "ExposureTime": self.exposuretime,
            "LensSerialNumber": self.lensserialnumber
        }
        for k, v in text_fields.items():
            if 'EXIF:' + k in exif.keys():
                value = exif["EXIF:" + k]
                if isinstance(value, float):
                    value = round(value, 3) # remove weird FP digits
                v.setText(str(value))
        # Handle more complicated fields
        if "EXIF:DateTimeOriginal" in exif.keys():
            iso_dt = exif["EXIF:DateTimeOriginal"].replace(":", "-", 2)
            q_dt = QDateTime.fromString(iso_dt, format=Qt.DateFormat.ISODate)
            self.datetime.setDateTime(q_dt)
        if "EXIF:OffsetTimeOriginal" in exif.keys() or "EXIF:OffsetTime" in exif.keys():
            if "EXIF:OffsetTimeOriginal" in exif.keys():
                offset_txt = exif["EXIF:OffsetTimeOriginal"]
            else: 
                offset_txt = exif["EXIF:OffsetTime"]
            offset_sign = 1 if offset_txt[0] == "+" else -1
            offset_hr = int(offset_txt[1:3])
            offset_min = int(offset_txt[4:6])
            self.offsettime.setValue(offset_sign * (offset_hr + offset_min/60))

    def populate_exif_onchange(self, checked):
        if checked == 2 and self.current_exif:
            self.populate_exif(self.current_exif)

    def exif_to_text(self, exif):
        prefixes = []
        if not exif:
            return "No EXIF data"
        res = ""
        for k, v in exif.items():
            if ":" in k:
                prefix = k.split(":")[0]
                if prefix != "EXIF":
                    if prefix not in prefixes:
                        prefixes += [prefix]
                else:
                    name = k.split(":")[1]
                    res += name + ": " + str(v) + "\n"
        for prefix in prefixes:
            res += prefix + ": [truncated]\n"

        return res

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
        self.preset_cameras = self.settings.value("preset_cameras")
        while self.preset_camera_name.count() > 0:
            self.preset_camera_name.removeItem(0)
        if self.preset_cameras:
            self.preset_camera_name.addItems([x["Name"] for x in self.preset_cameras])

    def remove_preset_camera(self):
        to_remove = self.preset_camera_name.currentText()
        if self.preset_cameras:
            self.preset_cameras = [x for x in self.preset_cameras if x["Name"] != to_remove]
        self.settings.setValue("preset_cameras", self.preset_cameras)
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
        else:
            self.preset_cameras = [new_camera]
        self.settings.setValue("preset_cameras", self.preset_cameras)
        self.refresh_preset_camera()

    def load_preset_lens(self, item):
        if self.preset_lenses:
            selected_presets = [x for x in self.preset_lenses if x["Name"] == item]
            if selected_presets:
                preset = selected_presets[0]
                print(preset)
                def get_preset(key):
                    return preset[key] if key in preset.keys() else ""
                self.lensmake.setText(get_preset("LensMake"))
                self.lensmodel.setText(get_preset("LensModel"))
                self.focallength.setText(get_preset("FocalLength"))
                self.maxaperturevalue.setText(get_preset("MaxApertureValue"))
                self.lensserialnumber.setText(get_preset("LensSerialNumber"))

    def refresh_preset_lens(self):
        self.preset_lenses = self.settings.value("preset_lenses")
        while self.preset_lens_name.count() > 0:
            self.preset_lens_name.removeItem(0)
        if self.preset_lenses:
            self.preset_lens_name.addItems([x["Name"] for x in self.preset_lenses])

    def remove_preset_lens(self):
        to_remove = self.preset_lens_name.currentText()
        if self.preset_lenses:
            self.preset_lenses = [x for x in self.preset_lenses if x["Name"] != to_remove]
        self.settings.setValue("preset_lenses", self.preset_lenses)
        self.refresh_preset_lens()
    
    def add_preset_lens(self):
        new_lens= {
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
        else:
            self.preset_lenses = [new_lens]
        self.settings.setValue("preset_lenses", self.preset_lenses)
        self.refresh_preset_lens()

    def clear_presets(self):
        self.settings.remove("preset_cameras")
        self.settings.remove("preset_lenses")
        print("Cleared presets")
        self.refresh_preset_camera()

    def save_offsettime(self, value):
        self.settings.setValue("offsettime", value)