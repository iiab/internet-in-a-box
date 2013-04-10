if [ -z $1 ]; then
    DIR=/knowledge/processed/chroot-armel
else
    DIR="$1"
fi
echo "DIR=$DIR"
mount -t proc none ${DIR}/proc
mount -t sysfs none ${DIR}/sys
mount -o bind /dev ${DIR}/dev
mount -o bind /dev/pts ${DIR}/dev/pts # important for pacman (for signature check)
mkdir ${DIR}/knowledge
mount -o bind /knowledge ${DIR}/knowledge
#mount -o bind /var/lib/mod_tile ${DIR}/var/lib/mod_tile
SHELL=/bin/bash HOME=/root chroot ${DIR} $2
