# Internet-in-a-Box System
# By Braddock Gaskill, 16 Feb 2013
from utils import whoosh_open_dir_32_or_64
from whoosh.qparser import QueryParser
from whoosh.sorting import ScoreFacet, FunctionFacet
from whoosh.query import Term
from whoosh import scoring, sorting
from flask.ext.sqlalchemy import SQLAlchemy
import os

import map_model
from extensions import db_map
from config import config

from utils import whoosh2dict
import timepro

def init_db(app):
    # setup database access
    if app.config['SQLALCHEMY_BINDS'] is None:
        app.config['SQLALCHEMY_BINDS'] = {}
    database_path = config().get_path('OSM', 'sqlalchemy_database_uri')
    db_uri = 'sqlite:///' + os.path.abspath(database_path)
    app.config['SQLALCHEMY_BINDS'].update({ 'maps': db_uri })
    db_map.init_app(app)
    print app.config['SQLALCHEMY_BINDS']

class FunctionWeighting(scoring.WeightingModel):
    """Scoring helper adapted from whoosh/scoring.py because class of the same name
    and function did not implement the required max_quality method on FunctionScorer"""

    def __init__(self, fn):
        self.fn = fn

    def scorer(self, searcher, fieldname, text, qf=1):
        return self.FunctionScorer(self.fn, searcher, fieldname, text, qf=qf)

    class FunctionScorer(scoring.BaseScorer):
        def __init__(self, fn, searcher, fieldname, text, qf=1):
            self.fn = fn
            self.searcher = searcher
            self.fieldname = fieldname
            self.text = text
            self.qf = qf

        def score(self, matcher):
            return self.fn(self.searcher, self.fieldname, self.text, matcher)

        def max_quality(self):
            return 1.0


class IndexAccessor(object):
    """Helper class to hold open index to avoid performance penalty when opening it on each query

    Supports use with `with` managed context.  If a managed context is not
    used, one must call `open` prior to use

    :attr ix: contains reference to opened whoosh index
    :method search_args: whoosh search method arguments populated with default
                settings.  Augment as needed with update. Expand kwargs when
                passing to search method.
    """
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.ix = None

    def __enter__(self):
        self.open()

    def __exit__(self, type, value, traceback):
        self.close()

    def open(self):
        self.ix = whoosh_open_dir_32_or_64(self.index_dir)

        # Setup sort and collapse facet. Sort based on importance field and then by score.
        # Collapse based on geoid to eliminate duplicate names
        importance_sort_facet = sorting.FieldFacet("importance", reverse=True)
        score = ScoreFacet()
        self.sort_order = [score, importance_sort_facet]
        self.collapse_facet = sorting.FieldFacet('geoid')
        def language_filter(s, docid):
            (lang,score) = s.key_terms([docid], "isolanguage")
            return lang == 'en'
        self.collapse_order_facet = sorting.FunctionFacet(language_filter)

        # Position based scoring. Note position information does not appear to be supported by ngram columns
        def position_score_fn(searcher, fieldname, text, matcher):
            poses = matcher.value_as("positions")
            return 1.0 / (poses[0] + 1)
        self.weighting = FunctionWeighting(position_score_fn)

    def close(self):
        self.ix.close()
        self.ix = None

    def search_args(self, queryObj):
        """Return suitable search parameters for whoosh searcher call.

        :param queryObj: Whoosh Query object to be used as search query
        """
        return {
            'q': queryObj,
            'sortedby': self.sort_order,
            #'collapse': self.collapse_facet,
            #'collapse_limit': 1,
            #'collapse_order': self.collapse_order_facet
        }


class MapSearch(object):
    DEFAULT_LIMIT = 10

    @classmethod
    def init_class(cls, index_dir):
        """Hold search index open as a class variable for performanc reasons

        :param index_dir: directory path containing whoosh index

        While it would be cleaner to create a context in the caller and pass the accessor to MapSearch on instantiation,
        an appropriate outer scope at which to place this has not yet been identified.  Until then attached to the class."""
        cls.ix_helper = IndexAccessor(index_dir)
        cls.ix_helper.open()

    @timepro.profile()
    def search(self, query, page=1, pagelen=20, autocomplete=False):
        """Return a sorted list of results.

        :param page: specifies the page of results to return (first page is 1)
        :param pagelen: specifies the number of hits per page.
            Set pagelen = None or 0 to retrieve up to DEFAULT_MAX results.
        :param autocomplete: flag indicating whether full record or just autocomplete matches should be returned
        """

        if not MapSearch.ix_helper or not MapSearch.ix_helper.ix:
            raise ValueError("Not initialized. Must call init_mod to initialize before use.")

        query = unicode(query)  # Must be unicode
        ix = MapSearch.ix_helper.ix
        with ix.searcher(weighting=MapSearch.ix_helper.weighting) as searcher:
            if autocomplete:
                query = QueryParser("ngram_fullname", ix.schema).parse(query)
            else:
                query = QueryParser("fullname", ix.schema).parse(query)

            args = MapSearch.ix_helper.search_args(query)

            if pagelen is not None and pagelen != 0:
                args.update({
                    'pagenum': page,
                    'pagelen': pagelen
                })
                try:
                    results = searcher.search_page(**args)
                except ValueError, e:  # Invalid page number
                    results = []
            else:
                args.update({
                    'limit': self.DEFAULT_LIMIT
                })
                results = searcher.search(**args)
#            print query, results
            r = whoosh2dict(results)

        # Originally only the names were indexed and geographic information was stored in a companion db.
        # Later, latlon data was added directly to the whoosh db making the db lookup unnecessary
        # Based on the selected name augment the record with the data from the geoinfo db
#        if not autocomplete:
#            for d in r:
#                #print d
#                geoid = d['geoid']
#                info = map_model.GeoInfo.query.filter_by(id=geoid).first()
#                d['latitude'] = info.latitude
#                d['longitude'] = info.longitude
#                d['links'] = map(lambda r: getattr(r, 'link'), map_model.GeoLinks.query.filter_by(geonameid=geoid).all())

        return r

    def count(self, query):
        """Return total number of matching documents in index"""
        query = unicode(query)  # Must be unicode
        ix = MapSearch.ix
        with ix.searcher() as searcher:
            query = QueryParser("fullname", ix.schema).parse(query)
            results = searcher.search(query)
            n = len(results)
        return n

