#!/usr/bin/env python

import csv
import json
import os
import sys
from optparse import OptionParser


def main(csv_filename, json_filename):
    if os.path.exists(json_filename):
        answer = raw_input("Confirm overwrite of " + json_filename + " (y/[n])")
        if answer != 'y' or answer != 'Y':
            exit()
    records = []
    with open(csv_filename, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in reader:
            assert isinstance(row, list) and len(row) == 1, "violated wordlist assumption of single word per record"
            records.append(row[0])

    with open(json_filename, 'w') as jsonfile:
        jsonfile.write(json.dumps(dict(completions=records), separators=(',',':')))

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print """
Convert CSV records to a JSON file for use with Gutenberg wordlist
    csv_to_json.py csv_input_file json_output_file
"""
        exit()

    parser = OptionParser()
    parser.add_option("--csv", dest="csv_filename", action="store",
                      help="csv input file")
    parser.add_option("--json", dest="json_filename", action="store",
                      help="json output file")
    (options, args) = parser.parse_args()

    main(options.csv_filename, options.json_filename)


