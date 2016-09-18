#!/usr/bin/env python

import sys
import os
from whoosh import analysis
from whoosh.index import create_in
import whoosh.fields as wf
from whoosh.fields import ID, TEXT, KEYWORD, STORED, NUMERIC, NGRAMWORDS
from argparse import ArgumentParser
import iiab_maps_model as model
import dbhelper
import multiprocessing


def enable_sqlalchemy_logging():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

    logging.getLogger('sqlalchemy.dialects.sqlite').setLevel(logging.DEBUG)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG)
    logging.getLogger('sqlite').setLevel(logging.DEBUG)


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

    MIN_LEN = 3
    MAX_LEN = 10
    FIXED_PREFIX = "start"
    return wf.Schema(nameid=ID(unique=True, stored=True),
        #geoid=ID(stored=True),
        fullname=TEXT(stored=True, sortable=True),
        name=TEXT,
        lang=KEYWORD(stored=True, sortable=True),
        ngram_fullname=NGRAMWORDS(minsize=MIN_LEN, maxsize=MAX_LEN, at=FIXED_PREFIX, queryor=False),
        #ngram_name=NGRAMWORDS(minsize=MIN_LEN, maxsize=MAX_LEN, at=FIXED_PREFIX, queryor=True),
        latitude=STORED,
        longitude=STORED,
        importance=NUMERIC(int, bits=64, sortable=True)
        )

def load_whitelist(filename):
    """return dict of tags from file where files lists one tag per line with no extra content"""
    if filename is None:
        return None

    with open(filename, 'r') as f:
        tag_list = f.readlines()

        # remove comments marked by a hash
        def filter_comment(v):
            index = v.find('#')
            if index > -1:
                return v[:index]
            else:
                return v
        tag_list = map(filter_comment, tag_list)

        # remove leading/trailing whitespace
        chomper = lambda v: v.strip()
        tag_list = map(chomper, tag_list)

        # remove empty lines
        remove_zero_length_items = lambda v: len(v) > 0
        tag_list = filter(remove_zero_length_items, tag_list)

        # convert list to dict for fast membership testing
        tag_dict = { k : 1 for k in tag_list }

        return tag_dict

def passes_featuretype_whitelist(feature_code, feature_code_whitelist):
    """returns true if feature_codes record should be retained"""
    return feature_code in feature_code_whitelist

def passes_language_whitelist(lang, lang_whitelist):
    """returns true if language record should be retained"""
    return lang_whitelist is None or lang in lang_whitelist

class WhooshGenerator:
    def setup(self, index_dir, schema):
        self.whoosh_index = create_in(index_dir, schema)
        self.writer = self.whoosh_index.writer(procs=multiprocessing.cpu_count())
        self.in_group = False  # only one level of grouping is used here

    def start_group(self):
        """For use with grouped index."""
        if self.in_group:
            self.end_group()
        self.writer.start_group()
        self.in_group = True

    def end_group(self):
        """For use with grouped index."""
        self.writer.end_group()
        self.in_group = False

    def write(self, record):
        self.writer.add_document(**record)

    def commit(self):
        if self.in_group:
            self.end_group()
        print 'committing... (this may take some time)'
        self.writer.commit()

class StdoutGenerator:
    def setup(self, index_dir, schema):
        pass

    def write(self, record):
        print record

    def start_group(self):
        pass

    def end_group(self):
        pass

    def commit(self):
        pass

class NullGenerator:
    def setup(self, index_dir, schema):
        pass

    def write(self, record):
        pass

    def start_group(self):
        pass

    def end_group(self):
        pass

    def commit(self):
        pass

RECORD_MAPPING = {
    # from-resultset, from-attribute, to
    (0, 'id', 'nameid'),
    #(0, 'geoid', 'geoid'),
    (0, 'fullname', 'fullname'),
    (0, 'name', 'name'),
    (0, 'fullname', 'ngram_fullname'),
    (0, 'lang', 'lang'),
    (0, 'importance', 'importance'),
    #(0, 'name', 'ngram_name'),
    (1, 'latitude', 'latitude'),
    (1, 'longitude', 'longitude')
    }

