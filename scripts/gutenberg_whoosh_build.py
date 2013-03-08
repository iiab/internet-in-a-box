#!/usr/bin/env python

import sys
import os
import sqlite3
from whoosh.index import create_in
import whoosh.fields as wf
from whoosh.fields import ID, TEXT, KEYWORD, STORED
import gutenberg_rdf_parser
from argparse import ArgumentParser
from gutenberg_filter import GutenbergIndexFilter


def test_query(indexdir, terms):
    from whoosh.index import open_dir
    from whoosh.qparser import QueryParser
    SEARCH_FIELD = "title"
    whoosh_index = open_dir(indexdir)
    with whoosh_index.searcher() as searcher:
        query = QueryParser(SEARCH_FIELD, whoosh_index.schema).parse(terms)
        results = searcher.search(query)
        return [r.items() for r in results]
        #return [dict(r.items()) for r in results]


def get_schema():
    # Whoosh schema - for ease of use match names with record keys used in gutenberg_rdf_parser
    # Spelling attribute will cause columns to be used as source of query correction suggestions
    return wf.Schema(textId=ID(unique=True, stored=True),
        title=TEXT(stored=True, spelling=True), 
        creator=TEXT(stored=True, spelling=True), 
        creator_id=STORED,
        contributor=TEXT(spelling=True), 
        contributor_id=STORED,
        subject=KEYWORD, 
        language=KEYWORD,
        friendlytitle=TEXT,
        category=STORED
        )


def create_gutenberg_index_rdf(bz2_rdf_filename, indexdir):
    """Build whoosh index from parsed RDF.
    DB contents are no longer identical to RDF output. Plus index now stores selected db row ids.
    DEPRECATED"""
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

    print "WARNING: direct use of rdf content may not accurately reflect database contents"

    schema = get_schema()
    whoosh_index = create_in(indexdir, schema)
    writer = whoosh_index.writer()
    for count, record in enumerate(gutenberg_rdf_parser.parse_rdf_bz2(bz2_rdf_filename, GutenbergIndexFilter().filter)):
        # Only index fields from description records. File records can be ignored.
        if record['record_type'] == 'DESCRIPTION':
            if count % 5000 == 0:
                print count,
            subset = {k : record[k] for k in schema.names() if k in record}
            writer.add_document(**subset)
    print "committing...",
    writer.commit()
    print "DONE"

def create_gutenberg_index_db(dbname, indexdir):
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout
    schema = get_schema()
    whoosh_index = create_in(indexdir, schema)
    writer = whoosh_index.writer()

    db = sqlite3.connect(dbname)
    book_cursor = db.cursor()
    aux_cursor = db.cursor()

    def sel_aux(aux_table, aux_col):
        """Build select table for aux table"""
        return 'SELECT AUX.id, AUX.%s from %s as AUX, gutenberg_books_%s_map AS MAP where MAP.book_id=:textId and AUX.id=MAP.%s_id' % (aux_col, aux_table, aux_col, aux_col)
    def row_to_rec(row):
        """Convert row from sql select response to dictionary"""
        keys = ['textId', 'title', 'friendlytitle', 'creator', 'contributor', 'category', 'subject', 'language']
        return dict(zip(keys, row))
    def resultset_to_keyval(sqlset):
        """
        :param sqlset: list of tuples (id, value)
        :returns: tuple of two lists (list of ids, list of values)
        """
        d = dict(sqlset)
        return (d.keys(), d.values())
        
    for count, row in enumerate(book_cursor.execute('SELECT * from gutenberg_books;')):
        record = row_to_rec(row)
        textId_dict = { 'textId' : record['textId'] } # separate dict because extra, unused keys causes error during binding
        # Even single column results come in a tuple [(..,),(..,),..].
        # Multiple select statements instead of one because want a single record per book.
        (record['creator_id'], record['creator']) = resultset_to_keyval(aux_cursor.execute(sel_aux('gutenberg_creators', 'creator'), textId_dict).fetchall())
        (record['contributor_id'], record['contributor']) = resultset_to_keyval(aux_cursor.execute(sel_aux('gutenberg_contributors', 'contributor'), textId_dict).fetchall())
        # don't store id's for these fields so just extract list of values
        record['category'] = [e[1] for e in aux_cursor.execute(sel_aux('gutenberg_categories', 'category'), textId_dict).fetchall()]
        record['subject'] = [e[1] for e in aux_cursor.execute(sel_aux('gutenberg_subjects', 'subject'), textId_dict).fetchall()]
        record['language'] = [e[1] for e in aux_cursor.execute(sel_aux('gutenberg_languages', 'language'), textId_dict).fetchall()]

        # Only index fields from description records. File records can be ignored.
        if count % 10000 == 0:
            print count,
        subset = {k : record[k] for k in schema.names() if k in record}
        writer.add_document(**subset)

    print "committing...",
    writer.commit()
    print "DONE"

if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rdf", dest="bz2_rdf_filename", action="store",
                      help="The Project Gutenberg RDF/XML index.")
    group.add_argument("--db", dest="dbname", action="store",
                      help="The Project Gutenberg RDF/XML index.")
    parser.add_argument("--indexdir", dest="indexdir", action="store",
                      default="gutenberg_index",
                      help="The output whoosh index directory name")
    args = parser.parse_args()

    if args.bz2_rdf_filename is not None:
        create_gutenberg_index_rdf(args.bz2_rdf_filename, args.indexdir)
    else:
        create_gutenberg_index_db(args.dbname, args.indexdir)

    print "Test search of whoosh index for 'Biology'..."
    test_search_results = test_query(args.indexdir, u"Biology")
    print test_search_results
    assert(len(test_search_results) > 0)

