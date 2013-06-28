#!/usr/bin/env python
# Uses Woosh and zimpy to Index ZIM files for searching

import sys
import os
import re
import argparse
import logging
from whoosh.index import create_in, open_dir
from whoosh.fields import TEXT, NUMERIC, ID, Schema
from whoosh.qparser import QueryParser

from iiab.zimpy import ZimFile

# Install progress bar package as it is really needed
# to help understand where the processing is
from progressbar import ProgressBar, Percentage, Bar

# For rendering HTML to text for indexing
from html2text import html2text

logger = logging.getLogger()

# Strip these tags that contain text between them that should not be indexed
STRIP_TEXT_TAGS = ["script"]

def remove_html(text):
    soup = BeautifulSoup(text)

    body_tag = soup.find("body")

    # No body in contents of article
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
                        metavar="MIME_TYPE", nargs="*", 
                        default=["text/html", "text/plain"],
                        help="Mimetypes of articles to index")
    parser.add_argument("--no-contents", dest="index_contents", action="store_false",
                        default=True,
                        help="Turn of indexing of article contents")
    parser.add_argument("--memory-limit", dest="memory_limit", action="store",
                        default=256, type=int,
                        help="Set maximum memory in Mb to consume by writer")
    parser.add_argument("--processors", dest="processors", action="store",
                        default=1, type=int,
                        help="Set the number of processors for use by the writer")
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
                    content=TEXT(stored=False),
                    blobNumber=NUMERIC(stored=True),
                    namespace=ID(stored=True),
                    fullUrl=ID,
                    clusterNumber=NUMERIC,
                    mimetype=NUMERIC,
                    parameter=ID,
                    parameterLen=NUMERIC,
                    revision=NUMERIC,)
    logger.debug("Using schema: %s" % schema)

    for zim_file in args.zim_files:
        zim_obj = ZimFile(zim_file)

        logger.info("Indexing: %s" % zim_file)

        if not args.index_contents:
            logger.info("Not indexing article contents")        

        # Figure out which mime type indexes from this file we will use
        logger.debug("All mime type names: %s" % zim_obj.mimeTypeList)
        logger.info("Using mime types:")
        mime_type_indexes = []
        for mt_re in args.mime_types:
            for mt_idx, mt_name in enumerate(zim_obj.mimeTypeList):
                if re.search(mt_re, mt_name):
                    mime_type_indexes.append(mt_idx)
                    logger.info(mt_name)

        index_dir = os.path.join(args.output_dir, os.path.splitext(os.path.basename(zim_file))[0])
        if not os.path.exists(index_dir):
            logger.debug("Creating index directory: %s" % index_dir)
            os.mkdir(index_dir)

        ix = create_in(index_dir, schema)
        writer = ix.writer(limitmb=args.memory_limit, proc=args.processors)

        # Get the analyzer object from a text field
        stem_ana = writer.schema["content"].analyzer
        # Set the cachesize to -1 to indicate unbounded caching
        # to speed up batch processing
        stem_ana.cachesize = -1

        pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=zim_obj.header['articleCount']).start()

        for idx, article_info in enumerate(zim_obj.articles()):
            # Skip articles of undesired mime types
            if article_info['mimetype'] not in mime_type_indexes:
                continue

            if args.index_contents:
                raw_content = zim_obj.get_article_by_index(idx)[0]
            
                try:
                    content = raw_content.decode("utf-8")
                except:
                    content = raw_content.decode("latin1")
                
                # Strip out HTML so it is not indexed
                # It also converts to unicode in the process
                # Only do the stripping on HTML article types
                if "html" in zim_obj.mimeTypeList[article_info['mimetype']]:
                    content = html2text(content)
            else:
                content = None

            # Make any strings into unicode objects
            for k,v in article_info.items():
                if type(v) is str:
                    article_info[k] = unicode(v)

            writer.add_document(content=content, **article_info)


            pbar.update(idx+1)

        pbar.finish()

        logger.info("Commiting index")
        writer.commit()
        zim_obj.close()


if __name__ == "__main__":
    main(sys.argv)
