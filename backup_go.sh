#!/bin/bash
cd /data/backup/go
DATE=`date +%Y-%m-%d_%H_%M_%S`
FILENAME2="backup_Go_${DATE}"
mongodump -d Go -o ./
zip ./"${FILENAME2}.zip" -r  ./Go
rm -rf ./Go
scp -P 22 ./${FILENAME2}.zip  root@172.16.182.142:/data/backup/go/${FILENAME2}.zip
