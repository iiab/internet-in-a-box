#!/usr/bin/env python
# Optimizes an already existing whoosh index

import os
import sys
import logging
import argparse

from whoosh import index

logger = logging.getLogger()

def optimize_whoosh_index(index_dir):
    logger.info("Optimizing index: %s" % index_dir)
    ix = index.open_dir(index_dir)
    writer = ix.writer()
    writer.commit(optimize=True)

def main(argv):
    parser =  argparse.ArgumentParser(description="Optimizes a whoosh index")

    parser.add_argument("index_dirs", nargs="+", 
                        help="Index directories to optimizes")

    parser.add_argument("-v", dest="verbose", action="store_true",
                        help="Turn on verbose logging")

    args = parser.parse_args()
   
    # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    console = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(console)
 
    # Loop over all index dirs and issue an error if any do not exist,
    # Save trouble of dying when some exist and some do not
    for dir_name in args.index_dirs:
        if not os.path.exists(dir_name):
            parser.error("Index directory does not exist: %s" % dir_name)
    
    # Optimize each of these dirs
    for dir_name in args.index_dirs:
        optimize_whoosh_index(dir_name)

if __name__ == "__main__":
    main(sys.argv)
