from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout


class MainPanel(QMainWindow):


    def __init__(self):
        super().__init__()
        self.setWindowTitle("TOOLBOX")
        self.setMinimumSize(750, 850)
        self.setWindowIcon(QIcon("../resources/images/toolbox_icon.ico"))
        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)


