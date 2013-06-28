# REMOVE: OBSOLETE: use zimpy.py instead
# Extract articles from ZIM files using zimdump (for now)
# Must use a patched version of zimdump
# By Braddock Gaskill May 2013

from subprocess import Popen, PIPE
import os
import re

import kiwix
from config import config


def parse_zimdump_line(line):
    line = line.strip()
    g = re.match("([a-z\- ]+): +(.+)", line)
    if g is not None:
        return g.groups()[0], g.groups()[1]
    else:
        return None, None


def parse_zimdump_info(text):
    d = {}
    lines = text.split("\n")
    for line in lines:
        name, value = parse_zimdump_line(line)
        if name is not None:
            d[name] = value
    return d


def get_article_info_by_url(zimfile, namespace, url, cwd='.'):
    name = "X" + namespace + "/" + url
    exe = config().get_path('KIWIX', 'zimdump')
    cmd = [exe,
           '-i', '-u', name,
           zimfile]
    cmd = [x.encode('utf-8') for x in cmd]
    p = Popen(cmd, stdout=PIPE, cwd=cwd)
    data = p.stdout.read()
    if len(data) == 0:
        print "ZERO LENGTH FILE"
        return None
    return parse_zimdump_info(data)


def get_zimfile_info(zimfile, cwd='.'):
    """Return info about the zim file itself"""
    exe = config().get_path('KIWIX', 'zimdump')
    cmd = [exe,
           '-F', '-v',
           zimfile]
    #print string.join(cmd, " ")
    cmd = [x.encode('utf-8') for x in cmd]
    p = Popen(cmd, stdout=PIPE, cwd=cwd)
    data = p.stdout.read()
    info = parse_zimdump_info(data)
    return info


def get_article_info_by_index(zimfile, idx, cwd='.'):
    exe = config().get_path('KIWIX', 'zimdump')
    cmd = [exe,
           '-i', '-o', str(idx),
           zimfile]
    #print string.join(cmd, " ")
    cmd = [x.encode('utf-8') for x in cmd]
    p = Popen(cmd, stdout=PIPE, cwd=cwd)
    data = p.stdout.read()
    if len(data) == 0:
        print "ZERO LENGTH FILE"
        return None
    return parse_zimdump_info(data)


def get_article_data_by_index(zimfile, index, cwd='.'):
    exe = config().get_path('KIWIX', 'zimdump')
    cmd = [exe,
           '-d', '-o', str(index),
           zimfile]
    #print string.join(cmd, " ")
    cmd = [x.encode('utf-8') for x in cmd]
    p = Popen(cmd, stdout=PIPE, cwd=cwd)
    data = p.stdout.read()
    if len(data) == 0:
        print "ZERO LENGTH FILE"
    return data


def get_article_by_url(zimfile, namespace, url, cwd='.'):
    info = get_article_info_by_url(zimfile, namespace, url, cwd=cwd)
    if not bool(int(info.get('redirect'))):
        data = get_article_data_by_index(zimfile, info['idx'], cwd=cwd)
    else:
        data = None
    return data, info


def get_article_by_index(zimfile, idx, cwd='.'):
    info = get_article_info_by_index(zimfile, idx, cwd=cwd)
    if not bool(int(info.get('redirect'))):
        data = get_article_data_by_index(zimfile, info['idx'], cwd=cwd)
    else:
        data = None
    return data, info


def replace_paths(top_url, html):
    replace = u"\\1\\2" + top_url + "/\\3/"
    html = re.sub(u'(href|src)(=["\']/)([A-Z\-])/', replace, html)
    html = re.sub(u'(@import[ ]+)(["\']/)([A-Z\-])/', replace, html)
    return html


class ZimArticle(object):
    def __init__(self, data, info):
        self.data = data
        self.url = info['url']
        self.title = info['title']
        self.idx = int(info['idx'])
        self.namespace = info['namespace']
        self.redirect = bool(int(info['redirect']))
        self.mime_type = info.get('mime-type', None)
        self.size = info.get('article size', None)
        self.redirect_index = info.get('redirect index', None)


class ZimFile(object):
    def __init__(self, book):
        self.book = book

    def get_filename(self):
        kiwix_dir = config().get_path('KIWIX', 'wikipedia_kiwix_dir')
        path = os.path.join(kiwix_dir, self.book['path'])
        return path

    def get_article_by_url(self, namespace, url):
        kiwix_dir = config().get_path('KIWIX', 'wikipedia_kiwix_dir')
        path = self.get_filename()
        data, info = get_article_by_url(path, namespace, url, cwd=kiwix_dir)
        article = ZimArticle(data, info)
        while article.redirect:
            data, info = get_article_by_index(path, article.redirect_index, cwd=kiwix_dir)
            article = ZimArticle(data, info)
        return article

    def get_article_by_index(self, idx):
        kiwix_dir = config().get_path('KIWIX', 'wikipedia_kiwix_dir')
        path = self.get_filename()
        data, info = get_article_by_index(path, idx, cwd=kiwix_dir)
        article = ZimArticle(data, info)
        while article.redirect:
            data, info = get_article_by_index(path, article.redirect_index, cwd=kiwix_dir)
            article = ZimArticle(data, info)
        return article

    def get_info(self):
        kiwix_dir = config().get_path('KIWIX', 'wikipedia_kiwix_dir')
        info = get_zimfile_info(self.get_filename(), cwd=kiwix_dir)
        return info

    def get_main_page(self):
        info = self.get_info()
        return self.get_article_by_index(info.get('main page', 1))


class Library(object):
    def __init__(self, library_filename):
        self.books = kiwix.parse_library(library_filename)
        self.readableToBooks = dict([(x['humanReadableId'], ZimFile(x)) for x in self.books])

    def get_article_by_url(self, humanReadableId, namespace, url):
        zimfile = self.get_zimfile(humanReadableId)
        if zimfile is None:
            return None
        article = zimfile.get_article_by_url(namespace, url)
        return article

    def get_zimfile(self, humanReadableId):
        return self.readableToBooks.get(humanReadableId, None)
