from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtGui import QFocusEvent, QValidator


class DoubleOffsetSpinBox(QDoubleSpinBox):
    """
    A QDoubleSpinBox customized to display and handle timezone offsets.

    This widget manages a floating-point value representing hours but displays it
    to the user in a more readable timezone format, such as `+HH:MM`. It is
    designed to accept input in both the `HH:MM` format and as a standard
    floating-point number.

    Key Features:
    - **Internal Value**: Stored as a `float` (e.g., `8.5`).
    - **Display Format**: Shown as a string `[+|-]HH:MM` (e.g., `"+08:30"`).
    - **Input Flexibility**: Accepts user input as a timezone string (`-04:00`),
      a partial string (`-4:30`), or a float (`-4.5`).
    - **Custom Validation**: Implements real-time validation to guide the user
      in entering a valid offset.
    - **Automatic Formatting**: On losing focus, the input is parsed and
      re-formatted into the canonical `[+|-]HH:MM` format.

    Behavior:
    - The spin box arrows step the value by 30-minute (0.5 hour) increments.
    - The range of valid offsets is from -14.0 to +14.0 hours.
    - The `textFromValue` and `valueFromText` methods handle the conversion
      between the internal float value and the display string.
    - A custom `validate` method checks the text as it is being typed,
      providing `Acceptable`, `Intermediate`, or `Invalid` states.
    - The `focusOutEvent` is overridden to ensure that the user's final text
      is correctly interpreted and converted to a float value, bypassing the
      default `QDoubleSpinBox` parsing which would fail with the `HH:MM` format.

    Example:
        - User types `5.5`. On focus out, it becomes `"+05:30"`.
        - User types `-8`. On focus out, it becomes `"-08:00"`.
        - User types `+7:15`. On focus out, it becomes `"+07:15"`.
        - User clicks the up arrow from `"+01:00"`. The value becomes `"+01:30"`.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-14.0, 14.0)
        self.setSingleStep(0.5)
        # We manage decimals internally; the display is a string.
        self.setDecimals(4)  # Allow enough precision for minutes
        self.setValue(0.0)

    def textFromValue(self, val: float) -> str:
        """Converts a float value to a timezone offset string `[+|-]HH:MM`."""
        sign = "+" if val >= 0 else "-"
        val = abs(val)
        hours = int(val)
        minutes = int(round((val % 1) * 60))
        return f"{sign}{hours:02d}:{minutes:02d}"

    def valueFromText(self, text: str) -> float:
        """Converts a timezone offset string or float string to a float value."""
        text = text.strip()
        if not text:
            return 0.0

        # Handle GMT prefix
        if text.upper().startswith('GMT'):
            text = text[3:].lstrip()

        sign = 1.0
        if text.startswith('+'):
            text = text[1:]
        elif text.startswith('-'):
            sign = -1.0
            text = text[1:]

        try:
            if ':' in text:
                parts = text.split(':', 1)
                hours_str = parts[0]
                minutes_str = parts[1] if parts[1] else "0"
                
                hours = float(hours_str) if hours_str else 0.0
                minutes = float(minutes_str) if minutes_str.isdigit() else 0.0
                
                value = hours + (minutes / 60.0)
            else:
                # Handle float/integer input directly
                value = float(text) if text else 0.0
            
            return sign * value
        except (ValueError, IndexError):
            return 0.0  # Fallback for invalid format

    def validate(self, input_str: str, pos: int) -> QValidator.State:
        """Validates the input text for a valid timezone offset."""
        input_str = input_str.strip()
        
        if not input_str:
            return QValidator.State.Intermediate

        # Handle optional GMT prefix for validation
        numeric_part = input_str
        if numeric_part.upper().startswith('GMT'):
            # Check for partial "G", "GM"
            if len(numeric_part) < 3:
                return QValidator.State.Intermediate if "GMT".startswith(numeric_part.upper()) else QValidator.State.Invalid
            # Check for just "GMT"
            if len(numeric_part) == 3:
                return QValidator.State.Intermediate
            
            numeric_part = numeric_part[3:].lstrip()

        # Now, `numeric_part` holds the part to validate for numeric correctness.
        
        # Allow sign prefix
        temp_str = numeric_part
        if temp_str.startswith(('+', '-')):
            temp_str = temp_str[1:]

        # Check for valid characters
        if not all(c.isdigit() or c in '.:' for c in temp_str):
            return QValidator.State.Invalid

        # Check for multiple colons or dots
        if temp_str.count(':') > 1 or temp_str.count('.') > 1:
            return QValidator.State.Invalid
        
        # If it contains a colon, validate as HH:MM
        if ':' in temp_str:
            parts = temp_str.split(':', 1)
            hours_str, minutes_str = parts
            
            if not hours_str.isdigit() and hours_str:
                return QValidator.State.Invalid
            
            if hours_str and not (0 <= int(hours_str) <= 14):
                return QValidator.State.Invalid

            if minutes_str and (not minutes_str.isdigit() or len(minutes_str) > 2):
                return QValidator.State.Invalid
            
            if minutes_str and int(minutes_str) >= 60:
                return QValidator.State.Invalid

        # If it contains a dot, validate as a float
        elif '.' in temp_str:
            try:
                val = float(temp_str)
                if not (0 <= val <= 14.0):
                    return QValidator.State.Invalid
            except ValueError:
                return QValidator.State.Invalid
        
        # If it's just a number (integer)
        elif temp_str.isdigit():
            val = int(temp_str)
            if not (0 <= val <= 14):
                return QValidator.State.Invalid

        # Try to convert to a final value to check range
        # IMPORTANT: Use the original input_str here for valueFromText
        try:
            final_value = self.valueFromText(input_str)
            if not (self.minimum() <= final_value <= self.maximum()):
                return QValidator.State.Invalid
        except (ValueError, IndexError):
            return QValidator.State.Intermediate # Still typing

        return QValidator.State.Acceptable

    def fixup(self, input_str: str) -> str:
        """Corrects an intermediate or invalid input into a valid format."""
        value = self.valueFromText(input_str)
        # Clamp the value to the allowed range before formatting
        clamped_value = max(self.minimum(), min(value, self.maximum()))
        return self.textFromValue(clamped_value)

    def stepBy(self, steps: int):
        """Overrides stepBy to ensure clean 30-minute increments."""
        # Step by 0.5 hours (30 minutes)
        new_val = self.value() + (steps * self.singleStep())
        
        # Clamp to range
        clamped_value = max(self.minimum(), min(new_val, self.maximum()))
        
        self.setValue(clamped_value)

    def focusOutEvent(self, event: QFocusEvent):
        """
        Overrides the focus out event to parse the text and set the value.
        This is critical for handling the custom `HH:MM` format.
        """
        # When focus is lost, we parse the current text and set the value.
        # This ensures that manual text edits are correctly processed.
        text = self.text()
        value = self.valueFromText(text)
        self.setValue(value)

        # Call the parent implementation to complete the event handling.
        super().focusOutEvent(event)
