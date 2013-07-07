# Time Profiling Tool
# By Braddock Gaskill, Dec 2012

import logging
log = logging.getLogger(__name__)

from time import time
from functools import wraps
import threading
from os import getpid


start_time = time()


global_active = False

try:
    from psutil import Process
    def get_memory_usage():
        pid = getpid()
        proc = Process(pid)
        mem = proc.get_memory_info()
        return mem
except Exception:
    def get_memory_usage():
        return 0


class TimePro(object):
    def __init__(self):
        global global_active
        self.times = {}
        self.ancestors = []
        self.active = global_active

    def activate(self):
        self.reset()
        self.active = True

    def deactivate(self):
        self.active = False
        self.reset()

    def start(self, name):
        if not self.active:
            return
        if len(self.ancestors) > 0:
            fullname = self.ancestors[-1] + "->" + name
        else:
            fullname = name
        self.ancestors.append(name)
        r = self.times.get(fullname, None)
        if r is None:
            r = {
                'count': 0,
                'total': 0.0,
                'max': -1.0,
                'min': -1.0,
                'mem_res_total': 0,
                'mem_virt_total': 0
            }
        r['count'] += 1
        r['start_time'] = time()
        mem = get_memory_usage()
        r['start_mem_res'] = mem.rss
        r['start_mem_virt'] = mem.vms
        self.times[fullname] = r

    def end(self, name):
        if not self.active:
            return
        self.ancestors.pop()
        if len(self.ancestors) > 0:
            fullname = self.ancestors[-1] + "->" + name
        else:
            fullname = name
        r = self.times[fullname]
        t0 = r['start_time']
        dt = time() - t0
        mem = get_memory_usage()
        r['total'] += dt
        if r['count'] == 1:
            r['max'] = dt
            r['min'] = dt
        r['max'] = max(r['max'], dt)
        r['min'] = min(r['min'], dt)
        r['mem_res_total'] += mem.rss - r['start_mem_res']
        r['mem_virt_total'] += mem.vms - r['start_mem_virt']

    def log_all(self):
        if not self.active:
            return
        log.debug("TOTAL RUNTIME " + str(time() - start_time))
        log.debug("COUNT  TOTAL      AVG     MAX     MIN   dMEM(MB) NAME")
        for name in self.times:
            r = self.times[name]
            dmem = float(r['mem_res_total']) / float(r['count']) / float(1024 * 1024)
            log.debug("%5i  %6.3f  %6.5f  %6.5f  %6.5f  %6i  %s"
                      % (r['count'], r['total'], r['total'] / float(r['count']), r['max'], r['min'], int(dmem), name))

    def reset(self):
        self.times = {}


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
