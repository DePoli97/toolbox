#!/bin/bash

echo "Updating {DB_NAME}"
echo ""

mysql -u root --password=supersecure --port=3307 --host=127.0.0.1 -e "CREATE DATABASE IF NOT EXISTS {DB_NAME};"
echo ""
mysql -u root --password=supersecure --port=3307 --host=127.0.0.1 {DB_NAME} < {ORIGIN}

echo ""
echo "{DB_NAME} updated"