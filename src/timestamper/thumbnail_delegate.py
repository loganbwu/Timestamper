from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from .constants import DONE_ICON

class ThumbnailDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        """Returns the size hint for the item, adjusting for padding."""
        # Get the default size hint
        size = super().sizeHint(option, index)
        # Set a fixed height to reduce vertical padding
        size.setHeight(40)
        return size
    def paint(self, painter, option, index):
        # Let the base class handle the default painting
        super().paint(painter, option, index)

        pass
