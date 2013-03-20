#!/usr/bin/env python
"""Script to convert all videos below a directory
to a phone-friendly format"""

from subprocess import Popen, check_call
from optparse import OptionParser
import os
import string
from time import sleep
from random import shuffle


def call2(cmd):
    print "CALL: " + string.join(cmd, ' ')
    check_call(cmd)


def convert_command_old(input_filename, output_filename,
                        async='200', resolution='480x320', vcodec='mpeg4',
                        acodec='libfaac', bitrate='250k', ar='16000',
                        ab='32000'):
    """REMOVE: This converts to a format I commonly use under Android,
    but it is not standard for web streaming"""
    cmd = ['ffmpeg',
           '-i', input_filename,
           '-async', async,
           '-s', resolution,
           '-vcodec', vcodec,
           '-acodec', acodec,
           '-b', bitrate,
           '-ar', ar,
           '-ab', ab,
           '-ac', '1',
           '-r', '12.5',
           '-loglevel', 'error',
           output_filename]
    return cmd


def convert_command(input_filename, output_filename,
                    vcodec='libx264'):
    """Convert to H.264 format"""
    cmd = ['ffmpeg',
           '-i', input_filename,
           '-vcodec', vcodec,
           output_filename,
           '-loglevel', 'error']
    return cmd


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


def new_filename(old_filename, dst_dir, ext):
    return os.path.join(dst_dir, os.path.splitext(old_filename)[0] + ext)


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


def convert(sources, src_dir, dst_dir, nthreads):
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
            output = new_filename(source, dst_dir, '.m4v')
            if not os.path.exists(output):
                mkdirs(os.path.dirname(output))
                tmp_output = output + '.incomplete.' + str(os.getpid()) + '.m4v'
                cmd = convert_command(full_source, tmp_output)
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


parser = OptionParser()
parser.add_option("--extension",
                  help="Extension of files of interest",
                  default=None)
parser.add_option("--threads",
                  help="Number of processes to run simultaneously",
                  default=1, type='int')
(options, args) = parser.parse_args()

if len(args) != 2:
    parser.error("ERROR: Expected <src> and <dst> directories")

src_dir = args[0]
dst_dir = args[1]

assert(src_dir != dst_dir)
if not os.path.exists(src_dir):
    parser.error("Source directory does not exist: " + src_dir)

sources = find(src_dir, options.extension)

# We shuffle the processing order so we can run from multiple nodes
# without a lot of collisions
shuffle(sources)

convert(sources, src_dir, dst_dir, options.threads)
