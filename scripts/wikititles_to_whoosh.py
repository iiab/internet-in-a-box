#!/usr/bin/env python
# Internet-In-A-Box by Braddock Gaskill, Feb 2013

import sys
import os
import sqlite3
from optparse import OptionParser
from whoosh.index import create_in, open_dir
from whoosh.fields import TEXT, NUMERIC, Schema
from whoosh.qparser import QueryParser

sys.path.append('.')


def query(ix, searcher, terms):
    """EXAMPLE QUERY USAGE:
        import wikititles_to_whoosh
        from whoosh.index import open_dir
        ix = open_dir("../wikititles_index/")
        searcher = ix.searcher()
        r = wikititles_to_whoosh.query(ix, searcher, u"washington")
        hit=r[0]
        hit.items()
        hit.get('score')
        hit.get('title')
    """
    #ix = open_dir(indexdir)
    #with ix.searcher() as searcher:
    query = QueryParser("title", ix.schema).parse(terms)
    results = searcher.search(query)
    return list(results)


def main(argv):
    parser = OptionParser()
    parser.add_option("--wikititles", dest="wikititles", action="store",
                      default="/knowledge/processed/wikititles.db",
                      help="The wikititles.db SQLite database")
    parser.add_option("--indexdir", dest="indexdir", action="store",
                      default="wikititles_index",
                      help="The output whoosh index directory name")
    (options, args) = parser.parse_args()

    if not os.path.exists(options.wikititles):
        parser.error("wikititles database file does not exist at " + options.wikititles)

    # Create index and schema
    schema = Schema(title=TEXT(stored=True), score=NUMERIC(stored=True))

    if not os.path.exists(options.indexdir):
        os.mkdir(options.indexdir)
    ix = create_in(options.indexdir, schema)

    writer = ix.writer()

    # Plough through the wikipedia titles
    conn = sqlite3.connect(options.wikititles)
    sqlQuery = "select title, reverselinks from article"
    count = 0
    for title, reverseLinks in conn.execute(sqlQuery):
        title = unicode(title)
        writer.add_document(title=title, score=reverseLinks)
        count += 1
        if not count % 1000:
            print count, title
    conn.close()
    writer.commit()


if __name__ == "__main__":
    main(sys.argv)
