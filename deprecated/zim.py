# DEPRECATED:
# zim_views.py now uses ZimFile directly to get file metadata

import re
import os

import kiwix
from zimpy import ZimFile


def replace_paths(top_url, html):
    replace = u"\\1\\2" + top_url + "/\\3/"
    html = re.sub(u'(href|src)(=["\']/)([A-Z\-])/', replace, html)
    html = re.sub(u'(@import[ ]+)(["\']/)([A-Z\-])/', replace, html)
    return html


class Library(object):
    def __init__(self, library_filename):
        self.books = kiwix.parse_library(library_filename)
        self.path = os.path.dirname(library_filename)
        self.readableToBooks = {}
        for book in self.books:
            hid = book['humanReadableId']
            filename = os.path.join(self.path, book['path'])
            self.readableToBooks[hid] = ZimFile(filename)

    def get_article_by_url(self, humanReadableId, namespace, url):
        zimfile = self.get_zimfile(humanReadableId)
        if zimfile is None:
            return None
        article = zimfile.get_article_by_url(namespace, url)
        return article

    def get_zimfile(self, humanReadableId):
        return self.readableToBooks.get(humanReadableId, None)

