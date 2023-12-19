import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel, QToolTip


class ArgumentType(Enum):
    UNKNOWN = 0
    REQUIRED_WITH_VALUE = 1
    OPTIONAL = 2
    OPTIONAL_WITH_VALUE = 3


class ArgumentStatus(Enum):
    AVAILABLE = 1
    SELECTED = 2
    REQUIRED = 3
    NOT_AVAILABLE = 4


@dataclass
class Argument:
    name: str
    name_repr: str = None
    argument_type: ArgumentType = None
    value_name: str = None
    default_value: str = None
    description: str = None

    def __post_init__(self):
        self.parse_name()

    def parse_name(self):
        if re.match(r"\[.* .*\]", self.name):
            self.argument_type = ArgumentType.OPTIONAL_WITH_VALUE
            self.name_repr = self.name[1:-1].split(" ")[0]
        elif re.match(r"\[.*\]", self.name):
            self.argument_type = ArgumentType.OPTIONAL
            self.name_repr = self.name[1:-1]
        elif re.match(r".* .*", self.name):
            self.argument_type = ArgumentType.REQUIRED_WITH_VALUE
            self.name_repr = self.name.split(" ")[0]
        else:
            self.argument_type = ArgumentType.UNKNOWN
            self.name_repr = self.name

    def __repr__(self):
        return f"Argument({self.name} {self.value_name}={self.default_value}, {self.argument_type} ({self.description[:20]}...)"


@dataclass
class RequiredArgumentGroup:
    arguments: List[Argument]

    def __repr__(self):
        return f"RequiredArgumentGroup({self.arguments})"


@dataclass
class OrArgumentGroup:
    arguments: List[RequiredArgumentGroup]

    def __init__(self, arguments: List[RequiredArgumentGroup], fix_first_argument: bool = False):
        if fix_first_argument:
            # Wrap the first argument in a RequiredArgumentGroup
            arguments[0] = RequiredArgumentGroup([arguments[0]])
        self.arguments = arguments

    def __repr__(self):
        return f"OrArgumentGroup({self.arguments})"


def split_arguments(description: str) -> List[Argument | OrArgumentGroup]:
    # Split the description into individual arguments
    arguments = []
    current_char = 0

    while current_char < len(description):
        if description[current_char] == "[":
            # Start of optional argument
            j = current_char + 1
            while description[j] != "]":
                j += 1
            arguments.append(Argument(description[current_char : j + 1]))
            current_char = j + 1

        elif description[current_char] == "(":
            # Start of required argument
            j = current_char + 1
            while description[j] != ")":
                j += 1
            arguments.append(OrArgumentGroup(split_arguments(description[current_char + 1 : j]), fix_first_argument=True))
            current_char = j + 1

        elif description[current_char] == "|":
            # Start of alternative argument
            j = current_char + 1
            while j < len(description) and description[j] != "|":
                j += 1
            arguments.append(RequiredArgumentGroup(split_arguments(description[current_char + 1 : j + 1])))
            current_char = j + 1

        elif description[current_char] == " ":
            # Skip whitespace
            current_char += 1

        elif description[current_char] == "-":
            # Start of required argument
            j = current_char + 1
            while description[j] not in [" ", "]", ")", "|"]:
                j += 1
            # print("name:" + description[current_char:j])

            if description[j + 1] in ["]", ")", "|"]:
                # Argument has no value
                # print("has no value")
                pass
            else:
                # Argument has a value
                j += 1  # Skip whitespace
                start_of_value = j
                while description[j] not in [" ", "]", ")", "|"]:
                    j += 1
                # print("value:" + description[start_of_value:j])

            arguments.append(Argument(description[current_char:j]))
            current_char = j + 1
        else:
            # Invalid character
            raise ValueError("Invalid character in description: " + description[current_char])
    return arguments


