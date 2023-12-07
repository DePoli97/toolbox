import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from GUI.MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Path("stylesheet.qss").read_text())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
