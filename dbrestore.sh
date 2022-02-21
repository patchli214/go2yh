#!/bin/bash
cd /data/backup/go
FILENAME=$(ls -tr | tail -1)
unzip ${FILENAME}
mongorestore --drop -d Go Go
rm -rf ./Go