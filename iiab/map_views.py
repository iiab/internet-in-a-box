# OpenStreetMap URL views
from flask import Blueprint, Response, request, redirect, make_response, render_template

from osmtile import TileSet, meta_load_one

blueprint = Blueprint('map_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/tile/<int:z>/<int:x>/<int:y>.png')
def tile(z, x, y):
    print "Hello tile"
    tileset = TileSet('/knowledge/processed/mod_tile', 'default', METATILE=8)
    tile = meta_load_one(tileset, x, y, z)
    return Response(tile, mimetype='image/png')
