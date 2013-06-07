# OpenStreetMap URL views
from flask import Blueprint, Response
import os

from osmtile import TileSet, meta_load_one
from config import config

blueprint = Blueprint('map_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/tile/<int:z>/<int:x>/<int:y>.png')
def tile(z, x, y):
    path = os.path.join(config().get_path('OSM', 'openstreetmap_dir'), 'mod_tile64')
    tileset = TileSet(path, 'default', METATILE=64, flatter=True)
    tile = meta_load_one(tileset, x, y, z)
    return Response(tile, mimetype='image/png')
