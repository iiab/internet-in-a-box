#!/usr/bin/env python

import sys
import os
from whoosh import analysis
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

    MIN_LEN = 3
    ngram_analyzer = analysis.NgramWordAnalyzer(MIN_LEN)
    return wf.Schema(geonameid=ID(unique=True, stored=True),
        name=TEXT(stored=True, spelling=True), 
        ngram_name=TEXT(analyzer=ngram_analyzer, phrase=False),
        latitude=STORED, 
        longitude=STORED,
        country_code=TEXT(stored=True),
        admin1_code=TEXT(stored=True),
        population=NUMERIC(long, stored=True) 
        )

def load_feature_code_whitelist(filename):
    """return dict of feature code names from file where files lists one tag per line with no extra content"""
    with open(filename, 'r') as f:
        tag_list = f.readlines()

        # remove leading/trailing whitespace
        chomper = lambda v: v.strip()
        tag_list = map(chomper, tag_list)

        # remove empty lines
        remove_zero_length_items = lambda v: len(v) > 0
        tag_list = filter(remove_zero_length_items, tag_list)

        # convert list to dict for fast membership testing
        tag_dict = { k : 1 for k in tag_list }

        return tag_dict

def passes_whitelist(record, feature_code_whitelist):
    """returns true if record should be retained"""
    # keep if on whitelist or no feature_code defined
    return 'feature_code' not in record or record['feature_code'] in feature_code_whitelist

class WhooshGenerator:
    def setup(self, index_dir, schema):
        self.whoosh_index = create_in(index_dir, schema)
        self.writer = self.whoosh_index.writer()

    def write(self, record):
        self.writer.add_document(**record)

    def commit(self):
        print 'committing... (this may take some time)'
        self.writer.commit()

class StdoutGenerator:
    def setup(self, index_dir, schema):
        pass

    def write(self, record):
        print record

    def commit(self):
        pass

class NullGenerator:
    def setup(self, index_dir, schema):
        pass

    def write(self, record):
        pass

    def commit(self):
        pass

# http://download.geonames.org/export/dump/readme.txt
# The main 'geoname' table has the following fields :
#    ---------------------------------------------------
#    geonameid         : integer id of record in geonames database
#    name              : name of geographical point (utf8) varchar(200)
#    asciiname         : name of geographical point in plain ascii characters, varchar(200)
#    alternatenames    : alternatenames, comma separated varchar(5000)
#    latitude          : latitude in decimal degrees (wgs84)
#    longitude         : longitude in decimal degrees (wgs84)
#    feature class     : see http://www.geonames.org/export/codes.html, char(1)
#    feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
#    country code      : ISO-3166 2-letter country code, 2 characters
#    cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 60 characters
#    admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
#    admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80) 
#    admin3 code       : code for third level administrative division, varchar(20)
#    admin4 code       : code for fourth level administrative division, varchar(20)
#    population        : bigint (8 byte int) 
#    elevation         : in meters, integer
#    dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
#    timezone          : the timezone id (see file timeZone.txt) varchar(40)
#    modification date : date of last modification in yyyy-MM-dd format
#
def parse_geo(geo, index_dir, whitelist_filename):
    """
    Parse geo data file and generate records for storage in whoosh or stdout.
    :param geo: filename of tab delimited text file with geo data to be parsed
    :param index_dir: directory into which whoosh data should be stored
    :param whitelist_filename: filename containing feature codes to be indexed.
    """
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

    field_names = ('geonameid', 'name', 'asciiname', 'altnames',
                   'latitude', 'longitude', 'feature_class', 'feature_code',
                   'country_code', 'cc2', 'admin1_code', 'admin2_code',
                   'admin3_code', 'admin4_code', 'population', 'elevation',
                   'gtopo30', 'timezone', 'modification_date')
    feature_code_whitelist = load_feature_code_whitelist(whitelist_filename)

    omitted_count = 0

    generator = WhooshGenerator()
    #generator = StdoutGenerator()
    #generator = NullGenerator()

    with codecs.open(geo, encoding='utf-8') as f:
        schema = get_schema()
        generator.setup(index_dir, schema)
        for count, line in enumerate(f):
            line = line.rstrip()
            record = dict(zip(field_names, line.split('\t')))

            # Note that whitelist filter should be applied before filtering out non-schema fields
            if passes_whitelist(record, feature_code_whitelist):
                # manipulate record to include special duplicated field for ngram parsing
                # beware hardcoded field names must be kept in sync with data and whoosh schemas
                NGRAM_FIELDNAME = 'ngram_name'
                NGRAM_SRC_FIELD = 'name'
                assert NGRAM_FIELDNAME in schema
                assert NGRAM_SRC_FIELD in record
                record[NGRAM_FIELDNAME] = record[NGRAM_SRC_FIELD]

                # remove fields not stored in the schema
                pruned_record = { k: v for k,v in record.items() if k in schema }
                generator.write(pruned_record)
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
    parser.add_argument("--geo", dest="geo", action="store",
                      default="allCountries.txt",
                      help="The geonames index. Defaults to allCountries.txt")
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
        parse_geo(args.geo, args.indexdir, args.whitelist_filename)

    print "Test search of whoosh index for 'Los Angeles'..."
    test_search_results = test_query(args.indexdir, u"Los Angeles")
    print test_search_results
    assert(len(test_search_results) > 0)


