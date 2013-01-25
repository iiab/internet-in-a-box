#!/usr/bin/env python
"""Script to process a Wikipedia dump.
By Braddock Gaskill, 22 Jan 2013

EXAMPLE USAGE:
    sudo scripts/make_wiki.py -l es -u wikimirror \
            -p wikimirror -r 'whatever' \
            -x /knowledge/data/wikipedia/eswiki-20121227-pages-articles.xml.bz2
"""

from subprocess import Popen, PIPE, call
from optparse import OptionParser
import string
import os
import sys
from time import time


def call2(cmd):
    print "CALL: " + string.join(cmd, ' ')
    call(cmd)


parser = OptionParser()
parser.add_option("-l", "--language",
                  help="Language code for wiki")
parser.add_option("-d", "--destination",
                  help="Apache destination directory",
                  default="/var/www")
parser.add_option("-u", "--user",
                  help="MySQL user name",
                  default="wikimirror")
parser.add_option("-p", "--password",
                  help="MySQL password for user")
parser.add_option("-r", "--rootpassword",
                  help="MySQL password for root")
parser.add_option("-x", "--xml",
                  help="Wikipedia XML bz2 dump file")
parser.add_option("-k", "--knowledge",
                  help="Knowledge directory",
                  default="/knowledge")
parser.add_option("--mediawiki",
                  help="Location of mediawiki tarball")

(options, args) = parser.parse_args()
if not options.language:
    parser.error('Language not given (-l)')
if not options.password:
    parser.error('MySQL password not given (-p)')
if not options.rootpassword:
    parser.error('MySQL password not given for MySQL root (-r)')
if not options.xml:
    parser.error('XML xml file not given (-d)')
if not options.mediawiki:
    options.mediawiki = os.path.join(options.knowledge, "packages", "mediawiki-1.20.2.tar.gz")
if not os.path.exists(options.knowledge):
    print 'ERROR: ' + options.knowledge + " does not exist"
    sys.exit(-1)
if not os.path.exists(options.destination):
    print 'ERROR: ' + options.destination + " does not exist"
    sys.exit(-1)
if not os.path.exists(options.xml):
    print 'ERROR: ' + options.xml + " does not exist"
    sys.exit(-1)

dbname = options.language + 'wiki'
wikidir = os.path.join(options.destination, dbname)

# Drop and create new user and database
p = Popen(['mysql', '-u', 'root',
           '--password=' + options.rootpassword],
          stdin=PIPE)
#       "GRANT USAGE ON *.* TO '" + options.user + "'@'localhost';",
#       "DROP USER '" + options.user + "'@'localhost';",
#       "CREATE USER '" + options.user + "'@'localhost' IDENTIFIED BY '"
#       + options.password + "';",
sql = ["DROP DATABASE IF EXISTS " + dbname + ";",
       "CREATE DATABASE " + dbname + ";",
       "GRANT USAGE ON * . * TO '" + options.user + "'@'localhost' IDENTIFIED BY '"
       + options.password + "' WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0 MAX_USER_CONNECTIONS 0;",
       "GRANT ALL PRIVILEGES ON " + dbname + ".* TO '" + options.user + "'@'localhost' WITH GRANT OPTION;"
       ]
sql = string.join(sql, "\n")
p.communicate(sql)
p.wait()

# Install wikimedia
untardir = os.path.join(options.destination, 'mediawiki-1.20.2')
if os.path.exists(untardir):
    print "ERROR: " + untardir + " already exists, refusing to proceed"
    sys.exit(-2)
    #call2(['rm', '-r', untardir])
if os.path.exists(wikidir):
    print "ERROR: " + wikidir + " already exists, refusing to proceed"
    sys.exit(-2)
    #call2(['rm', '-r', wikidir])
call2(['tar', '-C', options.destination, '-xzf', options.mediawiki])
os.rename(os.path.join(options.destination, 'mediawiki-1.20.2'), wikidir)

# Configure mediawiki
os.chdir(wikidir)
call2(['php', 'maintenance/install.php', '--wiki', 'Wikipedia',
       '--dbuser', options.user, '--dbpass', options.password,
       '--pass', options.password,
       '--dbname', dbname, '--lang', 'en',
       '--scriptpath', '/' + dbname,
       dbname, options.user])
call2(['chown', '-R', 'www-data.www-data', wikidir])

# Clean up tables created by MediaWiki install
# This solves duplicate key errors
p = Popen(['mysql', '-u', options.user,
           '--password=' + options.password, dbname],
           stdin=PIPE)
sql = ['DELETE FROM page;',
       'DELETE FROM text;']
sql = string.join(sql, "\n")
p.communicate(sql)
p.wait()

# Import XML Dump file
cmd = ["java -cp /usr/share/java/commons-compress-1.2.jar:/knowledge/packages/mwdumper-1.16.jar",
       "org.mediawiki.dumper.Dumper '" + options.xml + "' --format=sql:1.5",
       "| mysql -u " + options.user + " --password=" + options.password + " eswiki"]
cmd = string.join(cmd, ' ')
print cmd
t0 = time()
call(cmd, shell=True)
print "mwimport time = " + str(time() - t0) + " seconds"
