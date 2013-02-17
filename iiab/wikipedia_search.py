# Internet-in-a-Box System
# By Braddock Gaskill, 16 Feb 2013
from whoosh.index import open_dir
from whoosh.qparser import QueryParser


class WikipediaSearch(object):
    def __init__(self, index_dir):
        """Initialize a search object.
        index_dir is the Whoosh index directory to use."""
        self.index_dir = index_dir

    def search(self, query, page=1, pagelen=20):
        """Return a sorted list of results.
        pagelen specifies the number of hits per page.
        page specifies the page of results to return (first page is 1)
        Set pagelen = None to retrieve all results.
        """
        query = unicode(query)  # Must be unicode
        ix = open_dir(self.index_dir)
        with ix.searcher() as searcher:
            query = QueryParser("title", ix.schema).parse(query)
            if pagelen is not None:
                results = searcher.search_page(query, page, pagelen=pagelen,
                                               sortedby="score", reverse=True)
            else:
                results = searcher.search(query, limit=None,
                                          sortedby="score", reverse=True)
            r = [x.items() for x in results]
        ix.close()
        return r

    def count(self, query):
        """Return total number of matching documents in index"""
        query = unicode(query)  # Must be unicode
        ix = open_dir(self.index_dir)
        with ix.searcher() as searcher:
            query = QueryParser("title", ix.schema).parse(query)
            results = searcher.search(query)
            n = len(results)
        ix.close()
        return n
