# Search views
from flask import Blueprint, Response, request, redirect, make_response
import json

from wikipedia_search import WikipediaSearch
from map_search import MapSearch
from config import config

blueprint = Blueprint('search_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route("search_counts", methods=['GET'])
def search_counts_view():
    """Returns JSON containing the counts of matches
    in each major type of search"""
    query = request.args.get('q')
    counts = {}

    # Query wikipedia titles for matches
    ws = WikipediaSearch("wikititles_index")
    counts['wikipedia'] = ws.count(query)
    # Add additional search types here

    # Dump all matches to JSON
    j = json.dumps(counts, indent=4)
    return Response(j, mimetype='application/json')


@blueprint.route('search_wikipedia', methods=['GET'])
def search_wikipedia_view():
    """Return JSON containing search results for
    Wikipedia index"""
    query = request.args.get('q')
    pagelen = request.args.get('pagelen', 0, int)
    page = request.args.get('page', 1, int)
    ws = WikipediaSearch("wikititles_index")
    results = ws.search(query, pagelen=pagelen, page=page)
    j = json.dumps(results, indent=4)
    return Response(j, mimetype='application/json')

@blueprint.route('search_maps', methods=['GET'])
def search_map_view():
    query = request.args.get('q')
    pagelen = request.args.get('pagelen', 0, int)
    page = request.args.get('page', 1, int)
    path = config().get_path('OSM', 'osm_search_dir')
    ms = MapSearch(path)
    results = ms.search(query, pagelen=pagelen, page=page)
    j = json.dumps(results, indent=4)
    return Response(j, mimetype='application/json')
