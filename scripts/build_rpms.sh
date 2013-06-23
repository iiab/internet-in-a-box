#!/bin/bash
# Create RPMs for Internet-in-a-box
# sudo yum install fedora-packager

if [ ! -d internet-in-a-box/.git ]; then
    echo "Must be run from parent of internet-in-a-box clone"
    exit -1
fi

if [ ! -e Whoosh-2.4.1.tar.gz ]; then
    echo "Downloading Whoosh..."
    wget https://pypi.python.org/packages/source/W/Whoosh/Whoosh-2.4.1.tar.gz
fi

tar xzf Whoosh-2.4.1.tar.gz
(cd Whoosh-2.4.1; python setup.py bdist_rpm)

(cd internet-in-a-box; python setup.py bdist_rpm)

if [ -d fedora ]; then
    rm -rf fedora
fi
mkdir -p fedora/18
cp -v */dist/*.rpm fedora/18/
createrepo --verbose fedora/18/

echo "rsyncing to braddock.com - enter password"
rsync -avrP --delete fedora braddock@braddock.com:public_html/downloads.internet-in-a-box.org/