def read_description_of_arguments(
    command_arguments: List[Union[Argument, OrArgumentGroup]], description: list[str]
) -> List[Union[Argument, OrArgumentGroup]]:

    description = map(lambda x: x.strip(), description)
    fixed_arguments = []

    for argument in description:
        if not argument.startswith("-"):
            # Argument does not start with a dash, so it belongs to the previous argument
            fixed_arguments[-1] += "  " + argument
        else:
            fixed_arguments.append(argument)

    def extract_argument_properties(argument: str) -> Argument:
        # Split fixed arguments into: name, value name, description, default value

        name = argument.split("  ")[0]
        value_name = None
        # if a comma is found, pick the first part as the name
        if "," in name:
            name = name.split(",", 1)[0]
        if " " in name:
            name, value_name = name.split(" ")

        description = argument.rsplit("  ", 1)[1]
        default_value = None
        if description[-1] == ")":
            default_value = description.split("(default: ")[1].split(")")[0]
            description = description.split("(default: ")[0]

        return Argument(name=name, value_name=value_name, default_value=default_value, description=description)

    fixed_arguments = list(map(extract_argument_properties, fixed_arguments))

    def find_corresponding_argument(argument: Argument, argument_list: List[Argument]) -> Argument:
        for arg in argument_list:
            if arg.name_repr == argument.name_repr:
                return arg

        raise ValueError(f"Argument not found: {argument} in {argument_list}")

    arguments_with_description = []
    for argument in command_arguments:
        if isinstance(argument, Argument):
            argument_with_description = find_corresponding_argument(argument, fixed_arguments)
            argument_with_description.argument_type = argument.argument_type
            arguments_with_description.append(argument_with_description)
        elif isinstance(argument, OrArgumentGroup):
            required_groups = []
            for required_argument_group in argument.arguments:
                arguments = []
                for arg in required_argument_group.arguments:
                    argument_with_description = find_corresponding_argument(arg, fixed_arguments)
                    argument_with_description.argument_type = arg.argument_type
                    arguments.append(argument_with_description)
                required_groups.append(RequiredArgumentGroup(arguments))
            arguments_with_description.append(OrArgumentGroup(required_groups))
        else:
            raise ValueError("Invalid argument type")

    return arguments_with_description


@dataclass
class Script:
    name: str
    path: Path
    version: str
    author: str
    args: List[Argument]


@dataclass
class Folder:
    name: str
    scripts: List[Script]


class DisplayArgumentOptionWidget(QPushButton):
    add_signal = pyqtSignal(QPushButton)

    def __init__(self, parent, argument: Argument, status: ArgumentStatus = ArgumentStatus.AVAILABLE):
        super(DisplayArgumentOptionWidget, self).__init__(parent)

        self.parent = parent
        self.argument = argument
        self.status = status

        if argument.argument_type in (ArgumentType.REQUIRED_WITH_VALUE, ArgumentType.OPTIONAL_WITH_VALUE):
            if argument.default_value is None:
                self.setText(f"{argument.name_repr}=...")
            else:
                self.setText(f"{argument.name_repr}={argument.default_value}")
        else:
            self.setText(argument.name_repr)

        self.setProperty("argument", True)
        if self.status == ArgumentStatus.REQUIRED:
            self.setProperty("requiredArgument", True)
            self.setText(self.text() + "*")
        elif self.status == ArgumentStatus.SELECTED:
            self.setProperty("selectedArgument", True)
            self.setEnabled(False)
        elif self.status == ArgumentStatus.AVAILABLE:
            self.setProperty("availableArgument", True)
        elif self.status == ArgumentStatus.NOT_AVAILABLE:
            self.setProperty("notAvailableArgument", True)
            self.setEnabled(False)
        else:
            raise ValueError("Invalid status")

        self.clicked.connect(self.emit_add)
        self.add_signal.connect(self.parent.add_argument)

    def emit_add(self):
        self.add_signal.emit(self)

    def enterEvent(self, a0):
        QToolTip.showText(self.mapToGlobal(self.rect().topRight()), self.argument.description)


class DisplayScriptOptionWidget(QPushButton):
    add_signal = pyqtSignal(QPushButton)

    def __init__(self, parent, script: Script):
        super(DisplayScriptOptionWidget, self).__init__(parent)

        self.parent = parent
        self.script = script

        self.setText(script.name)

        self.clicked.connect(self.emit_add)

        self.add_signal.connect(self.parent.add_script)

    def emit_add(self):
        self.add_signal.emit(self)


