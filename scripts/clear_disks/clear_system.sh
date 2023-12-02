#!/bin/bash

echo "Cleaning disk, please wait... (only unused docker images will be cleaned)"
echo ""

docker system prune -a -f

echo ""
echo "Disk cleaned"