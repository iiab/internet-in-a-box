#!/usr/bin/env python

#from xml.etree import ElementTree as etree
# lxml is 10 times faster than ElementTree
from lxml import etree
from base64 import b64decode
import iso639
import os


def getHumanReadableBookId(path):
    """Gets the human readable id for a book from the book's path.
    Uses same technique as kiwix."""
    hid = os.path.basename(path)
    hid = os.path.splitext(hid)[0]
    hid = hid.replace(" ", "_")
    hid = hid.replace("+", "plus")
    return hid


def clean_book(book):
    """Fixes up the book data"""
    book2 = {}
    for k, v in book.items():
        if k == "favicon":
            v = b64decode(v)
        elif k == "articleCount":
            v = int(v)
            book2['articleCountString'] = "{:,}".format(v)
        elif k == "mediaCount":
            v = int(v)
        elif k == "size":
            v = int(v)
        elif k == "language":
            if v == 'en':  # Mislabel, replace with 3-letter label
                v = 'eng'
            if v in iso639.iso6392:
                book2["languageEnglish"] = iso639.iso6392[v]['english']
            else:
                book2["languageEnglish"] = v
        book2[k] = v
    if 'language' not in book2:
        title = book2.get('title', '')
        if title.find(" ml ") != -1:
            lang = 'mal'
        elif title.find(" zh ") != -1:
            lang = 'zho'
        else:
            # Assume english
            lang = 'eng'
        book2['language'] = lang
        book2['languageEnglish'] = iso639.iso6392[lang]['english']
    hid = getHumanReadableBookId(book2['path'])
    book2['humanReadableId'] = hid
    return book2


def parse_library(library_xml_filename):
    """Parse a kiwix library xml file"""
    with open(library_xml_filename, "r") as f:
        et = etree.parse(f)
        root = et.getroot()
        books = root.findall("book")
    books = map(clean_book, books)
    return books


def get_languages(library):
    """Get a list of all unique languages found in the library,
    sorted in decreasing order of total number of articles in that language"""
    langs = dict()
    for book in library:
        lang = book['language']
        langEng = book['languageEnglish']
        articles = book['articleCount']
        books = []
        if lang in langs:
            articles += langs[lang].get('articleCount', 0)
            books = langs[lang].get('books', [])
        books.append(book)
        langs[lang] = {
            'language': lang,
            'languageEnglish': langEng,
            'articleCount': articles,
            'books': books
        }
    langs = langs.values()
    langs.sort(key=lambda x: -x['articleCount'])
    return langs
