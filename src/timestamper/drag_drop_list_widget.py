from PySide6.QtWidgets import QListWidget, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from typing import Optional, List


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
