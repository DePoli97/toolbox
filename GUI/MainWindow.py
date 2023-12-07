import os
import re
import shutil
import subprocess

from PyQt5.QtCore import Qt, QSize, QProcess, pyqtSlot
from PyQt5.QtGui import QPixmap, QMouseEvent, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QGridLayout, \
    QScrollArea, QProgressBar, QInputDialog, QFileDialog, QApplication

from GUI.side_panel_dialog import PopUpDialog
from GUI.ScriptEditorWidget import ScriptEditorWidget
from config import base_path, release_directory, disk_devices


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TOOLBOX")
        self.setMinimumSize(750, 850)
        self.setWindowIcon(QIcon("../resources/images/toolbox_icon.ico"))

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Create a layout for the project name label and info icon
        self.project_info_layout = QHBoxLayout()
        self.project_info_layout.setContentsMargins(0, 0, 0, 0)
        self.project_info_layout.setSpacing(0)  # No spacing between items

        # Add a stretchable spacer to center the project name
        self.project_info_layout.addStretch(1)

        # Create the QLabel for the project name
        self.project_name_label = QLabel("Installed Release Version: N/A")
        self.project_name_label.setAlignment(Qt.AlignCenter)
        self.project_name_label.setStyleSheet("color: blue; font-weight: bold; font-size: 16px")

        # Add the QLabel to the project info layout
        self.project_info_layout.addWidget(self.project_name_label)

        # Add a stretchable spacer after the project name
        self.project_info_layout.addStretch(1)

        # Add the QLabel for the info icon
        self.info_icon_label = QLabel()
        icon_path = ":/info.png"  # Use the resource prefix
        icon_pixmap = QPixmap(icon_path)
        scaled_icon = icon_pixmap.scaled(QSize(20, 20), Qt.KeepAspectRatio)
        self.info_icon_label.setPixmap(scaled_icon)
        self.info_icon_label.setToolTip("Click to show info")
        self.info_icon_label.setAlignment(Qt.AlignTop | Qt.AlignRight)

        # Add the QLabel to the project info layout
        self.project_info_layout.addWidget(self.info_icon_label)

        # Add the project info layout to the main layout
        layout.addLayout(self.project_info_layout)
        # Add some padding (e.g., 20 pixels) under the project info layout
        layout.addSpacing(20)

        # Connect the info icon click event to show/hide the side panel
        self.info_icon_label.mousePressEvent = self.toggle_side_panel

        # Call the update_project_name method to initialize the project name
        self.update_project_name()

        # Create the section for installing releases
        install_release_layout = QHBoxLayout()

        # Create a QLabel for the title
        title_label = QLabel("Install Release:")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px")
        install_release_layout.addWidget(title_label)

        # Create a QComboBox for the file selection
        self.release_combo_box = QComboBox()
        install_release_layout.addWidget(self.release_combo_box)

        # Create the "Play" button
        install_button = QPushButton("Install")
        install_button.clicked.connect(self.run_selected_file)
        install_release_layout.addWidget(install_button)

        # Add the install release layout to the main layout
        layout.addLayout(install_release_layout)

        # Create a logs title label
        logs_title_label = QLabel("Logs")
        logs_title_label.setStyleSheet("font-weight: bold; font-size: 14px")
        layout.addWidget(logs_title_label)

        # Create a scroll area for the log window
        self.scroll_area = QScrollArea()  # Store it as an instance variable
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        layout.addWidget(self.scroll_area)  # Use instance variable here

        # Create a log window using QLabel
        self.log_label = QLabel()
        self.log_label.setStyleSheet("background-color: white")
        self.log_label.setWordWrap(True)
        self.log_label.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.log_label)  # Use instance variable here

        self.script_widget = ScriptEditorWidget(self)
        self.script_widget.log_signal.connect(self.log)
        layout.addWidget(self.script_widget)

        # Create a Copy logs button
        copy_button = QPushButton("Copy logs")
        copy_button.clicked.connect(self.copy_to_clipboard)

        # Create a Clear logs button
        clear_button = QPushButton("Clear logs")
        clear_button.clicked.connect(self.clear_logs)

        # Add both buttons to a horizontal layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(copy_button)
        buttons_layout.addWidget(clear_button)

        # Add the horizontal layout to the main layout
        layout.addLayout(buttons_layout)

        # Create progress bars and disk space labels as instance variables
        self.disk_labels = {}
        self.progress_bars = {}
        self.clear_buttons = {}  # Store clear buttons in a dictionary
        for index, device in enumerate(disk_devices.keys()):
            label = QLabel()
            layout.addWidget(label)
            self.disk_labels[device] = label

            # Create a QHBoxLayout for each progress bar and clear button
            row_layout = QHBoxLayout()

            progress_bar = QProgressBar()
            progress_bar.setTextVisible(True)  # Show text inside progress bar
            row_layout.addWidget(progress_bar)
            self.progress_bars[device] = progress_bar

            # Create a Clear button for each progress bar
            clear_button = QPushButton("Clear")
            clear_button.clicked.connect(lambda _, dev=device: self.trigger_clear_script(dev))
            row_layout.addWidget(clear_button)
            self.clear_buttons[device] = clear_button

            # Add the QHBoxLayout to the main layout
            layout.addLayout(row_layout)

        # Set the central widget
        self.setCentralWidget(central_widget)

        # Update disk space labels
        self.update_disk_space_labels()
        self.timer = self.startTimer(10000)  # Update every 10 seconds

        # Populate the release combo box
        self.populate_release_combo_box()

    def toggle_side_panel(self, event: QMouseEvent):
        # Show the side panel dialog when the info icon is clicked
        side_panel_dialog = PopUpDialog(self)
        side_panel_dialog.exec_()  # Show the dialog as a modal dialog

    def populate_release_combo_box(self):
        # Get the list of files in the specified directory
        release_directory = "/home/delvitech/work/sapiens-docker-compose/"
        if os.path.exists(release_directory):
            release_files = [f for f in os.listdir(release_directory) if
                             re.match(r'.*\d.*\.(yaml|yml)$', f) and os.path.isfile(os.path.join(release_directory, f))]
            self.release_combo_box.addItems(release_files)

    def update_project_name(self):
        # Get the current project name from the Docker container name
        container_name_command = "docker container ls -a --filter \"name=wrapper\" --format \"{{.Names}}\""
        try:
            container_names = subprocess.check_output(container_name_command, shell=True, text=True).strip().split("\n")
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            return

        # If there are no containers with the name "wrapper", set the project name to "N/A"
        if not container_names:
            self.current_project_name = "N/A"
        else:
            # Get the first container name and extract the project name from it
            container_name = container_names[0]
            self.current_project_name = container_name.split("_")[0]

        # print("Current project name:", self.current_project_name)  # Debugging statement

        # Update the project name label
        self.project_name_label.setText(f"Installed Release: {self.current_project_name}")

    def run_selected_file(self):
        # Get the selected file from the combo box
        selected_file = self.release_combo_box.currentText()

        # Extract the project_name from the selected_file
        project_name = selected_file.split("-")[-1]
        project_name = project_name[:project_name.rfind(".")]
        project_name = project_name.strip()

        # Stop the existing containers using docker-compose
        stop_command = f"docker-compose -f \"{os.path.join(release_directory, selected_file)}\" stop"

        stop_process = QProcess()
        stop_process.setProcessChannelMode(QProcess.MergedChannels)
        stop_process.readyRead.connect(lambda: self.append_log(stop_process))

        # Start the stop command in a subprocess
        stop_process.start(stop_command)
        stop_process.waitForFinished(-1)

        # Clear unused containers
        clear_containers = f"docker system prune -a -f"

        stop_process = QProcess()
        stop_process.setProcessChannelMode(QProcess.MergedChannels)
        stop_process.readyRead.connect(lambda: self.append_log(stop_process))

        # Start the stop command in a subprocess
        stop_process.start(clear_containers)
        stop_process.waitForFinished(-1)

        # Run the selected file using docker-compose up -d
        up_command = f"docker-compose -f \"{os.path.join(release_directory, selected_file)}\" -p \"{project_name}\" up -d"

        up_process = QProcess()
        up_process.setProcessChannelMode(QProcess.MergedChannels)
        up_process.readyRead.connect(lambda: self.append_log(up_process))

        # Start the up command in a subprocess
        up_process.start(up_command)
        up_process.waitForFinished(-1)

    def trigger_script(self, script_path):
        self.clear_logs()  # Clear the log label

        if "backup_database.sh" in script_path:
            # Show a custom input dialog to get the database name from the user
            database_name, ok = QInputDialog.getText(self, "Enter Database Name", "Enter the database name:")
            if not ok or not database_name:
                return  # User canceled or did not enter a name

            # Show a file dialog for the user to select the destination file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog  # To bypass the native file dialog (useful on some platforms)
            default_file_name = f"{database_name}.sql"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save SQL Backup", default_file_name,
                                                       "SQL Files (*.sql);;All Files (*)", options=options)
            if not file_path:
                return  # User canceled the file dialog

            # Replace the "{DB_NAME}" and "{DESTINATION}" placeholders in the script with the user input
            script_content = None
            with open(script_path, "r") as script_file:
                script_content = script_file.read()

            if script_content:
                script_content = script_content.replace("{DB_NAME}", database_name)
                script_content = script_content.replace("{DESTINATION}", file_path)

                # Use subprocess.Popen to execute the script and capture the output
                process = subprocess.Popen(
                    ["bash"],  # Use the bash shell to interpret the script content
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                # Execute the script and capture the output
                output, _ = process.communicate(input=script_content)

                # Append the output to the log label
                self.log(output)

        elif "update_database.sh" in script_path:
            # Show a file dialog for the user to select the origin file
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog  # To bypass the native file dialog (useful on some platforms)
            origin_file, _ = QFileDialog.getOpenFileName(self, "Select Origin File", "", "SQL Files (*.sql)",
                                                         options=options)
            if not origin_file:
                return  # User canceled the file dialog

            # Show a custom input dialog to get the database name from the user
            database_name, ok = QInputDialog.getText(self, "Enter Database Name", "Enter the database name:")
            if not ok or not database_name:
                return  # User canceled or did not enter a name

            # Read the content of the script file
            with open(script_path, "r") as script_file:
                script_content = script_file.read()

            # Replace the "{ORIGIN}" and "{DB_NAME}" placeholders in the script with the user input
            script_content = script_content.replace("{ORIGIN}", origin_file)
            script_content = script_content.replace("{DB_NAME}", database_name)

            # Use subprocess.Popen to execute the script and capture the output
            process = subprocess.Popen(
                ["bash"],  # Use the bash shell to interpret the script content
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Execute the script and capture the output
            output, _ = process.communicate(input=script_content)

            # Append the output to the log label
            self.log(output)
        else:
            # Use QProcess for other scripts
            process = QProcess()

            # Connect process signals for log updates
            process.setProcessChannelMode(QProcess.MergedChannels)
            process.readyRead.connect(lambda: self.append_log(process))
            process.finished.connect(lambda exit_code, exit_status: process.deleteLater())

            # Start the shell script in a subprocess
            print("Starting script:", script_path)
            process.start(script_path)

    def append_log(self, process):
        # Read the available data from the subprocess
        output = process.readAll().data().decode("utf-8")
        self.log(output)

    @pyqtSlot(str)
    def log(self, message):
        # Append the message to the log label
        self.log_label.setText(self.log_label.text() + message + "\n")

        # Scroll to the bottom to show the latest log messages
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def copy_to_clipboard(self):
        # Copy the content of the log label to the clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_label.text())

    def clear_logs(self):
        # Clear the log label
        self.log_label.setText("")

    def update_disk_space_labels(self):
        for device, label in self.disk_labels.items():
            # Get the mount point for the device
            mount_point = disk_devices[device]

            if os.path.exists(mount_point):
                # Get disk usage information for the device
                disk_usage = shutil.disk_usage(mount_point)
                total_space = disk_usage.total // (1024 ** 3)  # Convert to gigabytes
                available_space = disk_usage.free // (1024 ** 3)  # Convert to gigabytes

                # Update the label with disk space information
                label.setText(f"{device.capitalize()}: {available_space} GB / {total_space} GB")

                # Update the progress bar value
                progress_bar = self.progress_bars[device]
                progress_bar.setValue(int((disk_usage.used / disk_usage.total) * 100))
            else:
                # Mount point does not exist
                label.setText(f"{device.capitalize()}: Not mounted")

    def timerEvent(self, event):
        if event.timerId() == self.timer:
            self.update_disk_space_labels()
        else:
            super().timerEvent(event)

    def trigger_clear_script(self, device):
        # Implement the action for the "Clear" button for each progress bar here
        if device == "system":
            script_path = os.path.join(base_path, "../scripts/clear_disks/clear_system.sh")
            self.trigger_script(script_path)
        elif device == "ramdisk":
            script_path = os.path.join(base_path, "../scripts/clear_disks/clear_ramdisk.sh")
            self.trigger_script(script_path)
        elif device == "backup":
            script_path = os.path.join(base_path, "../scripts/clear_disks/clear_backup.sh")
            self.trigger_script(script_path)
