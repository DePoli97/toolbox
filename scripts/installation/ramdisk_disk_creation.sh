#!/bin/bash

uuid=$(blkid /dev/nvme1n1 -s UUID -o value)

if [ -z "$uuid" ];
then
    echo "Formatting disk, please wait..."
    echo ""

    mkfs -V -F -t ext4 /dev/nvme1n1

    uuid=$(blkid /dev/nvme1n1 -s UUID -o value)

    echo "Mounting disk"
    echo ""

    cp /etc/fstab /etc/fstab_bk
    chown delvitech:delvitech /etc/fstab
    sed -i '/ramdisk/d' /etc/fstab
    echo "UUID=$uuid /ramdisk ext4 errors=remount-ro 0 1" >> /etc/fstab
    chown root:root /etc/fstab
    mount -a

    ./installation/restart_sapiens_acquisition.sh

    cd /ramdisk
    rm -r lost+found/
    cp /etc/fstab* .

    echo "Disk created"
else
    echo "Disk already created"
fi