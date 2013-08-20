# Misc utility functions
# By Braddock Gaskill, Feb 2013
from subprocess import Popen, PIPE
import re
import sys


def is32bit():
    """Returns true if this is a 32-bit architecture, or false if 64-bit"""
    return not sys.maxsize > 2 ** 32


def whoosh_open_dir_32_or_64(dirname, indexname=None, readonly=False):
    """Convenience function for opening an index in a directory based on
    open_dir in whoosh.index.
    This functions automatically detects if the machine is 32-bit or 64-bit,
    and turns off mmap if only 32-bit to avoid address space exhaustion
    on large indices.

    :param dirname: the path string of the directory in which to create the
        index.
    :param indexname: the name of the index to create; you only need to specify
        this if you have multiple indexes within the same storage object.
    """

    from whoosh.filedb.filestore import FileStorage
    from whoosh.index import _DEF_INDEX_NAME

    supports_mmap = not is32bit()
    if indexname is None:
        indexname = _DEF_INDEX_NAME

    storage = FileStorage(dirname, readonly=readonly, supports_mmap=supports_mmap)
    return storage.open_index(indexname)


def whoosh2dict(hits):
    """Convert from whoosh results list to
    a list of dictionaries with a key/value pair for
    each schema column"""
    m = []
    for hit in hits:
        # use dict of list comprehension rather than dict comprehension for py2.6 compat
        d = dict((k, v) for (k, v) in hit.items())
        m.append(d)
    return m


def run_mount():
    """Run the mount command and return the parsed results"""
    p = Popen(['mount'], stdout=PIPE)
    data = p.stdout.readlines()
    regex = '(.*) on (.*) type ([^ ]*) (.*)\n'
    r = []
    for line in data:
        m = re.match(regex, line)
        if m is not None:
            r.append(m.groups())
    return r


def mdns_resolve(mdnsname):
    p = Popen(['avahi-resolve', '-4', '-n', mdnsname], stdout=PIPE)
    data = p.stdout.read()
    if data == '':  # Failed to resolve
        return None
    data = data.rstrip()
    fields = data.split("\t")
    return fields[1]
