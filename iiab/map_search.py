# Internet-in-a-Box System
# By Braddock Gaskill, 16 Feb 2013
from utils import whoosh_open_dir_32_or_64
from whoosh.qparser import QueryParser
from whoosh.sorting import ScoreFacet, FunctionFacet
from whoosh import sorting
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
    app.config['SQLALCHEMY_BINDS'].update({ 'maps' : db_uri })
    db_map.init_app(app)
    print app.config['SQLALCHEMY_BINDS']

class MapSearch(object):
    DEFAULT_LIMIT = 100

    @classmethod
    def init_class(cls, index_dir):
        """Class level initialize. Initialize search index once for performance reasons"""
        cls.whoosh_index = whoosh_open_dir_32_or_64(index_dir)
        # setup cached fields
        importance_sort_facet = sorting.FieldFacet("importance", reverse=True)
        score = ScoreFacet()
        cls.sort_order = [importance_sort_facet, score]
        cls.collapse_facet = sorting.FieldFacet('geoid')
        def language_filter(s, docid):
            (lang,score) = s.key_terms([docid], "isolanguage")
            return lang == 'en'
        cls.collapse_order_facet = sorting.FunctionFacet(language_filter)

    @timepro.profile()
    def search(self, query, page=1, pagelen=20, autocomplete=False):
        """Return a sorted list of results.
        :param page: specifies the page of results to return (first page is 1)
        :param pagelen: specifies the number of hits per page.
            Set pagelen = None or 0 to retrieve up to DEFAULT_MAX results.
        :param autocomplete: flag indicating whether full record or just autocomplete matches should be returned
        """

        if not self.whoosh_index:
            raise ValueError("Not initialized. Must call init_mod to initialize before use.")

        query = unicode(query)  # Must be unicode
        query = QueryParser("name", self.whoosh_index.schema).parse(query)

        with self.whoosh_index.searcher() as searcher:
            args = {
                'q' : query,
                #'sortedby' : self.sort_order,
                #'collapse' : self.collapse_facet,
                #'collapse_limit' : 1,
                #'collapse_order' : self.collapse_order_facet
            }

            if pagelen is not None and pagelen != 0:
                args.update({
                    'pagenum' : page,
                    'pagelen' : pagelen
                })
                try:
                    results = searcher.search_page(**args)
                except ValueError, e:  # Invalid page number
                    results = []
            else:
                args.update({
                    'limit' : self.DEFAULT_LIMIT
                })
                results = searcher.search(**args)
            print query, results
            r = whoosh2dict(results)
        self.whoosh_index.close()
        if not autocomplete:
            for d in r:
                #print d
                geoid = d['geoid']
                info = map_model.GeoInfo.query.filter_by(id=geoid).first()
                d['latitude'] = info.latitude
                d['longitude'] = info.longitude
                d['links'] = map(lambda r: getattr(r, 'link'), map_model.GeoLinks.query.filter_by(geonameid=geoid).all())

        return r

    def count(self, query):
        """Return total number of matching documents in index"""
        query = unicode(query)  # Must be unicode
        with self.whoosh_index.searcher() as searcher:
            query = QueryParser("title", self.whoosh_index.schema).parse(query)
            results = searcher.search(query)
            n = len(results)
        self.whoosh_index.close()
        return n

