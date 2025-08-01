import sys

from PySide6.QtWidgets import QApplication
from .main import MainWindow

def main():
    """Initializes and runs the Timestamper application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
