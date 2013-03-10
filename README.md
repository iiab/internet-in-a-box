Internet In A Box
=================

Humane Informatics LLC Internet In A Box (IIAB)

January 2013

Wikipedia
---------

This section describes how to make a complete Mediawiki-based Wikipedia mirror
for many languages.  This is not necessary if you are using kiwix - see the
section on Kiwiz ZIM File Download instead.

Install:
    apt-get install mysql-server php5 apache2 php5-mysql

First relocate the mysql directory.
    mv /var/lib/mysql /var/lib/mysql.orig
    ln -s /knowledge/processed/mysql /var/lib/mysql

Had to inform AppArmor of the new path (make sure there are no symlinks, or
modify this to provide a full path).
    cat >>/etc/apparmor.d/local/usr.sbin.mysqld  <<EOF
    /knowledge/processed/mysql rwk,
    /knowledge/processed/mysql/** rwk,
    EOF

Use wp-download to download the latest wikipedia dumps for various languages.
There is a wpdownloadrc config file in Heritage/wpdownloadrc

    Edit wpdownloadrc to comment out languages you don't want
    pip install wp-download
    wp-download -c wpdownloadrc /knowledge/data/wikipedia/dumps

Once downloaded, you need to import the wikipedia dump data into mysql
databases and mediawiki installations.  To do this use Heritage/scripts/make_wiki.py 

    sudo scripts/make_wiki.py -p mypassword -r rootpassword ar fr ru vi zh

By default, this script will look for wikipedia dumps as organized by
wp-download in /knowledge/data/wikipedia/dumps and select the latest downloaded
dump for each language specified on the command line.  It will create mysql
databases for each language.  It will create a stand-alone mediawiki
installation under /knowledge/processed/wiki/, which should be linked from
/var/www/wiki for proper operation.

    ln -s /knowledge/processed/wiki /var/www/wiki

After this is complete your new wikis should be accessible at http://localhost/wiki/arwiki (for example)


Kiwix ZIM File Download
-----------------------

1. Install Firefox plugin "Download Them All"
2. http://www.kiwix.org/index.php/Template:ZIMdumps
3. Tools->Download Them All->DownloadThemAll
4. In DTA dialog, open "Fast Filtering"
5. Enter Fast Filter "*.zim.torrent"
6. Start!
7. mv ~/Downloads/*.zim.torrent /knowledge/data/zim/torrents/
8. Open Transmission Bitorrent client
9. Open -> select all *.zim.torrent in file dialog
10. Select download destination /knowledge/data/zim/downloads/


Ubuntu Software Repository
--------------------------

    apt-get install apt-mirror
    apt-mirror scripts/mirror.list
(will mirror into /knowledge/data/ubuntu/12.04)


Project Gutenberg Mirror
------------------------

    cd /knowledge/data/gutenberg  (?)
    while (true); do (date; . ../../Heritage/rsync_gutenberg; sleep 3600) | tee -a 20120823.log; done


Web Service
-----------

    cd Heritage
    pip install Flask-Babel whoosh Flask-SQLAlchemy
    ./run.py


----
