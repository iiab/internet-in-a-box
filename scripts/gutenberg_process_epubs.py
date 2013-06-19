#!/usr/bin/python

import os
import re
import string
from time import sleep
from subprocess import Popen
from optparse import OptionParser
from sys import argv
from shutil import copyfile
from random import shuffle
import progressbar


def progress_bar(name, maxval):
    widgets = [name, progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)
    pbar.start()
    return pbar


def find_files(cache_mirror_dir, regex="pg([0-9]+)(-images)?.epub"):
    epubs = []
    compiled = re.compile(regex)
    for path, dirs, files in os.walk(cache_mirror_dir):
        for filename in files:
            if re.match(compiled, filename):
                epubs.append(os.path.join(path, filename))
    return epubs


def parse_epub_filename(filename):
    regex = 'pg([0-9]+)(-images)?.epub'
    g = re.match(regex, filename)
    if g is None:
        raise Exception("Invalid epub filename " + filename)
    is_image = g.groups()[1] is not None
    n = int(g.groups()[0])
    return (n, is_image)


def build_epub_filename(n, is_image):
    fn = "pg%i" % n
    if is_image:
        fn += '-images'
    fn += '.epub'
    return fn


def hashdir(n):
    return "%02i" % (int(n) % 100)


def copy_epub(pathname, epub_dir, epub_images_dir):
    filename = os.path.split(pathname)[1]
    n, is_image = parse_epub_filename(filename)
    hashpath = hashdir(n)
    newfilename = build_epub_filename(n, False)
    destdir = os.path.join(epub_images_dir, hashpath)
    dest = os.path.join(destdir, newfilename)
    if is_image or not os.path.exists(dest):
        mkdirs(destdir)
        copyfile(pathname, dest)
    if not is_image:
        destdir = os.path.join(epub_dir, hashpath)
        mkdirs(destdir)
        dest = os.path.join(destdir, filename)
        copyfile(pathname, dest)


def new_filename(epub_filename, output_dir):
    filename = os.path.split(epub_filename)[1]
    n, is_image = parse_epub_filename(filename)
    subdir = hashdir(n)
    subdir = os.path.join(output_dir, subdir)
    newfn = os.path.splitext(filename)[0] + '.htmlz'
    return os.path.join(subdir, newfn)


def mkdirs(d):
    """mkdir -p"""
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            # Multiple threads can race when creating directories,
            # ignore exception if the directory now exists
            if not os.path.exists(d):
                raise


def convert(sources, dst_dir, nthreads):
    nsources = len(sources)
    finished = False
    jobs = []
    count = 0
    while not finished:

        # spawn up to nthreads jobs
        while len(jobs) < nthreads and len(sources) > 0:
            count += 1
            print "Starting %i of %i jobs; %i running jobs" % (count, nsources, len(jobs))
            source = sources.pop()
            output = new_filename(source, dst_dir)
            if not os.path.exists(output):
                mkdirs(os.path.dirname(output))
                tmp_output = output + '.incomplete.' + str(os.getpid()) + '.htmlz'
                cmd = ['ebook-convert', source, tmp_output]
                print "POPEN: ", string.join(cmd, ' ')
                p = Popen(cmd)
                jobs.append((p, tmp_output, output))
            else:
                print "OUTPUT ALREADY EXISTS: Skipping " + source

        # Check for finished jobs
        newjobs = []
        for j in jobs:
            if j[0].poll() is not None:  # Job complete
                # Atomically rename file
                tmp_output = j[1]
                output = j[2]
                print "Completed %s" % (output)
                os.rename(tmp_output, output)
            else:
                newjobs.append(j)
        jobs = newjobs

        # test to see if we are finished
        if len(sources) == 0 and len(jobs) == 0:
            finished = True
        sleep(.5)
    print "Completed All %i of %i jobs" % (count, nsources)


def main(argv):
    parser = OptionParser()
    parser.add_option("-k", "--knowledge",
                      help="Knowledge directory",
                      default="/knowledge")
    parser.add_option("-s", "--stage",
                      help="Stage of processing to perform.  'all', or 1, 2, 3",
                      default='all')
    parser.add_option("--threads",
                      help="Number of processes to run simultaneously",
                      default=4, type='int')
    (options, args) = parser.parse_args()

    if options.stage == 'all':
        stages = [1, 2, 3]
    else:
        stages = [int(options.stage)]

    cache_mirror_dir = os.path.join(options.knowledge, 'data/gutenberg/cache')
    modules_dir = os.path.join(options.knowledge, 'modules')
    epub_dir = os.path.join(modules_dir, 'gutenberg-epub')
    epub_images_dir = os.path.join(modules_dir, 'gutenberg-epub-images')
    htmlz_dir = os.path.join(modules_dir, 'gutenberg-htmlz')
    htmlz_images_dir = os.path.join(modules_dir, 'gutenberg-htmlz-images')

    if not os.path.exists(cache_mirror_dir):
        print "ERROR: could not find gutenberg cache mirror at " + cache_mirror_dir
        return(-1)

    if 1 in stages:
        print "STAGE 1: Copying epubs out of mirror"
        if os.path.exists(epub_dir):
            print epub_dir + " already exists.  You must remove it."
            return -2
        if os.path.exists(epub_images_dir):
            print epub_images_dir + " already exists.  You must remove it."
            return -2
        os.makedirs(epub_dir)
        os.makedirs(epub_images_dir)
        print "Finding epubs in " + cache_mirror_dir + "..."
        epubs = find_files(cache_mirror_dir)
        print "Copying epubs to " + epub_dir + " and " + epub_images_dir + "..."
        progress = progress_bar("Copying " + str(len(epubs)) + " epubs", len(epubs))
        count = 0
        for filename in epubs:
            count += 1
            progress.update(count)
            copy_epub(filename, epub_dir, epub_images_dir)

    if 2 in stages:
        print "STAGE 2: Converting epubs (no images) to htmlz"
        os.makedirs(htmlz_dir)
        epubs = find_files(epub_dir)
        # We shuffle the processing order so we can run from multiple nodes
        # without a lot of collisions
        shuffle(epubs)
        convert(epubs, htmlz_dir, options.threads)

    if 3 in stages:
        print "STAGE 3: Converting epubs including images to htmlz"
        os.makedirs(htmlz_images_dir)
        epubs = find_files(epub_images_dir)
        # We shuffle the processing order so we can run from multiple nodes
        # without a lot of collisions
        shuffle(epubs)
        convert(epubs, htmlz_images_dir, options.threads)


if __name__ == '__main__':
    main(argv)
