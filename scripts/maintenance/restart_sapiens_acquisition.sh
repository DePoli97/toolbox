#!/bin/bash

res=$(docker ps -aqf "name=acquisition")

echo "Restarting sapiens-acquisition container"
docker restart $res
echo "Acquisition restarted"
