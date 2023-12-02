#!/bin/bash

list=$(docker ps -aqf "name=align")

echo "Restarting all the aligns containers"

for res in $list
do
   docker restart $res
done

echo "All aligns restarted"