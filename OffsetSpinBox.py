from PySide6.QtWidgets import QDoubleSpinBox

class DoubleOffsetSpinBox(QDoubleSpinBox):
    # Convert between float formats at "+8:30" type text
    def textFromValue(self, val):
        sign = "+" if val >= 0 else "-"
        val = abs(val)
        hours = int(val)
        minutes = int((val % 1) * 60)
        offset = f"{sign}{hours:02d}:{minutes:02d}"
        return(offset)

    def valueFromText(self, text):
        offset_sign = 1 if text[0] == "+" else -1
        offset_hr = int(text[1:3])
        offset_min = int(text[4:6])
        return(offset_sign * (offset_hr + offset_min/60))
