#!/usr/bin/env python

import os
import sys
import argparse
import logging

from whoosh.index import open_dir

from iiab.zimpy import ZimFile
from iiab.whoosh_search import index_directory_path

def main(argv):
    parser =  argparse.ArgumentParser(description="Checks that Whoosh indexes have the same number of items as their corresponding ZIM file")

    parser.add_argument("zim_files", nargs="+", 
                        help="ZIM files to index")
    parser.add_argument("-i", "--index-dir", dest="index_dir", action="store",
                        default="./zim-index",
                        help="The base directory where Woosh indexes are located.")
    parser.add_argument("-v", dest="verbose", action="store_true",
                        help="Turn on verbose logging")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")

    for zim_fn in args.zim_files:
        index_dir = index_directory_path(args.index_dir, zim_fn)

        if not os.path.exists(index_dir):
            logging.info("Index does not exist for %s" % zim_fn)
            continue

        zim_obj = ZimFile(zim_fn)
        ix = open_dir(index_dir)

        if ix.is_empty():
            logging.info("Index is empty for %s" % zim_fn)
        else:
            ix_count = ix.doc_count()
            zim_count = zim_obj.header['articleCount']

            logging.debug("ZIM File: %s" % zim_fn)
            logging.debug("Index Dir: %s" % index_dir)
            logging.debug("\t%d in ZIM file" % zim_count)
            logging.debug("\t%d in index" % ix_count)

        ix.close()
        zim_obj.close()


if __name__ == "__main__":
    main(sys.argv)
