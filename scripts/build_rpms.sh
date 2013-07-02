#!/bin/bash
# Create RPMs for Internet-in-a-box
# sudo yum install fedora-packager

if [ ! -d internet-in-a-box/.git ]; then
    echo "Must be run from parent of internet-in-a-box clone"
    exit -1
fi

echo "rsyncing from braddock.com - enter password"
rsync -avrP --delete braddock@braddock.com:public_html/downloads.internet-in-a-box.org/fedora .

if [ ! -e backports.lzma-0.0.2.tar.gz ]; then
    echo "Downloading LZMA..."
    wget https://pypi.python.org/packages/source/b/backports.lzma/backports.lzma-0.0.2.tar.gz
fi

tar xzf backports.lzma-0.0.2.tar.gz
(cd backports-lzma-0.0.2; python setup.py bdist_rpm)

if [ ! -e Whoosh-2.4.1.tar.gz ]; then
    echo "Downloading Whoosh..."
    wget https://pypi.python.org/packages/source/W/Whoosh/Whoosh-2.4.1.tar.gz
fi

tar xzf Whoosh-2.4.1.tar.gz
(cd Whoosh-2.4.1; python setup.py bdist_rpm)

(cd internet-in-a-box; python setup.py bdist_rpm)

#if [ -d fedora ]; then
#    rm -rf fedora
#fi
mkdir -p fedora/18
cp -v */dist/*.rpm fedora/18/
createrepo --verbose fedora/18/

echo "rsyncing to braddock.com - enter password"
rsync -avrP --delete fedora braddock@braddock.com:public_html/downloads.internet-in-a-box.org/
