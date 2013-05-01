#!/bin/bash
killall lighttpd-angel
(cd /knowledge/internet-in-a-box; ./run.py 2>&1 >>/knowledge/sys/iiab.log) &
(cd /knowledge/modules/wikipedia-kiwix; /knowledge/sys/bin-arm/kiwix-serve-patched -v --library library.xml --port 25001 2>&1 >>/knowledge/sys/kiwix.log) &
/etc/init.d/nginx start
nginx -s reload
echo "Ready to serve."
