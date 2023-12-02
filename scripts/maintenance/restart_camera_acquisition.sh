#!/bin/bash

res=$(docker ps -aqf "name=acq_microservice")

echo "Stopping acq_microservice"
docker stop $res

echo "Stopping Syncboard"
~/work/syncboard/36.reboot_syncboard.sh

echo "Reloading camera driver"
# sudo ~/work/acq_microservice/drivers/daxpylh/unload_driver -- don't do this, can crash the kernel
sudo ~/work/acq_microservice/drivers/daxpylh/load_driver

echo "Acquisition restarted"
docker start $res

sleep 60
echo "Done"
