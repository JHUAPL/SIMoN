#!/bin/bash

MODEL_NAME=$1
YEAR=$2
DB_CONTAINER=${3:-"simon_mongodb"}

JSON_DATA="/"$YEAR"_"$MODEL_NAME".json"

docker start "simon_mongodb"

# retrieve the document from the database and save it as a JSON file
docker exec -it $DB_CONTAINER \
  mongoexport --db broker --collection sub --limit 1 \
    --query "{\"source\": \"$MODEL_NAME\", \"year\": $YEAR}" \
    --out $JSON_DATA

# copy the JSON file from the container to the host
docker cp $DB_CONTAINER:$JSON_DATA .

# delete the JSON file from the container
docker exec -it $DB_CONTAINER rm $JSON_DATA

