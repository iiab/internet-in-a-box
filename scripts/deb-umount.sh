DIR=/mnt/data2/tmp/stable-chroot
umount ${DIR}/proc
umount ${DIR}/sys
umount ${DIR}/dev
umount ${DIR}/dev/pts # important for pacman (for signature check)

