#!/usr/bin/env python

import sys
from lxml import etree
from bz2 import BZ2File


# Identify record as either a book descriptor or a file descriptor
REC_TYPE_KEY = "record_type"
DESCRIPTION_TYPE_VALUE = "DESCRIPTION"
FILE_TYPE_VALUE =  "FILE"

# XML tag to record (and whoosh) tag mapping
ETEXT_MAPPINGS = {
    # omit dc:publisher, dc:rights
    "dc:title"              : "title",
    "pgterms:friendlytitle" : "friendlytitle",
    "dc:language"           : "language",
    "dc:contributor"        : "contributor",
    "dc:creator"            : "creator",
    "dc:subject"            : "subject",
    "pgterms:downloads"     : "downloads",
    # the gutenberg index currently always single nests tags: type >> category >> value 
    # this mapping might break if the index format varies in the future
    "dc:type"               : "category"
}

FILE_MAPPINGS = {
    # omit dcterms:modified
    "dc:format"             : "format",
    "dcterms:extent"        : "extent",
    "dcterms:isFormatOf"    : "textId"
}

# Record names for extracted attributes. Whoosh schema should reference same names.
# For storing rdf:ID attribut from etext element.
REC_ETEXT_ID = "textId"
# For storing rdf:about attribute from file element.
REC_FILE_PATH = "file"

# Tags sometimes include a formatType attribute of Literal indicating
# that the element contains some literal contents.  However,
# in practice the cases examined show contents are in the inner most
# element even though the depth varies so this seems to work.
def get_nested_content(element):
    """
    Recurse down the tree to each leaf and return a list of the text contents.

    :param element: XML element to parse
    :returns: list of XML text contents from inner most leaves
    """
    if len(element) == 0:
        if element.text is not None:
            return [unicode(element.text)]
        else:
            print element.tag + " has no content"
            return []
    else:
        content = []
        for el in element:
            content = content + get_nested_content(el)
        return content

def get_content(etext, tag, nsmap):
    """
    Extract list of contents under the tag provided

    :param etext:   Element containing XML record for the book entry
    :param tag:     Tag from the record to extract, which may use namespace abbreviations
    :param nsmap:   Namespace map to be used in parsing the tag
    :returns:       list of text elements retrieved from leaves of the @c tag elements.
    """
    content = []
    # Note: iter() does not use namespace abbreviations (apart from {*}), though it can filter on multiple tags
    # iterfind() only searches a single tag but can use namespace abbreviations.
    tag_iter = etext.iterfind(tag, namespaces=nsmap)
    for element in tag_iter:
        if len(element) == 0:
            if element.text is not None:
                content.append(unicode(element.text))
        else:
            content.extend(get_nested_content(element))

    return content

def parse_rdf_bz2(bz2_rdf_filename, filter=None):
    infile = BZ2File(bz2_rdf_filename)
    return parse_rdf(infile, filter)
    

def parse_rdf(src, filter=None):
    """
    Parse each etext element into a book record.  Yields each completed record.

    :param src:     File object for XML document (actually more liberal - see iterparse docs if you care)
    :param filter:  Function that accepts a record and returns false if record should be filtered out.  None means do not filter any records. Default is None.
    :returns:       Book record which is one of two types: a book description or a file description.
                    Distinguish between record types by using the REC_TYPE_KEY
    """
    # To get root element, we need to trap the first start event. 
    # Afterwards focus on the end events, which occur after the subtree has been fully parsed.
    # Like the docs say, the nested contents can't be accessed fully until after an 'end' event because
    # it hasn't all been parsed yet.  (Interestingly 34 elements were loaded on the root's 'start' event.)
    context = etree.iterparse(src, ('start','end'))
    root = None
    for event, element in context:
        if root is None and event == 'start':
            root = element
            # Must use full namespace for an attribute lookup and tag comparisons
            ETEXT_TAG           = "{%s}etext" % root.nsmap['pgterms']
            FILE_TAG            = "{%s}file" % root.nsmap['pgterms']
            ID_ATTRIB           = "{%s}ID" % root.nsmap['rdf']
            ABOUT_ATTRIB        = "{%s}about" % root.nsmap['rdf']
            RDF_RESOURCE_ATTRIB = "{%s}resource" % root.nsmap['rdf']

            FORMATOF_TAG        = "dcterms:isFormatOf"


        # The index format is roughly composed as follows:
        # <rdf:RDF ...>
        # <pgterms:etext ...>...</pgterms:etext>
        # <pgterms:etext ...>...</pgterms:etext>
        # <pgterms:etext ...>...</pgterms:etext>
        #
        # <pgterms:file ...>...</pgterms:file>
        # <pgterms:file ...>...</pgterms:file>
        # <pgterms:file ...>...</pgterms:file>
        # </rdf:RDF>
        #
        # Each file element embeds a reference to an associated etext entry.
        if event == 'end' and element.tag == ETEXT_TAG:
            assert(root is not None)
        
            record = { REC_TYPE_KEY : DESCRIPTION_TYPE_VALUE, REC_ETEXT_ID : unicode(element.attrib[ID_ATTRIB]) }
            for xmltag, rectag in ETEXT_MAPPINGS.items():
                content = get_content(element, xmltag, root.nsmap)
                if len(content) == 1:
                    content = content[0]
                record[rectag] = content
            if filter is None or filter(record):
                yield record
        elif event == 'end' and element.tag == FILE_TAG:
            assert(root is not None)

            # &f; in the about attrib is an entity expansion
            # http://www.gutenberg.org/dir seems to equate to /knowledge/data/gutenberg/gutenberg
            # http://www.gutenberg.org/cache seems to equate to generated content not currently downloaded
            record = { REC_TYPE_KEY : FILE_TYPE_VALUE, REC_FILE_PATH : unicode(element.attrib[ABOUT_ATTRIB]) }
            for xmltag, rectag in FILE_MAPPINGS.items():
                if xmltag == FORMATOF_TAG:
                    content = element.find(xmltag, namespaces=root.nsmap).attrib[RDF_RESOURCE_ATTRIB]
                else:
                    content = get_content(element, xmltag, root.nsmap)
                    if len(content) == 1:
                        content = content[0]
                record[rectag] = content
            if filter is None or filter(record):
                yield record

if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    if (len(sys.argv) != 2 or sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print """
        Prints books parsed into python records. This module also provides a service for other scripts.
        Usage: %s catalog.rdf.bz2
        """ % sys.argv[0]
        exit()
    filename = sys.argv[1]
    for record in parse_rdf_bz2(filename):
        print record
        #pp.pprint(record)

