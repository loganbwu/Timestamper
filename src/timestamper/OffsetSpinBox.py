from PySide6.QtWidgets import QDoubleSpinBox, QLineEdit
from PySide6.QtGui import QValidator


class DoubleOffsetSpinBox(QDoubleSpinBox):
    """A QDoubleSpinBox that displays float values as timezone offsets (e.g., +08:30)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-14.0, 14.0) # Set a reasonable range for timezones
        self.setSingleStep(0.5)
        self.setDecimals(2) # Allow for .5 increments, but display as :30

    def textFromValue(self, val: float) -> str:
        """Converts a float value to a timezone offset string."""
        sign = "+" if val >= 0 else "-"
        val = abs(val)
        hours = int(val)
        minutes = int(round((val % 1) * 60)) # Round minutes to nearest integer
        offset = f"{sign}{hours:02d}:{minutes:02d}"
        return offset

    def validate(self, input: str, pos: int) -> QValidator.State:
        """Validates the input text for the timezone offset."""
        input = input.strip()
        if not input:
            return QValidator.State.Intermediate # Allow empty input during editing

        # Check for sign
        if input.startswith('+') or input.startswith('-'):
            input_without_sign = input[1:]
        else:
            input_without_sign = input

        # Check for colon
        if ':' in input_without_sign:
            parts = input_without_sign.split(':')
            if len(parts) > 2: # More than one colon
                return QValidator.State.Invalid
            
            hours_str = parts[0]
            minutes_str = parts[1] if len(parts) > 1 else ""

            # Validate hours
            if not hours_str.isdigit() or not (0 <= int(hours_str) <= 14): # Max 14 hours for timezone
                return QValidator.State.Invalid
            
            # Validate minutes
            if minutes_str:
                if not minutes_str.isdigit() or not (0 <= int(minutes_str) < 60):
                    return QValidator.State.Invalid
                if len(minutes_str) > 2: # e.g., 08:300
                    return QValidator.State.Invalid
            
            # If we have a colon but incomplete minutes (e.g., "+08:"), it's intermediate
            if len(parts) == 2 and not minutes_str:
                return QValidator.State.Intermediate
            
        else: # No colon, just hours or partial number
            if not input_without_sign.replace('.', '', 1).isdigit(): # Allow decimal for direct float input
                return QValidator.State.Invalid
            
            try:
                val = float(input_without_sign)
                if not (0 <= val <= 14):
                    return QValidator.State.Invalid
            except ValueError:
                return QValidator.State.Invalid
            
        return QValidator.State.Acceptable # If all checks pass, accept the input

    def fixup(self, input: str) -> str:
        """Attempts to fix up invalid input."""
        # This method is called for Intermediate inputs when focus is lost.
        # We can try to format it to a standard form.
        try:
            value = self.valueFromText(input)
            return self.textFromValue(value)
        except Exception:
            return self.textFromValue(0.0) # Fallback to 0.0 if fixup fails

    def valueFromText(self, text: str) -> float:
        """Converts a timezone offset string to a float value."""
        text = text.strip()
        if not text:
            return 0.0

        offset_sign = 1.0
        if text.startswith('+'):
            text = text[1:]
        elif text.startswith('-'):
            offset_sign = -1.0
            text = text[1:]

        try:
            if ':' in text:
                parts = text.split(':')
                hours = float(parts[0])
                minutes = float(parts[1]) if len(parts) > 1 else 0.0
            else:
                hours = float(text)
                minutes = 0.0
            
            value = offset_sign * (hours + minutes / 60.0)
            return value
        except ValueError:
            return 0.0 # Return 0.0 for invalid input
