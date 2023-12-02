import os
import sys


# Dictionary of disk devices and their corresponding mount points
disk_devices = {
    "system": "/",
    "ramdisk": "/ramdisk",
    "backup": "/backup"
}

# Get the path to the temporary directory created by PyInstaller or the executable directory
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Define the release directory path
release_directory = "/home/delvitech/work/sapiens-docker-compose/"
