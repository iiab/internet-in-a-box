#!/usr/bin/env python

from xml.etree import ElementTree as etree
from base64 import b64decode
import iso639
import os

def clean_book(book):
    """Fixes up the book data"""
    clean_book = {}
    for k, v in book.items():
        if k == "favicon":
            v = b64decode(v)
        elif k == "mediaCount":
            v = int(v)
        elif k == "size":
            v = int(v)
        elif k == "language":
            if v == 'en':  # Mislabel, replace with 3-letter label
                v = 'eng'
            if v in iso639.iso6392:
                clean_book["languageEnglish"] = iso639.iso6392[v]['english']
            else:
                clean_book["languageEnglish"] = v
        clean_book[k] = v
    if 'language' not in clean_book:
        title = clean_book.get('title', '')
        if title.find(" ml ") != -1:
            lang = 'mal'
        elif title.find(" zh ") != -1:
            lang = 'zho'
        else:
            # Assume english
            lang = 'eng'
        clean_book['language'] = lang
        clean_book['languageEnglish'] = iso639.iso6392[lang]['english']
    return clean_book


class Library(object):
    def __init__(self, xml_filename):
        self.books = {}
        self._parse_library(xml_filename)

    def _parse_library(self, library_xml_filename):
        """Parse a kiwix library xml file"""
        with open(library_xml_filename, "r") as f:
            et = etree.parse(f)
            root = et.getroot()
            self.books = root.findall("book")
        self.books = map(clean_book, self.books)

    def find_by_uuid(self, uuid):
        for book in self.books:
            if book['id'] == uuid:
                return book
        return None

    def books_by_language(self):
        """Get a list of all unique languages found in the library,
        sorted in decreasing order of total number of articles in that language"""
        langs = dict()
        for book in library:
            lang = book['language']
            langEng = book['languageEnglish']
            articles = book['articleCount']
            self.books = []
            if lang in langs:
                articles += langs[lang].get('articleCount', 0)
                self.books = langs[lang].get('self.books', [])
            self.books.append(book)
            langs[lang] = {
                'language': lang,
                'languageEnglish': langEng,
                'articleCount': articles,
                'self.books': self.books
            }
        langs = langs.values()
        langs.sort(key=lambda x: -x['articleCount'])
        return langs
