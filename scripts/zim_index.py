#!/usr/bin/env python
"""Script to automatically build indices for zim files"""

from subprocess import Popen, check_call
from optparse import OptionParser
import os
import string
from time import sleep
from datetime import datetime
from random import shuffle


def call2(cmd):
    print "CALL: " + string.join(cmd, ' ')
    check_call(cmd)


def index_command(kiwix_bin, input_filename, output_dirname):
    """Index zim file"""
    cmd = [os.path.join(kiwix_bin, 'kiwix-index'),
           #'-v',
           input_filename,
           output_dirname]
    return cmd


def manage_command(kiwix_bin, libraryfile, zimfile, indexfile):
    cmd = [os.path.join(kiwix_bin, 'kiwix-manage'),
           libraryfile,
           'add',
           zimfile,
           '-i', indexfile]
    return cmd


def timestamp():
    return datetime.now().strftime("%H:%M")


def find(root, extension=None):
    """File files with specified extension under root"""
    found = []
    cwd = os.getcwd()
    os.chdir(root)
    for path, dirs, files in os.walk('.'):
        path = path[2:]  # Remove './'
        for f in files:
            if extension is None or f[-len(extension):] == extension:
                found.append(os.path.join(path, f))
    os.chdir(cwd)
    return found


def new_dirname(old_filename, dst_dir):
    return os.path.join(dst_dir, os.path.splitext(old_filename)[0])


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


def convert(sources, src_dir, dst_dir, nthreads, kiwix_bin_dir):
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
            full_source = os.path.join(src_dir, source)
            output = new_dirname(source, dst_dir)
            if not os.path.exists(output):
                tmp_output = output + '.incomplete.' + str(os.getpid())
                cmd = index_command(kiwix_bin_dir, full_source, tmp_output)
                #print timestamp() + " RUN: ", string.join(cmd, ' ')
                print timestamp() + " RUN: ", source
                p = Popen(cmd)
                jobs.append((p, tmp_output, output))
            else:
                print "OUTPUT ALREADY EXISTS: Skipping " + source

        # Check for finished jobs
        newjobs = []
        for j in jobs:
            if j[0].poll() is not None:  # Job complete
                if j[0].poll() == 0:
                    # Atomically rename file
                    tmp_output = j[1]
                    output = j[2]
                    print timestamp() + " Completed %s" % (output)
                    os.rename(tmp_output, output)
                else:
                    print "JOB FAILED WITH RETURN CODE " + str(j[0].poll()) + ": " + output
            else:
                newjobs.append(j)
        jobs = newjobs

        # test to see if we are finished
        if len(sources) == 0 and len(jobs) == 0:
            finished = True
        sleep(.5)
    print "Completed All %i of %i jobs" % (count, nsources)


parser = OptionParser()
parser.add_option("--kiwix_bin_dir",
                  help="Dir of kiwix-index binary",
                  default="/knowledge/packages/bin-amd64/kiwix/bin")
parser.add_option("--threads",
                  help="Number of processes to run simultaneously",
                  default=1, type='int')
parser.add_option("--index", default=False, dest='index',
                  action='store_true', help="Command to build indices for all zim files")
parser.add_option("--catalog", default=False, dest='catalog',
                  action='store_true',
                  help="Command to build a library file for all zim files and their indices")
parser.add_option("--library", default="library.xml", help="Location of library.xml file")
(options, args) = parser.parse_args()

if len(args) != 2:
    parser.error("ERROR: Expected <src> and <dst> directories")

src_dir = args[0]
dst_dir = args[1]

assert(src_dir != dst_dir)
if not os.path.exists(src_dir):
    parser.error("Source directory does not exist: " + src_dir)
if not os.path.exists(dst_dir):
    parser.error("Destination index directory does not exist: " + dst_dir)
if not options.index and not options.catalog:
    parser.error("Must specify at least one of --index or --catalog commands")
sources = find(src_dir, '.zim')

# We shuffle the processing order so we can run from multiple nodes
# without a lot of collisions
shuffle(sources)

if options.index:
    convert(sources, src_dir, dst_dir, options.threads, options.kiwix_bin_dir)

if options.catalog:
    for source in sources:
        full_source = os.path.join(src_dir, source)
        index = new_dirname(source, dst_dir)
        if not os.path.exists(full_source):
            raise full_source + " does not exist"
        if not os.path.exists(index):  # More likely
            print "ERROR: " + index + " does not exist"
        cmd = manage_command(options.kiwix_bin_dir, options.library, full_source, index)
        print "RUN: ", string.join(cmd, ' ')
        p = Popen(cmd)
        r = p.wait()
        if r != 0:
            raise "Error processing command, returned " + str(r) + " : " + string.join(cmd, ' ')
print "Processing Complete"
