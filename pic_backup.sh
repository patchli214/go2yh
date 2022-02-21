#!/bin/bash
cd /data/go2/go_static
DATE=`date +%Y-%m-%d_%H_%M_%S`
FILENAME="backup_pic_${DATE}.tar.gz"
tar -zcf ${FILENAME} ./users
scp -P 22 ./${FILENAME}  root@172.16.0.135:/data/backup/pic/${FILENAME}
