DIR=/mnt/sdc1/expire/chroot
mount -t proc none ${DIR}/proc
mount -t sysfs none ${DIR}/sys
mount -o bind /dev ${DIR}/dev
mount -o bind /dev/pts ${DIR}/dev/pts # important for pacman (for signature check)
mkdir ${DIR}/knowledge
mount -o bind /public2/knowledge ${DIR}/knowledge
mount -o bind /var/lib/mod_tile ${DIR}/var/lib/mod_tile
chroot ${DIR}
