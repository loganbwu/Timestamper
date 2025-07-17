from PySide6.QtWidgets import QListWidget, QWidget, QStyledItemDelegate, QApplication
from PySide6.QtCore import Qt, Signal, QSize, QRect
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QPainter, QIcon, QFontMetrics
from typing import Optional, List


class FileListItemDelegate(QStyledItemDelegate):
    """Custom delegate for drawing items in the file list."""
    def paint(self, painter: QPainter, option, index):
        """Paints the item with a checkmark if it's done."""
        # Call the base class paint to draw the default icon and text
        super().paint(painter, option, index)

        # Get the 'done' status from the item's data
        is_done = index.data(Qt.UserRole + 1) # Using UserRole + 1 for done status

        if is_done:
            # Draw a checkmark
            # You might want to use a QIcon for a more professional checkmark
            # For simplicity, let's draw a text checkmark for now
            checkmark_text = "✓"
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # Calculate position for the checkmark (e.g., top-right of the icon/text area)
            # This is a simplified placement, adjust as needed for exact layout
            text_rect = option.rect
            
            # Position the checkmark to the right of the text, or adjust as needed
            metrics = QFontMetrics(painter.font())
            text_width = metrics.horizontalAdvance(index.data(Qt.DisplayRole))
            
            # Adjust x position to be to the right of the text, with some padding
            x = text_rect.left() + option.decorationSize.width() + text_width + 5 # 5 for padding
            y = text_rect.top() + (text_rect.height() - metrics.height()) / 2 + metrics.ascent()
            
            painter.drawText(x, y, checkmark_text)

    def sizeHint(self, option, index):
        """Returns the size hint for the item, adjusting for padding."""
        # Get the default size hint
        size = super().sizeHint(option, index)
        
        # Reduce vertical padding if needed, or adjust overall size
        # The default QListWidgetItem.setSizeHint(QSize(120, 120)) is already quite large.
        # We might want to make the default smaller in main.py if this is still too big.
        # For now, let's just ensure it's not excessively padded by the delegate.
        # This is where you'd adjust for the "too much padding" issue (Issue #6)
        # For now, I'll keep it simple and just return the super's size.
        # The main padding issue is likely in the QListWidget's view mode or item size hint.
        return size


class DragDropListWidget(QListWidget):
    """A QListWidget that supports drag and drop of files."""
    filesDropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initializes the DragDropListWidget."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handles the drag enter event to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handles the drag move event to accept URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """Handles the drop event to add dropped files to the list."""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
            self.filesDropped.emit(links)
        else:
            super().dropEvent(event)
