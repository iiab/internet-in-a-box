#!/bin/sh
SYS=/knowledge/sys
SCRIPTS=/knowledge/internet-in-a-box/scripts
cd $SYS
sleep 3
$SCRIPTS/deb-chroot.sh chroot-armel $SCRIPTS/startup.sh

