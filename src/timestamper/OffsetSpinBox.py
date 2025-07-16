from PySide6.QtWidgets import QDoubleSpinBox


class DoubleOffsetSpinBox(QDoubleSpinBox):
    """A QDoubleSpinBox that displays float values as timezone offsets (e.g., +08:30)."""

    def textFromValue(self, val: float) -> str:
        """Converts a float value to a timezone offset string."""
        sign = "+" if val >= 0 else "-"
        val = abs(val)
        hours = int(val)
        minutes = int((val % 1) * 60)
        offset = f"{sign}{hours:02d}:{minutes:02d}"
        return offset

    def valueFromText(self, text: str) -> float:
        """Converts a timezone offset string to a float value."""
        offset_sign = 1 if text.startswith("+") else -1
        try:
            offset_hr = int(text[1:3])
            offset_min = int(text[4:6])
            value = offset_sign * (offset_hr + offset_min / 60)
        except (ValueError, IndexError):
            value = 0.0
        return value
