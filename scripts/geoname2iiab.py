#!/usr/bin/env python

from optparse import OptionParser

import geoname_parser.geoname_db_generator as gn
import geoname_parser.iiab_db_generator as iiab

def main(geodb_filename, iiabdb_filename):
    print "Parsing geoname text records to create a geoname db..."
    gn.main(geodb_filename, True, True)

    print "Converting geoname db to IIAB dbi..."
    iiab.main(geodb_filename, iiabdb_filename)


if __name__ == '__main__':
    parser = OptionParser(description="Parse geonames.org geo data into a SQLite DB.")
    parser.add_option("--geodb", dest="geodb_filename", action="store",
                      default="geoname_geonames.db",
                      help="The geodata.db SQLite database")
    parser.add_option("--iiabdb", dest="iiabdb_filename", action="store",
                      default="iiab_geonames.db",
                      help="The geodata.db SQLite database")

    (options, args) = parser.parse_args()

    main(options.geodb_filename, options.iiabdb_filename)


