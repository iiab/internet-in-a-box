#!/usr/bin/env python

import sys
from bz2 import BZ2File
#from xml.etree import ElementTree as etree
# lxml is 10 times faster than ElementTree
from lxml import etree


def main(argv):
    if len(argv) < 2:
        print "USAGE: " + argv[0] + " <catalog.rdf.bz2>"
        return
    fname = argv[1]
    f = BZ2File(fname)
    et = etree.parse(f)
    root = et.getroot()
    it = root.iterfind("pgterms:etext", namespaces=root.nsmap)
    for etext in it:
        title = etext.find("pgterms:friendlytitle", namespaces=etext.nsmap)
        if title is not None and title.text is not None:
            print title.text.encode('utf-8')
        else:  # there are only 33 entries without friendlytitle
            print "No friendly title"


if __name__ == '__main__':
    main(sys.argv)
