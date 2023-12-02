#!/bin/bash

res=$(docker ps -aqf "name=hardware")

echo "Restarting hardware container"
docker restart $res
echo "Hardware restarted"
