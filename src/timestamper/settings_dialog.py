from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel
from PySide6.QtCore import QSettings

class SettingsDialog(QDialog):
    """A dialog for configuring application settings."""

    def __init__(self, parent=None):
        """Initializes the SettingsDialog."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("Test", "Timestamper")

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self._create_exiftool_widgets()

    def _create_exiftool_widgets(self):
        """Creates widgets for configuring the exiftool path."""
        # Add a descriptive label if the exiftool path is not set
        if not self.settings.value("exiftool"):
            info_label = QLabel(
                "<b>exiftool</b> not found. Please specify the path to the exiftool executable."
            )
            info_label.setWordWrap(True)
            self.layout.addWidget(info_label)

        exiftool_layout = QHBoxLayout()
        
        label = QLabel("exiftool Path:")
        exiftool_layout.addWidget(label)

        self.exiftool_path_edit = QLineEdit(self.settings.value("exiftool"))
        exiftool_layout.addWidget(self.exiftool_path_edit)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_exiftool_path)
        exiftool_layout.addWidget(browse_button)

        self.layout.addLayout(exiftool_layout)

        save_button = QPushButton("Save")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(save_button)

    def browse_exiftool_path(self):
        """Opens a file dialog to browse for the exiftool executable."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executable Files (*)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.exiftool_path_edit.setText(selected_file)

    def save_settings(self):
        """Saves the settings and closes the dialog."""
        self.settings.setValue("exiftool", self.exiftool_path_edit.text())
        self.accept()