def make_record(record):
    out = {}
    for ii, from_, to in RECORD_MAPPING:
        out[to] = unicode(getattr(record[ii], from_))
    return out

def parse_geo(dbfilename, index_dir, features_whitelist_filename, languages_whitelist_filename=None):
    """
    Parse geo data database and generate records for storage in whoosh or stdout.
    :param dbfilename: filename of sqlite database with geo data tailored for IIAB.
    :param index_dir: directory into which whoosh data should be stored
    :param features_whitelist_filename: filename containing feature codes to be indexed.
    :param languages_whitelist_filename: filename containing language codes to be indexed.
    """
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

    feature_code_whitelist = load_whitelist(features_whitelist_filename)
    lang_whitelist = load_whitelist(languages_whitelist_filename)

    print("Using feature whitelist with %d entries" % len(feature_code_whitelist))
    if lang_whitelist is not None:
        print("Using language whitelist with %d entries" % len(lang_whitelist))
    else:
        print("All languages include")

    generator = WhooshGenerator()
    #generator = StdoutGenerator()
    #generator = NullGenerator()

    schema = get_schema()
    generator.setup(index_dir, schema)

    geoid = None
    db = dbhelper.Database(model.Base, dbfilename)

    # Build query
    query = db.session.query(model.GeoNames, model.GeoInfo).filter(model.GeoNames.geoid == model.GeoInfo.id)
    if feature_code_whitelist is not None:
        query = query.filter(model.GeoInfo.feature_code.in_(feature_code_whitelist))
    if lang_whitelist is not None:
        query = query.filter(model.GeoNames.lang.in_(lang_whitelist))
    query = query.order_by(model.GeoNames.geoid)

    BLK_SIZE = 1000
    for count, record in enumerate(query.yield_per(BLK_SIZE)):
        # our format does not seem to conform to the classic parent-child group so holding off on grouping for now
        #if geoid != record.geoid:
        #    geoid = record.geoid
        #    generator.start_group()
        schema_record = make_record(record)
        generator.write(schema_record)

        # print progress
        if count & 0x3ff == 0:  # every 1024 records
            if count & 0x1ffff == 0: # every 131072 records
                print count,
            else:
                print '.',

    print 'parsing complete'
    generator.commit()
    print 'done'


if __name__ == '__main__':
    parser = ArgumentParser(description="""
    Parses geo data from tab delimited text file.  Obtain the geo data file from
    http://download.geonames.org/export/dump/ usually allCountries.txt (found in allCountries.zip)
    After parsing the content, a whoosh index is created.  The index output directory must already
    exist. Be aware the index size will be on the order of 2GB.
    """)
    parser.add_argument("--db", dest="dbfilename", action="store",
                      default="iiab_geonames.db",
                      help="The name of the IIAB geonames database. Defaults to iiab_geonames.db.")
    parser.add_argument("--indexdir", dest="indexdir", action="store",
                      default="geonames_index",
                      help="The output whoosh index directory name. Defaults to geonames_index")
    parser.add_argument("--features-whitelist", dest="features_whitelist_filename", action="store",
                      default="geotag_featurecode_whitelist.txt",
                      help="Simple list of feature codes to permit in the index, one code per line. Defaults to geotag_featurecode_whitelist.txt")
    parser.add_argument("--language-whitelist", dest="language_whitelist_filename", action="store",
                      default=None,
                      help="Simple list of language codes to permit in the index, one code per line. Defaults to include all.")
    parser.add_argument("--testonly", action="store_true",
                      help="Only run test query on existing whoosh index. Do not regenerate index")
    parser.add_argument("--verbose", action="store_true",
                      help="Enable DB query logging")
    args = parser.parse_args()

    if args.verbose:
        enable_sqlalchemy_logging()

    if not args.testonly:
        parse_geo(args.dbfilename, args.indexdir, args.features_whitelist_filename)

    print "Test search of whoosh index for 'Los Angeles'..."
    test_search_results = test_query(args.indexdir, u"Los Angeles")
    print test_search_results
    assert(len(test_search_results) > 0)


