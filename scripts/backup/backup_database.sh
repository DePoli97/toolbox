#!/bin/bash

echo "Creating {DB_NAME} backup"
echo ""

mysqldump -u root --password=supersecure --port=3307 --host=127.0.0.1 {DB_NAME} > {DESTINATION}

echo ""
echo "{DB_NAME} backup created"