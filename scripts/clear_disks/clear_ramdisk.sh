#!/bin/bash

echo "Cleaning disk, please wait..."

find /ramdisk -mindepth 1 ! -regex '^./ramdisk/background\(/.*\)?' -delete
./installation/restart_sapiens_acquisition.sh

echo ""
echo "Disk cleaned"