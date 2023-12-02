#!/bin/bash

uuid=$(blkid /dev/sda -s UUID -o value)

if [ -z "$uuid" ];
then
    echo "Formatting disk, please wait..."
    echo ""

    mkfs -V -F -t ext4 /dev/sda

    uuid=$(blkid /dev/sda -s UUID -o value)
    
    echo "Mounting disk"
    echo ""

    mkdir /backup
    cp /etc/fstab /etc/fstab_bk
    chown delvitech:delvitech /etc/fstab
    echo "UUID=$uuid /backup ext4 errors=remount-ro 0 1" >> /etc/fstab
    chown root:root /etc/fstab
    mount -a

    cd /backup
    rm -r lost+found/
    cp /etc/fstab* .

    echo "Creating backup routine"
    echo ""

    cp ~/work/toolbox/backup_script.sh /backup
    
    echo "BE SURE TO ADD THIS TO: SUDO CRONTAB -E :"
    echo "0 13 * * * /backup/backup_script.sh" 
    echo ""

    echo "Disk created"
else
    echo "Disk already created"
fi
