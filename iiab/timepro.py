# Time Profiling Tool
# By Braddock Gaskill, Dec 2012

import logging
log = logging.getLogger(__name__)

from time import time
from functools import wraps
import threading
from os import getpid


global_active = False

try:
    from psutil import Process

    def get_memory_usage():
        pid = getpid()
        proc = Process(pid)
        mem = proc.get_memory_info()
        return (mem.rss, mem.vms)
except Exception:
    def get_memory_usage():
        return (0, 0)


class TimePro(object):
    def __init__(self):
        global global_active
        self.active = global_active
        self.current = None
        self.reset()

    def activate(self):
        self.reset()
        self.active = True

    def deactivate(self):
        self.active = False
        self.reset()

    def start_record(self, name, r):
        if r is None:
            r = {
                'name': name,
                'count': 0,
                'total': 0.0,
                'max': -1.0,
                'min': -1.0,
                'mem_res_total': 0,
                'mem_virt_total': 0,
                'parent': self.current,
                'children': {}
            }
        r['count'] += 1
        r['start_time'] = time()
        (rss, vms) = get_memory_usage()
        r['start_mem_res'] = rss
        r['start_mem_virt'] = vms
        return r

    def start(self, name):
        if not self.active:
            return
        if self.current is not None:
            r = self.current['children'].get(name, None)
        else:
            r = None
        r = self.start_record(name, r)
        self.current = r
        if r['parent'] is not None:
            r['parent']['children'][name] = r

    def end_record(self, r):
        t0 = r['start_time']
        dt = time() - t0
        r['total'] += dt
        if r['count'] == 1:
            r['max'] = dt
            r['min'] = dt
        r['max'] = max(r['max'], dt)
        r['min'] = min(r['min'], dt)
        rss, vms = get_memory_usage()
        r['mem_res_total'] += rss - r['start_mem_res']
        r['mem_virt_total'] += vms - r['start_mem_virt']

    def end(self, name):
        if not self.active:
            return
        r = self.current
        if r['name'] != name:
            log.warning("Timepro got mismatched start/end block, expected %s but got %s" % (r['name'], name))
            return
        self.end_record(r)
        self.current = r['parent']

    def log_record(self, r, level=0):
        indent = " " * level
        dmem = float(r['mem_res_total']) / float(r['count']) / float(1024 * 1024)
        log.debug("%5i  %6.3f  %6.5f  %6.5f  %6.5f  %6i  %s%s"
                  % (r['count'], r['total'], r['total'] / float(r['count']), r['max'], r['min'], int(dmem), indent, r['name']))

    def log_children(self, r, level=0):
        children = r['children'].values()
        children.sort(key=lambda x: -x['total'])
        for child in children:
            self.log_record(child, level + 1)
            self.log_children(child, level + 1)

    def log_all(self):
        if not self.active:
            return
        log.debug("SINCE TIMER RESET %6.3f sec" % (time() - self.reset_time))
        log.debug("COUNT  TOTAL      AVG     MAX     MIN   dMEM(MB) NAME")
        self.log_children(self.root)

    def reset(self):
        self.current = self.start_record("TOTAL", None)
        self.root = self.current
        self.reset_time = time()


threadlocal = threading.local()


def timepro():
    """Get the timepro singleton for this thread.
    Create a new instance if it doesn't exist for this thread."""
    v = getattr(threadlocal, 'timepro', None)
    if v is None:
        threadlocal.timepro = TimePro()
    return threadlocal.timepro


def start(name):
    """Start a named timer"""
    timepro().start(name)


def end(name):
    """Stop a named timer"""
    timepro().end(name)


def log_all():
    """Log all time profiling information for this thread"""
    timepro().log_all()


def profile():
    """This is a decorator you can wrap functions in to get
    timing information"""
    def wrapper1(fn):
        @wraps(fn)
        def wrapper2(*args, **kwargs):
            timepro().start(fn.func_name)
            r = fn(*args, **kwargs)
            timepro().end(fn.func_name)
            return r
        return wrapper2
    return wrapper1


def profile_and_print():
    """This is a decorator you can wrap functions in to get
    timing information"""
    def wrapper1(fn):
        @wraps(fn)
        def wrapper2(*args, **kwargs):
            timepro().start(fn.func_name)
            r = fn(*args, **kwargs)
            timepro().end(fn.func_name)
            timepro().log_all()
            return r
        return wrapper2
    return wrapper1


def reset():
    """Reset all timers for this thread"""
    timepro().reset()
