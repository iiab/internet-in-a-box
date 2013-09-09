#!/usr/bin/python
# Performs a link analysis on a zim file, recording
# the in-degree and out-degree of each article
# By Braddock Gaskill, 9 Sept 2013

import sys
import os
import re
import string
import time
from optparse import OptionParser
import progressbar
import logging

package_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, package_dir)

import iiab
from iiab.zimpy import ZimFile, full_url
import iiab.timepro as timepro

import memory_profiler


def progress_bar(name, maxval):
    widgets = [name, progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)
    pbar.start()
    return pbar


# Regex to match references to other articles
regex = re.compile(u'(?:href|src)(?:=["\']/)([A-Z\-])/([^"\']+)')


def find_urls(html):
    """Find all urls in html text which refer to other
    articles"""
    return re.findall(regex, html)


def process2(zf, namespaces=['A']):
    mime_indices = set()
    for n, mimetype in enumerate(zf.mimeTypeList):
        if mimetype in ['text/html; charset=utf-8', 'stylesheet/css', 'text/html']:
            mime_indices.add(n)

    articleCount = zf.header['articleCount']
    progress = progress_bar("Processing " + str(articleCount) + " articles in " + os.path.basename(zf.filename), articleCount)

    links = {}

    articles = zf.articles()
    for entry in articles:
        if 'redirectIndex' not in entry.keys() and entry['mimetype'] in mime_indices and entry['namespace'] in namespaces:
            body = zf.read_blob(entry['clusterNumber'], entry['blobNumber'])
            body = body.decode('utf-8', errors='replace')
            urls = find_urls(body)
            urls = [(namespace, title) for (namespace, title) in urls if namespace in namespaces]

            # Record outbound links
            link = links.get(entry['fullUrl'], (0, 0))
            links[entry['fullUrl']] = (link[0], link[1] + len(urls))

            # Record inbound links
            for namespace, title in urls:
                if namespace in namespaces:
                    full = full_url(namespace, title)
                    link = links.get(full, (0, 0))
                    links[full] = (link[0] + 1, link[1])

            progress.update(entry['index'])
    print
    return links


def output2(fname, zf, links):
    not_found = 0
    progress = progress_bar("Writing " + str(len(links)) + " articles in " + os.path.basename(zf.filename), len(links))
    f = open(fname, "w")
    f.write("INDEX\tTO\tFROM\tURL\n")
    for idx, (fullurl, link) in enumerate(links.items()):
        if (idx % 100 == 0):
            progress.update(idx)
        namespace, url = fullurl.split("/", 1)
        entry, m = zf.get_entry_by_url(namespace, url)
        if entry is None:
            not_found += 1
        else:
            s = string.join([str(entry['index']), str(link[0]), str(link[1]), fullurl.replace("\t", " ").replace("\n", " ")], '\t')
            s = s.encode('utf-8', errors='replace') + "\n"
            f.write(s)
    f.close()
    if not_found > 0:
        print
        print "WARNING: " + str(not_found) + " referenced articles not found by URL"


def main(argv):
    parser = OptionParser()
    parser.add_option("--outputdir", default='.',
                      help="Directory into which to store output")
    parser.add_option("--version", action="store_true", default=False,
                      help="Print version and quit")
    parser.add_option("--timepro", action="store_true", default=False,
                      help="Enable timepro performance profiler")

    (options, args) = parser.parse_args()

    if options.version:
        print "Internet-in-a-Box Version " + iiab.__version__
        return 0

    # Set up logging
    FORMAT = "%(name)s -- %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG, stream=sys.stdout)

    if options.timepro:
        timepro.global_active = True

    for zim_filename in args:
        print "Processing " + zim_filename
        t0 = time.time()

        zf = ZimFile(zim_filename, cache_size=1024)

        outname = os.path.basename(zim_filename)
        outname, ext = os.path.splitext(outname)
        outname += ".links"
        outname = os.path.join(options.outputdir, outname)
        if os.path.exists(outname):
            print "Skipping " + zim_filename + " because output file " + outname + " already exists"
        else:
            links = process2(zf)
            output2(outname, zf, links)
        print zim_filename + " completed in " + str((time.time() - t0)/60.0) + " minutes"
        print


if __name__ == '__main__':
    main(sys.argv)
