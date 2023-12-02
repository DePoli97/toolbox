# README #

First approach to a GUI for running some scripts.

### What is this repository for? ###

* run scripts visually
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

1. make sure to have PyQt installed ( sudo apt-get install python3-pyqt5 )
2. for debug run with: python3 main.py
3. to add new resources use the resource.qrc file and then add them with: pyrcc5 -o resources.py resource.qrc

### How to make a program out of this ###

pip3 install pyinstaller

python3 -m PyInstaller --onefile --name=ToolBox --windowed --add-data="installation:installation" --add-data="maintenance:maintenance" --add-data="clear_disks:clear_disks" --add-data="installation:installation" --add-data="maintenance:maintenance" --add-data="backup:backup" main.py

the compiled file will be under the dist folder
sudo chmod a+x ToolBox

### Qt reference ###
https://doc.qt.io/qtforpython-6/index.html
