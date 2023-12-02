#!/bin/bash

list=$(docker ps -aqf "name=sapiens-ai")

echo "Restarting all the sapiens-ai containers"

for res in $list
do
   docker restart $res
done

echo "All sapiens-ai restarted"