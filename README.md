Internet In A Box
=================

Humane Informatics LLC Internet In A Box (IIAB)

January 2013

Wikipedia
---------

Use wp-download to download the latest wikipedia dumps for various languages.
There is a wpdownloadrc config file in Heritage/wpdownloadrc

    Edit wpdownloadrc to comment out languages you don't want
    pip install wp-download
    wp-download -c wpdownloadrc /knowledge/data/wikipedia/dumps

Once downloaded, you need to import the wikipedia dump data into mysql
databases and mediawiki installations.  To do this use Heritage/scripts/make_wiki.py 

    sudo scripts/make_wiki.py -p mypassword -r rootpassword ar fr ru vi zh

By default, this script will look for wikipedia dumps as organized by wp-download in /knowledge/data/wikipedia/dumps and select the latest downloaded dump for each language specified on the command line.  It will create mysql databases for each language.  It will create a stand-alone mediawiki installation under /knowledge/processed/wiki/, which should be linked from /var/www/wiki for proper operation.

After this is complete your new wikis should be accessible at http://localhost/wiki/arwiki (for example)


