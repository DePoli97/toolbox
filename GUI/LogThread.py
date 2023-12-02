import subprocess

from PyQt5.QtCore import QThread, pyqtSignal


class LogThread(QThread):
    log_updated = pyqtSignal(str)

    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        process = subprocess.Popen(
            [self.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )

        while True:
            line = process.stdout.readline()
            if not line:
                break

            self.log_updated.emit(line)

        process.communicate()
