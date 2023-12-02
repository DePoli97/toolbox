from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel


class PopUpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.Window)  # Use Qt.Window flag for separate window

        self.setWindowTitle("Info")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("INFO"))  # Add your content here
