#!/usr/bin/python

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


def progress_bar(name, maxval):
    widgets = [name, progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)
    pbar.start()
    return pbar


@timepro.profile_and_print()
def init_article_info(zf, show_progress=True):
    # Initialize the article info dictionary
    article_info = {}
    articles_by_index = []
    articles = zf.articles()
    if show_progress:
        count = zf.header['articleCount']
        progress = progress_bar("Reading " + str(count) + " article indices", count)
    for entry in articles:
        entry['indegree'] = 0
        entry['outdegree'] = 0
        article_info[entry['fullUrl']] = entry
        articles_by_index.append(entry)
        if show_progress and (len(articles_by_index) % 100 == 0):
            progress.update(len(articles_by_index))
    print
    return article_info, articles_by_index


# Regex to match references to other articles
regex = re.compile(u'(?:href|src)(?:=["\']/)([A-Z\-])/([^"\']+)')


def find_urls(html):
    """Find all urls in html text which refer to other
    articles"""
    return re.findall(regex, html)


@timepro.profile_and_print()
def process(zf, article_info, articles_by_entry, not_found, show_progress=True):
    mime_indices = set()
    for n, mimetype in enumerate(zf.mimeTypeList):
        if mimetype in ['text/html; charset=utf-8', 'stylesheet/css', 'text/html']:
            mime_indices.add(n)
    if show_progress:
        progress = progress_bar("Processing " + str(len(article_info)) + " in " + os.path.basename(zf.filename), len(article_info))
    count = 0
    for entry in articles_by_entry:
        if 'redirectIndex' not in entry.keys() and entry['mimetype'] in mime_indices:
            body = zf.read_blob(entry['clusterNumber'], entry['blobNumber'])
            body = body.decode('utf-8', errors='replace')
            urls = find_urls(body)
            entry['outdegree'] = len(urls)
            for url in (full_url(namespace, title) for namespace, title in urls):
                dst = article_info.get(url, None)
                if dst is None:
                    #print "Could not find destination " + url
                    n = not_found.get(url, 0)
                    not_found[url] = n + 1
                else:
                    dst['indegree'] += 1
        count += 1
        if show_progress:
            progress.update(count)
    print


def output(fname, article_info):
    f = open(fname, "w")
    m = [(x['index'], x['indegree'], x['outdegree'], x['fullUrl']) for x in article_info.values()]
    m.sort(key=lambda x: -x[1])
    m = [str(x[0]) + "\t" + str(x[1]) + "\t" + str(x[2]) + "\t" + x[3].replace("\t", " ").replace("\n", " ") for x in m]
    txt = string.join(m, '\n') + "\n"
    txt = txt.encode('utf-8', errors='replace')
    f.write("INDEX\tTO\tFROM\tURL\n")
    f.write(txt)
    f.close()
    print


def output_notfound(fname, not_found):
    f = open(fname, "w")
    m = [(v, k) for (k, v) in not_found.items()]
    m.sort(key=lambda x: -x[0])
    m = [str(v) + "\t" + k]
    txt = string.join(m, "\n") + "\n"
    txt = txt.encode('utf-8', errors='replace')
    f.write(txt)
    f.close()


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
        article_info, articles_by_index = init_article_info(zf)
        timepro.reset()
        print

        not_found = {}
        process(zf, article_info, articles_by_index, not_found)

        outname = os.path.basename(zim_filename)
        outname, ext = os.path.splitext(outname)
        outname_notfound = outname + ".not_found"
        outname_notfound = os.path.join(options.outputdir, outname_notfound)
        outname += ".links"
        outname = os.path.join(options.outputdir, outname)
        output(outname, article_info)
        output_notfound(outname_notfound, not_found)
        zf.close()

        print "Processed " + zim_filename + " in " + str(time.time() - t0) + " seconds"
        print


if __name__ == '__main__':
    main(sys.argv)
