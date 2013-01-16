DIR=/mnt/sdc1/expire/chroot
umount ${DIR}/proc
umount ${DIR}/sys
umount ${DIR}/dev
umount ${DIR}/dev/pts # important for pacman (for signature check)
umount ${DIR}/knowledge
umount ${DIR}/var/lib/mod_tile
