#!/usr/bin/env python

import sys
import os
from whoosh.index import create_in
import whoosh.fields as wf
from whoosh.fields import ID, TEXT, KEYWORD, STORED, NUMERIC
from argparse import ArgumentParser
import codecs


def test_query(indexdir, terms):
    from whoosh.index import open_dir
    from whoosh.qparser import QueryParser
    SEARCH_FIELD = "name"
    whoosh_index = open_dir(indexdir)
    with whoosh_index.searcher() as searcher:
        query = QueryParser(SEARCH_FIELD, whoosh_index.schema).parse(terms)
        results = searcher.search(query)
        return [r.items() for r in results]
        #return [dict(r.items()) for r in results]

def get_schema():
    # Whoosh schema - for ease of use match names with record keys
    # Spelling attribute will cause columns to be used as source of query correction suggestions

    # Analyzers can be used to provide fuzzy matches to searches.  However,
    # the side effect seems to be that it polutes the match streams so that
    # spelling suggestions are meaningless.

    return wf.Schema(geonameid=ID(unique=True, stored=True),
        name=TEXT(stored=True, spelling=True), 
        latitude=NUMERIC(float, stored=True), 
        longitude=NUMERIC(float, stored=True),
        population=NUMERIC(int, stored=True) 
        )

# field structure courtesy of http://blogs.msdn.com/b/edkatibah/archive/2009/01/13/loading-geonames-data-into-sql-server-2008-yet-another-way.aspx
# geonameid int NOT NULL,
# name nvarchar(200) NULL,
# asciiname nvarchar(200) NULL,
# alternatenames nvarchar(max) NULL,
# latitude float NULL,
# longitude float NULL,
# feature_class char(2) NULL,
# feature_code nvarchar(10) NULL,
# country_code char(3) NULL,
# cc2 char(60) NULL,
# admin1_code nvarchar(20) NULL,
# admin2_code nvarchar(80) NULL,
# admin3_code nvarchar(20) NULL,
# admin4_code nvarchar(20) NULL,
# population int NULL,
# elevation int NULL,
# gtopo30 int NULL,
# timezone char(31) NULL,
# modification_date date NULL 
def parse_geo(geo, index_dir):
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

    field_names = ('geonameid', 'name', 'asciiname', 'altnames',
                   'latitude', 'longitude', 'feature_class', 'feature_code',
                   'country_code', 'cc2', 'admin1_code', 'admin2_code',
                   'admin3_code', 'admin4_code', 'population', 'elevation',
                   'gtopo30', 'timezone', 'modification_date')
    with codecs.open(geo, encoding='utf-8') as f:
        schema = get_schema()
        whoosh_index = create_in(index_dir, schema)
        writer = whoosh_index.writer()
        for count, line in enumerate(f):
            line = line.rstrip()
            record = dict(zip(field_names, line.split('\t')))
            pruned_record = { k: v for k,v in record.items() if k in schema }
            writer.add_document(**pruned_record)
            if count % 1000 == 0:
                print '.',

        print 'committing...'
        writer.commit()
        print 'done'
        

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--geo", dest="geo", action="store",
                      default="allCountries.txt",
                      help="The geonames index.")
    parser.add_argument("--indexdir", dest="indexdir", action="store",
                      default="geonames_index",
                      help="The output whoosh index directory name")
    args = parser.parse_args()

    parse_geo(args.geo, args.indexdir)

    print "Test search of whoosh index for 'Los Angeles'..."
    test_search_results = test_query(args.indexdir, u"Los Angeles")
    print test_search_results
    assert(len(test_search_results) > 0)


