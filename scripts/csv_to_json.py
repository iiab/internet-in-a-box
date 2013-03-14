#!/usr/bin/env python

import csv
import json
import os
import sys
from optparse import OptionParser

def read_csv(csvfile):
    records = []
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        assert isinstance(row, list) and len(row) == 1, "violated wordlist assumption of single word per record"
        records.append(row[0])
    return records

def write_json(jsonfile, records):
    jsonfile.write(json.dumps(dict(completions=records), separators=(',',':')))

def main(csv_filename, json_filename, always_overwrite):
    use_stdin = csv_filename == '-'
    use_stdout = json_filename == '-'

    if use_stdin:
        records = read_csv(sys.stdin)
    else:
        with open(csv_filename, 'r') as csvfile:
            records = read_csv(csvfile)

    if use_stdout:
        write_json(sys.stdout, records)
    else:
        if not always_overwrite and os.path.exists(json_filename):
            answer = raw_input("Confirm overwrite of " + json_filename + " (y/[n])")
            if answer != 'y' or answer != 'Y':
                exit()

        with open(json_filename, 'w') as jsonfile:
            write_json(jsonfile, records)

if __name__ == '__main__':

    parser = OptionParser(description="Convert CSV records to a JSON file for use with Gutenberg wordlist")
    parser.add_option("--csv", dest="csv_filename", action="store",
                      default="-",
                      help="csv input file. defaults to stdin")
    parser.add_option("--json", dest="json_filename", action="store",
                      default="-",
                      help="json output file. defaults to stdout")
    parser.add_option("-y", dest="always_overwrite", action="store_true",
                      default=False,
                      help="If specified target file will be overwritten without user query")
    (options, args) = parser.parse_args()

    if options.csv_filename == '-' and options.json_filename != '-' and not options.always_overwrite:
        print "ERROR: Since stdin is used for program input, cannot ask for overwrite confirmation.  Must specify the force overwrite option in this configuration."
        exit(1)

    main(options.csv_filename, options.json_filename, options.always_overwrite)


