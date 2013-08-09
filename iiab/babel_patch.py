from babel.localedata import _cache, _cache_lock, load, merge
import os
import pickle

_mydirname = os.path.dirname(__file__)


def babel_patched_load(name, merge_inherited=True):
    # Load additional languages into the babel
    # cache.  We do this so we can add Haitian Creole
    # using french as a model.
    _cache_lock.acquire()
    try:
        data = _cache.get(name)
        if not data:
            # Load inherited data
            if name == 'root' or not merge_inherited:
                data = {}
            else:
                parts = name.split('_')
                if len(parts) == 1:
                    parent = 'root'
                else:
                    parent = '_'.join(parts[:-1])
                data = load(parent).copy()
            filename = os.path.join(_mydirname, '%s.dat' % name)
            fileobj = open(filename, 'rb')
            try:
                if name != 'root' and merge_inherited:
                    merge(data, pickle.load(fileobj))
                else:
                    data = pickle.load(fileobj)
                _cache[name] = data
            finally:
                fileobj.close()
        return data
    finally:
        _cache_lock.release()
