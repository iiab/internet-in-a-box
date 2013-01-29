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
import re
from time import time


options = None


def call2(cmd):
    print "CALL: " + string.join(cmd, ' ')
    call(cmd)


def assert_exists(filename):
    if not os.path.exists(filename):
        print 'ERROR: ' + filename + ' does not exist'
        exit(-1)


def find_latest_dump(dump_dir, lang):
    assert_exists(dump_dir)
    lang_dir = os.path.join(dump_dir, lang)
    assert_exists(lang_dir)
    filenames = [int(x) for x in os.listdir(lang_dir) if re.match('[0-9]{8}', x)]
    if len(filenames) == 0:
        msg = "ERROR: " + lang_dir + " contains no valid dated subdirectories"
        raise Exception(msg)
    dates = sorted(filenames)
    target = lang + "wiki-" + str(dates[-1]) + "-pages-articles.xml.bz2"
    path = os.path.join(lang_dir, str(dates[-1]), target)
    assert_exists(path)
    print "Latest " + lang + " dump is " + path
    return path, dates[-1]


def write_version(path, version):
    f = open(os.path.join(path, "WIKI_VERSION"), "w")
    f.write(str(version))
    f.close()


def process(language):
    global options
    print "Processing " + language
    # Define paths
    dump_path = os.path.join(options.knowledge, "data", "wikipedia", "dumps")
    if not options.xml:
        xml, xml_date = find_latest_dump(dump_path, language)
    else:
        assert_exists(options.xml)
        xml = options.xml
        xml_date = None
    packages = os.path.join(options.knowledge, "packages")
    dbname = language + 'wiki'
    wikidir = os.path.join(options.destination, dbname)
    extensions_dir = os.path.join(wikidir, 'extensions')
    local_settings = os.path.join(wikidir, 'LocalSettings.php')
    mobile = "wikimedia-mediawiki-extensions-MobileFrontend-eeb4f48"
    mobile_tarball = os.path.join(packages, mobile + ".tar.gz")
    assert_exists(mobile_tarball)
    cite = "wikimedia-mediawiki-extensions-Cite-aa635f0"
    cite_tarball = os.path.join(packages, cite + ".tar.gz")
    assert_exists(cite_tarball)

    # We use mediawiki-extensions package, even though we don't use mediawiki
    call2(['apt-get', 'install', 'mediawiki-extensions'])

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
        if options.force:
            call2(['rm', '-r', untardir])
        else:
            print "ERROR: " + untardir + " already exists, refusing to proceed"
            sys.exit(-2)
    if os.path.exists(wikidir):
        if options.force:
            call2(['rm', '-r', wikidir])
        else:
            print "ERROR: " + wikidir + " already exists, refusing to proceed"
            sys.exit(-2)
    call2(['tar', '-C', options.destination, '-xzf', options.mediawiki])
    os.rename(os.path.join(options.destination, 'mediawiki-1.20.2'), wikidir)

    # Install wikimedia MobileFrontend extension
    # NOTE: git version is incompatible with 1.20.2
    #call2(['git', 'clone', '--branch', 'production',
    #       'https://gerrit.wikimedia.org/r/p/mediawiki/extensions/MobileFrontend.git',
    #       os.path.join(extensions_dir, 'MobileFrontend')])
    call2(['tar', '-C', extensions_dir, '-xzf', mobile_tarball])
    os.rename(os.path.join(extensions_dir, mobile),
              os.path.join(extensions_dir, "MobileFrontend"))

    # Install Cite extension
    call2(['tar', '-C', extensions_dir, '-xzf', cite_tarball])
    os.rename(os.path.join(extensions_dir, cite),
              os.path.join(extensions_dir, "Cite"))

    # Configure mediawiki
    os.chdir(wikidir)
    call2(['php', 'maintenance/install.php', '--wiki', 'Wikipedia',
           '--dbuser', options.user, '--dbpass', options.password,
           '--pass', options.password,
           '--dbname', dbname,
           #'--lang', language,
           '--lang', 'en',
           '--scriptpath', '/wiki/' + dbname,
           'Wikipedia', options.user])

    # We must remove the $wgServer setting which defaults to localhost
    os.rename(local_settings, local_settings + ".bak")
    fin = open(local_settings + ".bak", "r")
    fout = open(local_settings, "w")
    for line in fin:
        if string.find(line, '$wgServer ') == 0:
            line = '# ' + line
        fout.write(line)

    # We must include ParserFunctions
    fout.write('\nrequire_once( "$IP/extensions/ParserFunctions/ParserFunctions.php" );\n')

    # Cite processes <ref> tags. We assume apt-get install mediawiki-extensions
    fout.write('require_once( "$IP/extensions/Cite/Cite.php" );\n')

    # Mobile front end configuration
    fout.write('require_once( "$IP/extensions/MobileFrontend/MobileFrontend.php" );\n')
    fout.write('# Force mobile view for all devices because mobile device detection is hard\n')
    fout.write('$context = MobileContext::singleton();\n')
    fout.write('$context->setForceMobileView(true);\n')

    # We must set the meta name
    #fout.write('$wgMetaNamespace = "Wikipedia";\n')
    fin.close()
    fout.close()

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

    # Write database version to WIKI_VERSION file
    if xml_date is not None:
        write_version(wikidir, xml_date)
    else:
        write_version(wikidir, xml)

    # Import XML Dump file
    sqlonly = False
    if sqlonly:
        cmd = ["java -cp /usr/share/java/commons-compress-1.2.jar:/knowledge/packages/mwdumper-1.16.jar",
               "org.mediawiki.dumper.Dumper '" + xml + "' --format=sql:1.5",
               ">/tmp/sql"]
    else:
        cmd = ["java -cp /usr/share/java/commons-compress-1.2.jar:/knowledge/packages/mwdumper-1.16.jar",
               "org.mediawiki.dumper.Dumper '" + xml + "' --format=sql:1.5",
               "| mysql -u " + options.user + " --password=" + options.password + " " + dbname]
    cmd = string.join(cmd, ' ')
    print cmd
    t0 = time()
    call(cmd, shell=True)
    print language + " mwimport time = " + str(time() - t0) + " seconds"


