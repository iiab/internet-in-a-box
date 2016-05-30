#!/usr/bin/env python

import os
import sys
import logging

# Expand import search path to allow import of timepro profiling code
package_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, package_dir)

from optparse import OptionParser, OptionGroup

import geoname_parser.geoname_db_generator as gn
import geoname_parser.iiab_db_generator as iiab
import geoname_parser.whoosh_indexer as whooshgen

import iiab.timepro as timepro

# Debug logging required to see profiling output.
# In other cases logging level can be tuned if desired.
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(message)s")


def main(geodb_filename, iiabdb_filename, make_geonames_info_db=True, make_geonames_names_db=True, make_iiab_db=True):
    if make_geonames_info_db or make_geonames_names_db:
        print "Parsing geoname text records to create a geoname db..."
        gn.main(geodb_filename, make_geonames_info_db, make_geonames_names_db)

    if make_iiab_db:
        print "Converting geoname db to IIAB db..."
        iiab.main(geodb_filename, iiabdb_filename)


if __name__ == '__main__':
    parser = OptionParser(description="Parse geonames.org geo data into a SQLite DB.")
    parser.add_option("--iiabdb", dest="iiabdb_filename", action="store",
                      default="iiab_geonames.db",
                      help="The name of the IIAB geonames SQLite database. Defaults to iiab_geonames.db.")
    dbgroup = OptionGroup(parser, "Generate SQLite Databases")
    dbgroup.add_option("--mkdb", action="store_true",
                      help="Make the geonames and iiab databases.")
    dbgroup.add_option("--geodb", dest="geodb_filename", action="store",
                      default="geoname_geonames.db",
                      help="The geodata.db SQLite database")
    dbgroup.add_option("--skip_gn_info", action="store_true",
                      help="Skip the geonames info db gen.")
    dbgroup.add_option("--skip_gn_names", action="store_true",
                      help="Skip the geonames names db gen.")
    dbgroup.add_option("--skip_iiab_db", action="store_true",
                      help="Skip convert geonames db to iiab db.")
    whooshgroup = OptionGroup(parser, "Generate Whoosh Index")
    whooshgroup.add_option("--mkwhoosh", action="store_true",
                      help="Make the whoosh index.")
    whooshgroup.add_option("--indexdir", dest="indexdir", action="store",
                      default="geonames_index",
                      help="The output whoosh index directory name. Defaults to geonames_index")
    whooshgroup.add_option("--whitelist", dest="whitelist_filename", action="store",
                      default="geotag_featurecode_whitelist.txt",
                      help="Simple list of feature codes to permit in the index, one code per line. Defaults to geotag_featurecode_whitelist.txt")
    parser.add_option_group(dbgroup)
    parser.add_option_group(whooshgroup)
    parser.add_option("--timepro", action="store_true", default=False,
                      help="Enable timepro performance profiler")

    (options, args) = parser.parse_args()

    if not options.mkdb and not options.mkwhoosh:
        print "Nothing to do. Specify options to make something happen."
    else:
        # timepro must be configured prior to making the database or index
        if options.timepro:
            timepro.global_active = True

        if options.mkdb:
            main(options.geodb_filename, options.iiabdb_filename, not options.skip_gn_info, not options.skip_gn_names, not options.skip_iiab_db)

        if options.mkwhoosh:
            whooshgen.parse_geo(options.iiabdb_filename, options.indexdir, options.whitelist_filename)

