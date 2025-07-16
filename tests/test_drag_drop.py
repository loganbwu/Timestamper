import pytest
from PySide6.QtCore import QUrl, QMimeData, Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication
from src.timestamper.drag_drop_list_widget import DragDropListWidget
import os

@pytest.fixture
def app(qtbot):
    """Create a QApplication instance."""
    test_app = QApplication.instance()
    if test_app is None:
        test_app = QApplication([])
    return test_app

def test_drag_drop_list_widget(qtbot, app):
    """Test the DragDropListWidget."""
    widget = DragDropListWidget()
    qtbot.addWidget(widget)

    # Create a dummy file
    file_path = "test_file.txt"
    with open(file_path, "w") as f:
        f.write("test")

    # Simulate a drop event
    mime_data = QMimeData()
    urls = [QUrl.fromLocalFile(os.path.abspath(file_path))]
    mime_data.setUrls(urls)
    
    # The drop event needs a position, so we use the widget's rect
    drop_event = QDropEvent(widget.rect().center(), Qt.CopyAction, mime_data, Qt.LeftButton, Qt.NoModifier)

    # A mock to capture the emitted files
    from unittest.mock import Mock
    mock_slot = Mock()
    widget.filesDropped.connect(mock_slot)

    # Process the event
    widget.dropEvent(drop_event)

    # Check that the signal was emitted with the correct file path
    mock_slot.assert_called_once_with([os.path.abspath(file_path)])

    # Clean up
    os.remove(file_path)
