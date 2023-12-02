#!/bin/bash
DATE=$(date +%d-%m-%Y)
BACKUP_DIR=/backup
TEMP_DIR=/backup

{
echo "- COPING DATA FOLDER (except for minio folder) -"
sudo rsync -av /data $BACKUP_DIR$TEMP_DIR --exclude minio/
sudo rsync -av /mnt/cal $BACKUP_DIR$TEMP_DIR
echo "- COMPRESS COPIED DATA FOLDER -"
tar -zcvpf $BACKUP_DIR/backup-$DATE.tar.gz $BACKUP_DIR$TEMP_DIR
echo "- REMOVING COPIED DATA FOLDER -"
rm -r $BACKUP_DIR$TEMP_DIR
echo "- CLEANED -"
} &>log-$DATE.log

# Delete files older than 30 days #
find $BACKUP_DIR/* ! -name 'backup_script.sh' ! -name 'fstab' -mtime +90 -exec rm {} \;