class DisplayFolderOptionWidget(QWidget):
    add_signal = pyqtSignal(QLabel)

    def __init__(self, parent, folder: Folder):
        super(DisplayFolderOptionWidget, self).__init__(parent)

        self.folder = folder
        self.parent = parent

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignTop)
        self.label.setText(folder.name)
        self.main_layout.addWidget(self.label)

        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout()
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_widget.setLayout(self.options_layout)
        self.options_widget.hide()

        for folder_script in folder.scripts:
            self.options_layout.addWidget(DisplayScriptOptionWidget(parent, folder_script))
        self.main_layout.addWidget(self.options_widget)

    def enterEvent(self, a0):
        self.options_widget.show()
        self.parent.options_widget.adjustSize()

    def leaveEvent(self, a0):
        self.options_widget.hide()
        self.adjustSize()
        self.options_widget.adjustSize()
        self.parent.options_widget.adjustSize()


class ArgumentWidget(QWidget):
    delete_signal = pyqtSignal(QWidget)

    def __init__(self, argument: Argument, parent=None):
        super(ArgumentWidget, self).__init__(parent)

        self.argument = argument
        self.value = None

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.command_name = QLabel()
        self.command_name.enterEvent = self.command_name_enter_event
        self.main_layout.addWidget(self.command_name)

        if argument.argument_type in (ArgumentType.REQUIRED_WITH_VALUE, ArgumentType.OPTIONAL_WITH_VALUE):
            self.value = argument.default_value
            self.input_widget = QLineEdit()
            self.input_widget.setText(self.value)
            self.input_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.main_layout.addWidget(self.input_widget)

            self.command_name.setText(f"{argument.name_repr}=")
        else:
            self.command_name.setText(argument.name_repr)

        self.delete_button = QPushButton("X")
        self.delete_button.setMaximumWidth(20)
        self.delete_button.clicked.connect(self.emit_delete)
        self.main_layout.addWidget(self.delete_button)

    def command_name_enter_event(self, a0):
        QToolTip.showText(self.mapToGlobal(self.rect().topLeft()), self.argument.description)

    def emit_delete(self):
        self.delete_signal.emit(self)

    def get_command(self):
        if self.argument.argument_type in (ArgumentType.REQUIRED_WITH_VALUE, ArgumentType.OPTIONAL_WITH_VALUE):
            return self.argument.name_repr + "=" + self.input_widget.text()
        return self.argument.name_repr


class ScriptWidget(QWidget):
    delete_signal = pyqtSignal()

    def __init__(self, main_window, script: Script):
        QWidget.__init__(self, main_window)

        self.main_window = main_window

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.script = script

        self.script_name = QLabel(script.name)
        self.main_layout.addWidget(self.script_name)

        self.delete_button = QPushButton("X")
        self.delete_button.setMaximumWidth(20)
        self.delete_button.clicked.connect(self.emit_delete)
        self.main_layout.addWidget(self.delete_button)

    def emit_delete(self):
        self.delete_signal.emit()


