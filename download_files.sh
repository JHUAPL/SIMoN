#!/bin/bash

mkdir files
cd files
docker exec mongodb mongofiles --db files list | awk '{print $1}' | xargs -I {} docker exec mongodb mongofiles --db files get {} \
&& docker exec mongodb mongofiles --db files list | awk '{print $1}' | xargs -I {} docker cp mongodb:/{} .

