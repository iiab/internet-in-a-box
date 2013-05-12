#!/bin/bash
chmod a+x /run/media/olpc/
mkdir /var/log/nginx
nginx
(cd /knowledge/internet-in-a-box; ./run.py 2>&1 >>/knowledge/sys/iiab.log) &
#(cd /knowledge/modules/wikipedia-kiwix; /knowledge/sys/bin-arm/kiwix-serve -v --library library.xml --port 25001 2>&1 >>/knowledge/sys/kiwix.log) &
echo "Ready to serve."
