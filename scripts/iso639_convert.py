#!/usr/bin/env python

"""ISO-639-2 Language Codes.
Based on
http://stackoverflow.com/questions/2879856/get-system-language-in-iso-639-3-letter-codes-in-python"""


import json
import codecs


iso_codes = None

def get_iso_codes():
    if iso_codes == None:
        pass
    return iso_codes


def language_name(code):
    """Returns a human-readable english language
    name for the specified language code"""


def getisocodes_dict(data_path):
    # Provide a map from ISO code (both bibliographic and terminologic)
    # in ISO 639-2 to a dict with the two letter ISO 639-2 codes (alpha2)
    # English and french names
    #
    # "bibliographic" iso codes are derived from English word for the language
    # "terminologic" iso codes are derived from the pronunciation in the target
    # language (if different to the bibliographic code)

    D = {}
    f = codecs.open(data_path, 'rb', 'utf-8')
    for line in f:
        iD = {}
        iD['bibliographic'], iD['terminologic'], iD['alpha2'], \
            iD['english'], iD['french'] = line.strip().split('|')
        D[iD['bibliographic']] = iD

        if iD['terminologic']:
            D[iD['terminologic']] = iD

        if iD['alpha2']:
            D[iD['alpha2']] = iD

        for k in iD:
            # Assign '' when columns not available from the data
            iD[k] = iD[k] or ''
    f.close()
    return D


def isocodes_to_json(source="data/ISO-639-2_utf-8.txt", destination="iiab/iso639.py"):
    d = getisocodes_dict(source)
    f = open(destination, "w")
    f.write("iso6392 = ")
    json.dump(d, f, indent=4)
    f.write("\n")
    f.close()

isocodes_to_json()
