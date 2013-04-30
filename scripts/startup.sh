#!/bin/bash
echo "Hello World!"
killall lighttpd-angel
(cd /knowledge/internet-in-a-box; ./run.py) &
(cd /knowledge/modules/wikipedia-kiwix; /root/repo/kiwix-kiwix/src/server/kiwix-serve -v --library library.xml --port 25001) &
/etc/init.d/nginx start
nginx -s reload
echo "Ready to serve."
bash
