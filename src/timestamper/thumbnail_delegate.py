from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from .constants import DONE_ICON

class ThumbnailDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Let the base class handle the default painting
        super().paint(painter, option, index)

        # Check if the item is marked as 'done'
        is_done = index.data(Qt.UserRole + 1)
        if is_done:
            painter.save()
            
            # Set a bold font for the checkmark
            font = painter.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() * 2)
            painter.setFont(font)
            
            # Set the color (e.g., green)
            painter.setPen(QColor("green"))
            
            # Position the checkmark over the thumbnail
            # This might need adjustment depending on the icon size and view mode
            rect = option.rect
            painter.drawText(rect, Qt.AlignCenter, DONE_ICON)
            
            painter.restore()
