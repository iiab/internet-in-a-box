#!/usr/bin/env python

import sys
import os
from whoosh import analysis
from whoosh.index import create_in
import whoosh.fields as wf
from whoosh.fields import ID, TEXT, KEYWORD, STORED, NUMERIC, NGRAMWORDS
from argparse import ArgumentParser
import iiab_model as model



def test_query(indexdir, terms):
    from whoosh.index import open_dir
    from whoosh.qparser import QueryParser
    SEARCH_FIELD = "ngram_name"
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

    MIN_LEN = 1
    MAX_LEN = 151 # based on max name length found in geonames db.
    FIXED_PREFIX = "start"
    return wf.Schema(nameid=ID(unique=True, stored=True),
        geoid=ID(stored=True),
        fullname=TEXT(stored=True), 
        ngram_fullname=NGRAMWORDS(minsize=MIN_LEN, maxsize=MAX_LEN, at=FIXED_PREFIX, queryor=True),
        ngram_name=NGRAMWORDS(minsize=MIN_LEN, maxsize=MAX_LEN, at=FIXED_PREFIX, queryor=True),
        importance=NUMERIC(int, bits=64, sortable=True) 
        )

def load_feature_code_whitelist(filename):
    """return dict of feature code names from file where files lists one tag per line with no extra content"""
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

def passes_whitelist(feature_code, feature_code_whitelist):
    """returns true if feature_codes record should be retained"""
    return feature_code in feature_code_whitelist

class WhooshGenerator:
    def setup(self, index_dir, schema):
        self.whoosh_index = create_in(index_dir, schema)
        self.writer = self.whoosh_index.writer()
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
    # from, to
    ('id', 'nameid'),
    ('geonameid', 'geoid'),
    ('fullname', 'fullname'),
    ('fullname', 'ngram_fullname'),
    ('name', 'ngram_name'),
    ('importance', 'importance')
    }

def make_record(record):
    out = {}
    for from_, to in RECORD_MAPPING:
        out[to] = unicode(getattr(record, from_))
    return out

def parse_geo(dbfilename, index_dir, whitelist_filename):
    """
    Parse geo data database and generate records for storage in whoosh or stdout.
    :param dbfilename: filename of sqlite database with geo data tailored for IIAB.
    :param index_dir: directory into which whoosh data should be stored
    :param whitelist_filename: filename containing feature codes to be indexed.
    """
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

    feature_code_whitelist = load_feature_code_whitelist(whitelist_filename)

    generator = WhooshGenerator()
    #generator = StdoutGenerator()
    #generator = NullGenerator()

    schema = get_schema()
    generator.setup(index_dir, schema)

    omitted_count = 0
    geoid = None
    db = model.Database(dbfilename)

    for count, record in enumerate(db.session.query(model.GeoNames).order_by(model.GeoNames.geonameid).yield_per(1)):
        feature_code = db.session.query(model.GeoInfo).filter_by(id=record.geonameid).first().feature_code
        if passes_whitelist(feature_code, feature_code_whitelist):
            # our format does not seem to conform to the classic parent-child group so holding of on grouping for now
            #if geoid != record.geonameid:
            #    geoid = record.geonameid
            #    generator.start_group()
            schema_record = make_record(record)
            generator.write(schema_record)
        else:
            omitted_count += 1

        # print progress
        if count & 0x3ff == 0:  # every 1024 records
            if count & 0x1ffff == 0: # every 131072 records
                print count,
            else:
                print '.',

    print 'parsing complete'
    print 'omitted %d items' % omitted_count
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
    parser.add_argument("--whitelist", dest="whitelist_filename", action="store",
                      default="geotag_featurecode_whitelist.txt",
                      help="Simple list of feature codes to permit in the index, one code per line. Defaults to geotag_featurecode_whitelist.txt")
    parser.add_argument("--testonly", action="store_true",
                      help="Only run test query on existing whoosh index. Do not regenerate index")
    args = parser.parse_args()

    if not args.testonly:
        parse_geo(args.dbfilename, args.indexdir, args.whitelist_filename)

    print "Test search of whoosh index for 'Los Angeles'..."
    test_search_results = test_query(args.indexdir, u"Los Angeles")
    print test_search_results
    assert(len(test_search_results) > 0)