class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(CustomLineEdit, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def focusInEvent(self, event):
        event.accept()
        QLineEdit.focusInEvent(self, event)
        self.parent().display_options()

    def focusOutEvent(self, event):
        event.accept()
        QLineEdit.focusOutEvent(self, event)
        self.parent().options_widget.hide()


class ScriptEditorWidget(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, main_window):
        super(ScriptEditorWidget, self).__init__(main_window)
        self.main_window = main_window

        self.python_scripts: List[Script] = self.read_python_scripts()
        self.shell_scripts: List[Folder] = self.read_shell_scripts()

        self.selected_script: Script = None

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.command_parts_layout = QHBoxLayout()
        self.command_parts_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.command_parts_layout)

        self.input_widget = CustomLineEdit()
        self.main_layout.addWidget(self.input_widget)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_script)
        self.main_layout.addWidget(self.run_button)

        self.available_options_layout = QVBoxLayout()
        self.options_widget = QWidget(main_window)
        self.options_widget.setObjectName("options_widget")
        self.options_widget.setLayout(self.available_options_layout)
        self.options_widget.hide()

    def get_available_scripts(self) -> List[DisplayArgumentOptionWidget]:
        options = []
        assert self.selected_script is None

        for folder in self.shell_scripts:
            options.append(DisplayFolderOptionWidget(self, folder))

        for script in self.python_scripts:
            options.append(DisplayScriptOptionWidget(self, script))
        return options

    def display_options(self):
        # Delete all the widgets inside the options layout
        while self.available_options_layout.count():
            item = self.available_options_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if self.selected_script is None:
            scripts = self.get_available_scripts()
            if not scripts:
                self.available_options_layout.addWidget(QLabel("No scripts available"))

            for script in scripts:
                self.available_options_layout.addWidget(script)
        else:
            arguments = self.selected_script.args
            if not arguments:
                self.available_options_layout.addWidget(QLabel("No arguments available"))
                self.update_options_widget_size()
                self.options_widget.show()
                self.options_widget.raise_()
                return

            def add_argument(
                layout, selected_arguments, argument: Argument, status: ArgumentStatus = ArgumentStatus.AVAILABLE
            ):
                for selected_argument in selected_arguments:
                    if selected_argument.argument.name_repr == argument.name_repr:
                        status = ArgumentStatus.SELECTED
                        break
                layout.addWidget(DisplayArgumentOptionWidget(self, argument, status))

            def add_or_argument_group(layout, selected_arguments, argument: OrArgumentGroup):
                vertical_layout = QVBoxLayout()
                layout.addLayout(vertical_layout)
                label = QLabel("Choose one path of arguments")
                label.setAlignment(Qt.AlignBottom)
                vertical_layout.addWidget(label)

                # If any argument in the group is selected, the other groups become unavailable
                argument_selected_row = None
                for i, required_arg_list in enumerate(argument.arguments):
                    if argument_selected_row is None and any(
                        selected_argument.argument.name_repr in [arg.name_repr for arg in required_arg_list.arguments]
                        for selected_argument in selected_arguments
                    ):
                        argument_selected_row = i

                for j, required_arg_list in enumerate(argument.arguments):
                    # No argument in any group has been selected
                    if argument_selected_row is None:
                        add_required_argument_group(vertical_layout, selected_arguments, required_arg_list)
                        continue

                    # Lie and say that there is no other row with a selected argument
                    if argument_selected_row == j:
                        add_required_argument_group(vertical_layout, selected_arguments, required_arg_list)
                        continue

                    # Other row has a selected argument, so mark all the arguments in this row as not available
                    add_required_argument_group(vertical_layout, selected_arguments, required_arg_list, True)
                    continue

            def add_required_argument_group(
                layout, selected_arguments, required_argument_group: RequiredArgumentGroup, any_argument_selected=False
            ):
                horizontal_layout = QHBoxLayout()
                layout.addLayout(horizontal_layout)

                # if any argument in the group is selected, the unselected ones become required
                status = ArgumentStatus.AVAILABLE

                if any_argument_selected:
                    status = ArgumentStatus.NOT_AVAILABLE
                else:
                    any_selected_in_group = False
                    for argument in required_argument_group.arguments:
                        for selected_argument in selected_arguments:
                            if selected_argument.argument.name_repr == argument.name_repr:
                                any_selected_in_group = True
                                break
                    if any_selected_in_group:
                        status = ArgumentStatus.REQUIRED

                for argument in required_argument_group.arguments:
                    # Don't mark as required the arguments that are optional
                    if not any_argument_selected and argument.argument_type in (
                        ArgumentType.OPTIONAL,
                        ArgumentType.OPTIONAL_WITH_VALUE,
                    ):
                        status = ArgumentStatus.AVAILABLE

                    add_argument(horizontal_layout, selected_arguments, argument, status)

            container = QWidget()
            main_layout = QHBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(main_layout)
            self.available_options_layout.addWidget(container)

            selected_arguments = self.get_selected_arguments()

            for argument in arguments:
                if isinstance(argument, Argument):
                    add_argument(main_layout, selected_arguments, argument)
                if isinstance(argument, OrArgumentGroup):
                    add_or_argument_group(main_layout, selected_arguments, argument)
                elif isinstance(argument, RequiredArgumentGroup):
                    add_required_argument_group(main_layout, selected_arguments, argument)

        self.update_options_widget_size()
        self.options_widget.show()
        self.options_widget.raise_()

    def update_options_widget_size(self):
        self.options_widget.adjustSize()
        coords = self.pos().x(), self.pos().y() - self.options_widget.height()
        self.options_widget.move(*coords)

    def resizeEvent(self, event):
        super(ScriptEditorWidget, self).resizeEvent(event)
        self.update_options_widget_size()

    def get_selected_arguments(self) -> List[ArgumentWidget]:
        widgets = []
        for i in range(self.command_parts_layout.count()):
            widget = self.command_parts_layout.itemAt(i).widget()
            if isinstance(widget, ArgumentWidget):
                widgets.append(widget)
        return widgets

    def read_python_scripts(self) -> List[Script]:
        # Get all .py files inside the scripts folder
        python_scripts = Path("scripts").glob("*.py")
        return [self.read_python_script(script) for script in python_scripts]

    def read_shell_scripts(self) -> List[Folder]:
        # Get all folders inside the scripts folder
        subdirectories = [folder for folder in Path("scripts").iterdir() if folder.is_dir()]
        folders = []
        for folder in subdirectories:
            shell_scripts = Path(folder).glob("*.sh")
            folder_scripts = [self.read_shell_script(script) for script in shell_scripts]
            folders.append(Folder(folder.name, folder_scripts))
        return folders

    @staticmethod
    def read_shell_script(script: Path) -> Script:
        # TODO: add documentation to shell scripts ?
        return Script(
            name=script.stem,
            path=script,
            version="",
            author="",
            args=[],
        )

    @staticmethod
    def read_python_script(script: Path) -> Script:
        # Get the output of the script's usage
        command = f'"{sys.executable}" {script} --help'
        lines = subprocess.check_output(command, shell=True, text=True).splitlines()

        # Get the script name, which is before the version
        name = lines[2].split("(")[0].strip()

        # Get the script version, which is in the third line between parentheses
        version = lines[2].split("(")[1].split(")")[0].strip()

        # Get the script author, which is in the third line after the version
        author = lines[2].split("maintained by")[1].strip()

        usage = lines[0].split(".py")[1].strip()
        i = 6
        while lines[i]:
            i += 1

        args = split_arguments(usage)
        args = read_description_of_arguments(args, lines[6:i])
        return Script(name, script, version, author, args)

    def run_script(self):
        command = f"{self.selected_script.path.absolute()} "

        for i in range(self.command_parts_layout.count()):
            widget = self.command_parts_layout.itemAt(i).widget()
            if isinstance(widget, ArgumentWidget):
                command += widget.get_command() + " "

        print(f"Running {command}")

        self.main_window.trigger_script(command)

    @pyqtSlot(DisplayScriptOptionWidget)
    def add_script(self, widget: DisplayScriptOptionWidget):
        self.selected_script = widget.script
        script_widget = ScriptWidget(self.main_window, widget.script)
        script_widget.delete_signal.connect(self.delete_script)
        assert self.command_parts_layout.count() == 0
        self.command_parts_layout.addWidget(script_widget)

    @pyqtSlot(DisplayArgumentOptionWidget)
    def add_argument(self, widget: DisplayArgumentOptionWidget):
        argument_widget = ArgumentWidget(widget.argument)
        argument_widget.delete_signal.connect(self.delete_argument)
        # Append the argument widget to the buttons layout at the end
        self.command_parts_layout.insertWidget(self.command_parts_layout.count(), argument_widget)

    @pyqtSlot(ArgumentWidget)
    def delete_argument(self, widget: ArgumentWidget):
        self.command_parts_layout.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()

    @pyqtSlot()
    def delete_script(self):
        self.selected_script = None
        # remove all the argument widgets
        while self.command_parts_layout.count():
            item = self.command_parts_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
