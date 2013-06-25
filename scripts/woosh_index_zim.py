#!/usr/bin/env python
# Uses Woosh and zimpy to Index ZIM files for searching

import sys
import os
import argparse
import logging
from whoosh.index import create_in, open_dir
from whoosh.fields import TEXT, NUMERIC, ID, Schema
from whoosh.qparser import QueryParser

from iiab.zimpy import ZimFile

# Install progress bar package as it is really needed
# to help understand where the processing is
from progressbar import ProgressBar, Percentage, Bar

# For stripping out html tags
from BeautifulSoup import BeautifulSoup

logger = logging.getLogger()

# Strip these tags that contain text between them that should not be indexed
STRIP_TEXT_TAGS = ["script"]

def remove_html(text):
    soup = BeautifulSoup(text)

    body_tag = soup.find("body")

    # No body contents in article
    if body_tag == None:
        return u''

    # Remove script tags since they contain "text"
    for strip_tag_name in STRIP_TEXT_TAGS:
        tag_find = body_tag.findAll(STRIP_TEXT_TAGS)
        if tag_find != None:
            for script_tag in tag_find:
                script_tag.replaceWith("")

    return body_tag.findAll(text=True)

def main(argv):
    parser =  argparse.ArgumentParser(description="Indexes the contents of a ZIM file using Woosh")
    parser.add_argument("zim_files", nargs="+", 
                        help="ZIM files to index")
    parser.add_argument("-o", "--output-dir", dest="output_dir", action="store",
                        default="./zim-index",
                        help="The base directory where Woosh indexes are written. One sub directory per file.")
    parser.add_argument("-m", "--mime-types", dest="mime_types",
                        metavar="INT", nargs="*", default=[0,6],
                        help="Mimetypes of articles to index")
    parser.add_argument("--no-contents", dest="index_contents", action="store_false",
                        default=True,
                        help="Turn of indexing of article contents")
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

    # Create base directory for indexes
    if not os.path.exists(args.output_dir):
        logger.debug("Creating output dir: %s" % args.output_dir)
        os.mkdir(args.output_dir)

    # Create schema use by all indexes
    schema = Schema(title=TEXT(stored=True), 
                    url=ID(stored=True),
                    contents=TEXT(stored=False),
                    blobNumber=NUMERIC(stored=True),
                    fullUrl=ID,
                    clusterNumber=NUMERIC,
                    mimetype=NUMERIC,
                    namespace=ID,
                    parameter=ID,
                    parameterLen=NUMERIC,
                    revision=NUMERIC,)
    logger.debug("Using schema: %s" % schema)

    for zim_file in args.zim_files:
        zim_obj = ZimFile(zim_file)

        logger.info("Indexing: %s" % zim_file)

        if not args.index_contents:
            logger.info("Not indexing article contents")        

        logger.info("Using mime types: %s" % [ zim_obj.mimeTypeList[i] for i in args.mime_types ])

        index_dir = os.path.join(args.output_dir, os.path.splitext(os.path.basename(zim_file))[0])
        if not os.path.exists(index_dir):
            logger.debug("Creating index directory: %s" % index_dir)
            os.mkdir(index_dir)

        ix = create_in(index_dir, schema)
        writer = ix.writer()

        pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=zim_obj.header['articleCount']).start()

        for idx, article_info in enumerate(zim_obj.articles()):
            # Skip articles of undesired mime types
            if article_info['mimetype'] not in args.mime_types:
                continue

            if args.index_contents:
                # Strip out HTML so it is not indexed
                # It also converts to unicode in the process
                # Only do the stripping on HTML article types
                raw_contents = zim_obj.get_article_by_index(article_info['blobNumber'])[0]
                if "html" in zim_obj.mimeTypeList[article_info['mimetype']]:
                    contents = remove_html(raw_contents)
                else:
                    contents = unicode(raw_contents)

            else:
                contents = None

            # Make any strings into unicode objects
            for k,v in article_info.items():
                if type(v) is str:
                    article_info[k] = unicode(v)
            writer.add_document(contents=contents, **article_info)


            pbar.update(idx+1)

        pbar.finish()
        writer.commit()
        zim_obj.close()


if __name__ == "__main__":
    main(sys.argv)
