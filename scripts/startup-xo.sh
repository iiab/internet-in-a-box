#!/bin/bash
chmod a+x /run/media/olpc/
mkdir /var/log/nginx
nginx
(cd /knowledge/internet-in-a-box; ./run.py 2>&1 >>/knowledge/sys/iiab.log)
