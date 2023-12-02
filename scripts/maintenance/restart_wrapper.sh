#!/bin/bash

res=$(docker ps -aqf "name=wrapper")

echo "Restarting Wrapper container"
docker restart $res
echo "Wrapper restarted"
