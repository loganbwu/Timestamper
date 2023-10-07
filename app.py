import sys

from PySide6.QtWidgets import QApplication
from main import MainWindow


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
