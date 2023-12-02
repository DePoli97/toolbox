#!/bin/bash

res=$(docker ps -aqf "name=calibration")

echo "Restarting calibration container"
docker restart $res
echo "Calibration restarted"