parser = OptionParser()
parser.add_option("-d", "--destination",
                  help="Apache destination directory",
                  default="/knowledge/processed/wiki")
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
parser.add_option("-f", "--force", action="store_true", default=False,
                  help="Force install - delete any existing install and reinstall")
parser.add_option("-a", "--all", action="store_true", default=False,
                  help="Process all available languages")


# Validate options
(options, languages) = parser.parse_args()
if len(languages) and options.all:
    parser.error("ERROR: languages cannot be specified if -a/--all flag is given")
if len(languages) == 0 and not options.all:
    parser.error('Language(s) not given')
if options.all:
    dump_path = os.path.join(options.knowledge, "data", "wikipedia", "dumps")
    languages = list(os.listdir(dump_path))
if not options.password:
    parser.error('MySQL password not given (-p)')
if not options.rootpassword:
    parser.error('MySQL password not given for MySQL root (-r)')
if not options.mediawiki:
    options.mediawiki = os.path.join(options.knowledge, "packages", "mediawiki-1.20.2.tar.gz")
assert_exists(options.knowledge)
assert_exists(options.destination)

# Do initial check of languages
dump_path = os.path.join(options.knowledge, "data", "wikipedia", "dumps")
for language in languages:
    # Do I have a data dump
    dump_file, date = find_latest_dump(dump_path, language)
    # Does the target directory already exist
    dbname = language + 'wiki'
    wikidir = os.path.join(options.destination, dbname)
    if os.path.exists(wikidir):
        print "ERROR: " + wikidir + " already exists.  Delete it to continue"
        exit(-3)

for language in languages:
    process(language)
