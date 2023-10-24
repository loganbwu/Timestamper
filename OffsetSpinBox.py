from PySide6.QtWidgets import QDoubleSpinBox

class DoubleOffsetSpinBox(QDoubleSpinBox):
    def textChanged(self, arg__1):
        QDoubleSpinBox.textChanged(arg__1)