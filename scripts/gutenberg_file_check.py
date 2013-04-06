#!/usr/bin/env python

import os
import string
import sys
import sqlite3
from argparse import ArgumentParser
from functools import partial

def crawl_files(db, cb):
    cur = db.cursor()
    for (fname,) in cur.execute('SELECT file FROM gutenberg_files;'):
        cb(fname)

def check_exists(root, fname):
    fullpath = os.path.join(root, fname)
    if not os.path.exists(fullpath):
        print fname

def main():
    parser = ArgumentParser()
    parser.add_argument("dbname", 
                      default="gutenberg.db",
                      help="The gutenberg.db SQLite database")
    parser.add_argument("file_root",
                      default="/knowledge/data/gutenberg/",
                      help="The directory root at which gutenberg book files can be found")
    args = parser.parse_args()

    db = sqlite3.connect(args.dbname)
    crawl_files(db, partial(check_exists, args.file_root))

if __name__ == '__main__':
    main()

