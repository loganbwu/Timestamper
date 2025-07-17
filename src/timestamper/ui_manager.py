"""UI management for the Timestamper application."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QDateTimeEdit,
    QLineEdit,
    QScrollArea,
    QComboBox,
    QTreeWidget,
    QSplitter,
    QListWidget,
    QStyle,
)
from datetime import datetime

from .constants import (
    IMAGE_PREVIEW_MAX_WIDTH,
    IMAGE_PREVIEW_MAX_HEIGHT,
    DONE_ICON,
    DT_CONTROL_LIST
)
from .OffsetSpinBox import DoubleOffsetSpinBox
from .drag_drop_list_widget import DragDropListWidget
from .thumbnail_delegate import ThumbnailDelegate


class UIManager:
    """Manages the creation and layout of UI components."""

    def __init__(self, main_window: "MainWindow"):
        """Initialize the UI manager with a reference to the main window."""
        self.main_window = main_window
        self.settings = main_window.settings
    
    def create_widgets(self):
        """Create all UI widgets and store them as attributes of the main window."""
        self._create_file_widgets()
        self._create_image_widgets()
        self._create_info_widgets()
        self._create_datetime_widgets()
        self._create_control_buttons()
        self._create_equipment_widgets()
        self._create_exposure_widgets()
        self._create_preset_widgets()
    
    def _create_file_widgets(self):
        """Create file list and related widgets."""
        self.main_window.file_list = DragDropListWidget()
        self.main_window.file_list.setViewMode(QListWidget.IconMode)
        self.main_window.file_list.setResizeMode(QListWidget.Adjust)
        self.main_window.file_list.setSpacing(2)
        self.main_window.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.main_window.file_list.itemSelectionChanged.connect(self.main_window.on_file_selection_changed)
        self.main_window.file_list.filesDropped.connect(self.main_window.onFilesDropped)
        self.main_window.file_list.setItemDelegate(ThumbnailDelegate(self.main_window.file_list))
        
        file_list_scroll = QScrollArea()
        file_list_scroll.setWidget(self.main_window.file_list)
        file_list_scroll.setWidgetResizable(True)
        self.main_window.file_list_scroll = file_list_scroll
        
        self.main_window.files_done = []
        self.main_window.done_icon = DONE_ICON
    
    def _create_image_widgets(self):
        """Create image preview widgets."""
        self.main_window.pic = QLabel("Open pictures to begin.")
        self.main_window.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.pic.setMaximumWidth(IMAGE_PREVIEW_MAX_WIDTH)
        self.main_window.pic.setMaximumHeight(IMAGE_PREVIEW_MAX_HEIGHT)
        self.main_window.current_path = None
        self.main_window.current_exif = None
    
    def _create_info_widgets(self):
        """Create EXIF info display widgets."""
        self.main_window.info = QTreeWidget()
        self.main_window.info.setColumnCount(2)
        self.main_window.info.setHeaderLabels(["Name", "Value"])
        
        info_scroll = QScrollArea()
        info_scroll.setWidget(self.main_window.info)
        info_scroll.setWidgetResizable(True)
        self.main_window.info_scroll = info_scroll
    
    def _create_datetime_widgets(self):
        """Create datetime and offset widgets."""
        self.main_window.datetime = QDateTimeEdit()
        self.main_window.datetime.setDateTime(datetime.now())
        
        self.main_window.offsettime = DoubleOffsetSpinBox()
        self.main_window.offsettime.setSingleStep(0.5)
        self.main_window.offsettime.setRange(-12, 14)
        self.main_window.offsettime.setPrefix("GMT")
        if self.settings.value("offsettime"):
            self.main_window.offsettime.setValue(self.settings.value("offsettime"))
        self.main_window.offsettime.valueChanged.connect(
            lambda value: self.settings.setValue("offsettime", value)
        )
    
    def _create_control_buttons(self):
        """Create datetime control buttons and save/amend controls."""
        dt_buttons = []
        for text, shortcut_key, adjustment_values in DT_CONTROL_LIST:
            button = QPushButton(f"{text} ({shortcut_key})")
            button.setShortcut(shortcut_key)
            button.setToolTip(f"Hotkey: {shortcut_key}")
            # Connect to a specific slot in main_window that handles the adjustment
            # We'll create a new method in main.py to handle this
            if text == "+1d":
                button.clicked.connect(self.main_window.adjust_datetime_plus_1d)
            elif text == "-1d":
                button.clicked.connect(self.main_window.adjust_datetime_minus_1d)
            elif text == "+01:00":
                button.clicked.connect(self.main_window.adjust_datetime_plus_1h)
            elif text == "-01:00":
                button.clicked.connect(self.main_window.adjust_datetime_minus_1h)
            elif text == "+00:10":
                button.clicked.connect(self.main_window.adjust_datetime_plus_10m)
            elif text == "-00:10":
                button.clicked.connect(self.main_window.adjust_datetime_minus_10m)
            elif text == "+00:01":
                button.clicked.connect(self.main_window.adjust_datetime_plus_1m)
            elif text == "-00:01":
                button.clicked.connect(self.main_window.adjust_datetime_minus_1m)
            dt_buttons.append(button)
        
        button_save = QPushButton("Save")
        button_save.setAutoDefault(True)
        button_save.clicked.connect(self.main_window.save)
        
        self.main_window.amend_mode = QCheckBox("Load EXIF for Editing")
        self.main_window.amend_mode.setToolTip(
            "When checked, re-selecting a 'ticked' photo or any photo will load its EXIF data into the fields."
        )
        self.main_window.amend_mode.stateChanged.connect(self.main_window.populate_exif_onchange)
        
        dt_buttons.append(self.main_window.amend_mode)
        dt_buttons.append(button_save)
        self.main_window.dt_buttons = dt_buttons

        self.main_window.settings_button = QPushButton()
        style = self.main_window.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.main_window.settings_button.setIcon(icon)
        self.main_window.settings_button.setToolTip("Settings")
        self.main_window.settings_button.clicked.connect(self.main_window.open_settings_dialog)
    
    def _create_equipment_widgets(self):
        """Create camera and lens equipment widgets."""
        # Camera widgets
        self.main_window.make = QLineEdit()
        self.main_window.model = QLineEdit()
        
        # Lens widgets
        self.main_window.lensmake = QLineEdit()
        self.main_window.lensmodel = QLineEdit()
        self.main_window.widefocallength = QLineEdit()
        self.main_window.widefocallength.textChanged.connect(self.main_window.on_widefocallength_change)
        self.main_window.widefocallength.editingFinished.connect(self.main_window.on_widefocallength_editingfinished)
        self.main_window.longfocallength = QLineEdit()
        self.main_window.longfocallength.setDisabled(True)
        self.main_window.wideaperturevalue = QLineEdit()
        self.main_window.wideaperturevalue.textChanged.connect(self.main_window.on_wideaperturevalue_change)
        self.main_window.wideaperturevalue.editingFinished.connect(self.main_window.on_wideaperturevalue_editingfinished)
        self.main_window.longaperturevalue = QLineEdit()
        self.main_window.longaperturevalue.setDisabled(True)
        self.main_window.lensserialnumber = QLineEdit()
    
    def _create_exposure_widgets(self):
        """Create exposure setting widgets."""
        self.main_window.iso = QLineEdit()
        self.main_window.exposuretime = QLineEdit()
        self.main_window.fnumber = QLineEdit()
        self.main_window.focallength = QLineEdit()
    
    def _create_preset_widgets(self):
        """Create preset management widgets."""
        # Camera preset widgets
        self.main_window.preset_camera_name = QComboBox(editable=True)
        self.main_window.preset_camera_add = QPushButton("Save camera")
        self.main_window.preset_camera_remove = QPushButton("Remove camera")
        
        # Lens preset widgets
        self.main_window.preset_lens_name = QComboBox(editable=True)
        self.main_window.preset_lens_add = QPushButton("Save lens")
        self.main_window.preset_lens_remove = QPushButton("Remove lens")

    
    def setup_layouts(self):
        """Set up all layouts and add widgets to the main window."""
        # Main horizontal splitter
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.addWidget(self.main_window.file_list_scroll)
        h_splitter.addWidget(self.main_window.pic)
        h_splitter.addWidget(self.main_window.info_scroll)
        h_splitter.setSizes([200, 400, 200])
        
        # Main layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(h_splitter, 1)
        
        # HUD layout (datetime controls)
        layout_hud = QHBoxLayout()
        layout_hud.addWidget(self.main_window.datetime, 1)
        layout_hud.addWidget(self.main_window.offsettime)
        layout_hud.addWidget(self.main_window.settings_button)
        layout_main.addLayout(layout_hud)
        
        # Control buttons layout
        layout_buttons = QGridLayout()
        for i, button in enumerate(self.main_window.dt_buttons):
            layout_buttons.addWidget(button, i % 2, i // 2)
        layout_main.addLayout(layout_buttons)
        
        # Equipment layout
        layout_extra = self._create_equipment_layout()
        layout_main.addLayout(layout_extra)
        
        # Preset layout
        layout_preset = self._create_preset_layout()
        layout_main.addLayout(layout_preset)
        
        # Set central widget
        widget = QWidget()
        widget.setLayout(layout_main)
        self.main_window.setCentralWidget(widget)
    
    def _create_equipment_layout(self) -> QGridLayout:
        """Create the equipment settings layout."""
        layout_extra = QGridLayout()

        # Camera section
        layout_extra.addWidget(QLabel("Camera"), 0, 0, 1, 2)
        layout_extra.addWidget(QLabel("Camera make"), 1, 0)
        layout_extra.addWidget(self.main_window.make, 1, 1)
        layout_extra.addWidget(QLabel("Camera model"), 2, 0)
        layout_extra.addWidget(self.main_window.model, 2, 1)
        
        # Lens section
        layout_extra.addWidget(QLabel("Lens"), 0, 2, 1, 2)
        layout_extra.addWidget(QLabel("Lens make"), 1, 2)
        layout_extra.addWidget(self.main_window.lensmake, 1, 3)
        layout_extra.addWidget(QLabel("Lens model"), 2, 2)
        layout_extra.addWidget(self.main_window.lensmodel, 2, 3)
        layout_extra.addWidget(QLabel("Focal range (mm)"), 3, 2)
        
        layout_lensinfo_focallength = QGridLayout()
        layout_lensinfo_focallength.addWidget(self.main_window.widefocallength, 0, 1)
        layout_lensinfo_focallength.addWidget(self.main_window.longfocallength, 0, 2)
        layout_extra.addLayout(layout_lensinfo_focallength, 3, 3)
        
        layout_extra.addWidget(QLabel("Max aperture (f/)"), 4, 2)
        layout_lensinfo_longaperture = QGridLayout()
        layout_lensinfo_longaperture.addWidget(self.main_window.wideaperturevalue, 0, 1)
        layout_lensinfo_longaperture.addWidget(self.main_window.longaperturevalue, 0, 2)
        layout_extra.addLayout(layout_lensinfo_longaperture, 4, 3)
        
        layout_extra.addWidget(QLabel("Lens serial no."), 5, 2)
        layout_extra.addWidget(self.main_window.lensserialnumber, 5, 3)
        
        # Exposure section
        layout_extra.addWidget(QLabel("Exposure"), 0, 4, 1, 2)
        layout_extra.addWidget(QLabel("ISO"), 1, 4)
        layout_extra.addWidget(self.main_window.iso, 1, 5)
        layout_extra.addWidget(QLabel("Exposure time (s)"), 2, 4)
        layout_extra.addWidget(self.main_window.exposuretime, 2, 5)
        layout_extra.addWidget(QLabel("Focal length (mm)"), 3, 4)
        layout_extra.addWidget(self.main_window.focallength, 3, 5)
        layout_extra.addWidget(QLabel("Aperture (f/)"), 4, 4)
        layout_extra.addWidget(self.main_window.fnumber, 4, 5)
        
        return layout_extra
    
    def _create_preset_layout(self) -> QGridLayout:
        """Create the preset controls layout."""
        layout_preset = QGridLayout()

        # Camera preset controls
        layout_preset.addWidget(QLabel("Camera preset"), 0, 0, 1, 2)
        layout_preset.addWidget(self.main_window.preset_camera_name, 1, 0, 1, 2)
        layout_preset.addWidget(self.main_window.preset_camera_add, 2, 0)
        layout_preset.addWidget(self.main_window.preset_camera_remove, 2, 1)
        
        # Lens preset controls
        layout_preset.addWidget(QLabel("Lens preset"), 0, 2, 1, 2)
        layout_preset.addWidget(self.main_window.preset_lens_name, 1, 2, 1, 2)
        layout_preset.addWidget(self.main_window.preset_lens_add, 2, 2)
        layout_preset.addWidget(self.main_window.preset_lens_remove, 2, 3)

        
        return layout_preset
