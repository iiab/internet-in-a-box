DIR=/mnt/ssd/expire/stable-chroot
mount -t proc none ${DIR}/proc
mount -t sysfs none ${DIR}/sys
mount -o bind /dev ${DIR}/dev
mount -o bind /dev/pts ${DIR}/dev/pts # important for pacman (for signature check)
chroot ${DIR}
