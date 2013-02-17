# Misc utility functions
# By Braddock Gaskill, Feb 2013


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
