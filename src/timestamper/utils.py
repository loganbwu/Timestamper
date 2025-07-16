"""Utility functions for the Timestamper application."""

import logging

logger = logging.getLogger(__name__)


def float_to_shutterspeed(value: float) -> str:
    """Converts a float value to a shutter speed string."""
    if float(value) < 1:
        inv_shutterspeed = 1/float(value)
        return f"1/{inv_shutterspeed:g}s"
    else:
        return f"{value:g}s"


def parse_lensinfo(lensinfo: str) -> list[str] | None:
    """Parses the lens info string into a list of its components."""
    elements = lensinfo.split(" ", 3)
    if len(elements) != 4:
        return None
    
    def can_be_cast_to_float(x):
        if x is None:
            return False
        try:
            float(x)
            return True
        except ValueError:
            return False
    
    processed_elements = []
    for x in elements:
        if can_be_cast_to_float(x):
            processed_elements.append(x)
        else:
            return None  # If any element is not float-castable, return None for the whole thing
    return processed_elements


def format_as_offset(x: float) -> str:
    """Formats a float as a timezone offset string."""
    x = abs(x)
    hours = int(x)
    minutes = int((x % 1) * 60)
    offset = f"{hours:02d}:{minutes:02d}"
    return offset


def validate_numeric_input(field_name: str, text_value: str) -> bool:
    """Validates that a given text value can be cast to a float."""
    if text_value == "":
        return True  # Empty string is allowed, means no value to write
    try:
        float(text_value)
        return True
    except ValueError:
        error_message = f"Error: Invalid numeric input for {field_name}: '{text_value}'"
        logger.error(error_message)
        return False
