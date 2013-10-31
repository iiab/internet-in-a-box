#!/usr/bin/env python

import os
import re
import sys
import argparse
import logging
import pickle
from contextlib import closing, nested

from whoosh.index import open_dir

from iiab.zimpy import ZimFile
from iiab.whoosh_search import index_directory_path

DEFAULT_MIME_TYPES = ["text/html", "text/plain"]

logger = logging.getLogger()

def verify_indexes(zim_files, index_dir_base, indexed_count_cache=None, verbose=False):

    missing_indexes = []
    empty_indexes = []

    # Load a dictionary from the index cache file 
    if indexed_count_cache != None:
        if os.path.exists(indexed_count_cache):
            logger.debug("Loading existing indexable count cache: %s" % indexed_count_cache)
            zim_indexable = pickle.load(open(indexed_count_cache, "rb"))
        else:
            logger.debug("Opening new indexable count cache: %s" % indexed_count_cache)
            zim_indexable = {}
    else:
        zim_indexable = None

    for zim_fn in zim_files:
        index_dir = index_directory_path(index_dir_base, zim_fn)

        if not os.path.exists(index_dir):
            missing_indexes.append( (zim_fn, index_dir) )
            continue

        with nested(closing(ZimFile(zim_fn)), closing(open_dir(index_dir))) as (zim_obj, ix):
            logger.debug("Examining ZIM file %s" % zim_fn)

            if ix.is_empty():
                empty_indexes.append( (zim_fn, index_dir) )
                continue

            if zim_indexable != None:
                # Try to find indexable count from cache since it takes
                # awhile to compute these and they never change
                indexed_count = zim_indexable.get(zim_fn, None)
                if indexed_count == None:
                    mime_type_indexes = []
                    for mt_re in DEFAULT_MIME_TYPES:
                        for mt_idx, mt_name in enumerate(zim_obj.mimeTypeList):
                            if re.search(mt_re, mt_name):
                                mime_type_indexes.append(mt_idx)

                    indexed_count = 0
                    logger.debug("Checking indexable against %d articles" % zim_obj.header['articleCount'])
                    for idx in xrange(zim_obj.header['articleCount']):
                        article_info = zim_obj.read_directory_entry_by_index(idx)
                        if article_info['mimetype'] in mime_type_indexes:
                            indexed_count += 1
                    zim_indexable[zim_fn] = indexed_count
    
                    # Store cache of indexable items in zim files
                    pickle.dump(zim_indexable, open(indexed_count_cache, "wb"))

            else:
                indexed_count = None

            ix_count = ix.doc_count()
            zim_count = zim_obj.header['articleCount']

            logging.info("ZIM File: %s" % zim_fn)
            logging.info("Index Dir: %s" % index_dir)
            logging.info("\t%d total in ZIM file" % zim_count)
            if indexed_count != None:
                logging.info("\t%d indexable in ZIM file" % indexed_count)
            logging.info("\t%d in index" % ix_count)
                    
    if len(missing_indexes) > 0:
        logger.info("Missing Index Files")
        logger.info("-------------------")
    for zim_fn, index_dir in missing_indexes:
        logging.info(zim_fn)
        pass

    if len(empty_indexes) > 0:
        logger.info("Index is Empty")
        logger.info("--------------")
    for zim_fn, index_dir in empty_indexes:
        logging.info(index_dir)


def main(argv):
    parser =  argparse.ArgumentParser(description="Checks that Whoosh indexes have the same number of items as their corresponding ZIM file")

    parser.add_argument("zim_files", nargs="+", 
                        help="ZIM files to index")
    parser.add_argument("-i", "--index-dir", dest="index_dir_base", action="store",
                        default="./zim-index",
                        help="The base directory where Woosh indexes are located.")
    parser.add_argument("-c", dest="indexed_count_cache", metavar="FILENAME",
                        help="Count items that would be indexed, not just total files. Specify cache file for counting.")
    parser.add_argument("-v", dest="verbose", action="store_true",
                        help="Turn on verbose logging")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")

    verify_indexes(**args.__dict__)


if __name__ == "__main__":
    main(sys.argv)
