# Misc utility functions
# By Braddock Gaskill, Feb 2013
from subprocess import Popen, PIPE
import re


def whoosh2dict(hits):
    """Convert from whoosh results list to
    a list of dictionaries with a key/value pair for
    each schema column"""
    m = []
    for hit in hits:
        d = {}
        for k, v in hit.items():
            d[k] = v
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
