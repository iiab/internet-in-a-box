from subprocess import Popen, PIPE
import os
import re
import string

import kiwix
from config import config


def get_article_by_url(zimfile, namespace, url, cwd='.'):
    name = namespace + "/" + url
    cmd = ['zimdump',
           '-d', '-u', name,
           zimfile]
    print string.join(cmd, " ")
    p = Popen(cmd, stdout=PIPE, cwd=cwd)
    data = p.stdout.read()
    if len(data) == 0:
        print "ZERO LENGTH FILE"
    data = data.decode('utf-8')
    return data


def replace_paths(top_url, html):
    replace = u"\\1\\2" + top_url + "/\\3/"
    html = re.sub(  u'(href|src)(=["\']/)([A-Z\-])/', replace, html)
    html = re.sub(u'(@import[ ]+)(["\']/)([A-Z\-])/', replace, html)
    return html


class ZimFile(object):
    def __init__(self, book):
        self.book = book

    def get_article_by_url(self, namespace, url):
        kiwix_dir = config().get('KIWIX', 'wikipedia_kiwix_dir')
        path = os.path.join(kiwix_dir, self.book['path'])
        return get_article_by_url(path, namespace, url, cwd=kiwix_dir)


class Library(object):
    def __init__(self, library_filename):
        self.books = kiwix.parse_library(library_filename)
        self.readableToBooks = dict([(x['humanReadableId'], ZimFile(x)) for x in self.books])

    def get_article_by_url(self, humanReadableId, namespace, url):
        print "URL: " + namespace + "/" + url
        zimfile = self.readableToBooks.get(humanReadableId, None)
        if zimfile is None:
            return None
        data = zimfile.get_article_by_url(namespace, url)
        return data
