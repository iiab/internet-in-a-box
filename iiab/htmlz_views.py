from flask import Blueprint, abort
import zipfile
import os

from config import config

blueprint = Blueprint('htmlz_views', __name__,
                      template_folder='templates', static_folder='static')


def hashdir(n):
    return "%02i" % (int(n) % 100)


def build_htmlz_filename(n):
    return "pg%i.htmlz" % n


@blueprint.route('/<int:pgid>/<path:path>')
def htmlz(pgid, path):
    htmlz_dir = config().get_path('GUTENBERG', 'htmlz_dir')
    htmlz_images_dir = config().get_path('GUTENBERG', 'htmlz_images_dir')
    hashpath = hashdir(pgid)
    filename = build_htmlz_filename(pgid)
    hashpath = os.path.join(hashpath, filename)
    htmlz_path = os.path.join(htmlz_images_dir, hashpath)
    if not os.path.exists(htmlz_path):
        htmlz_path = os.path.join(htmlz_dir, hashpath)
    if not os.path.exists(htmlz_path):
        print "Path not found " + htmlz_path
        abort(404)
    zf = zipfile.ZipFile(htmlz_path)
    f = zf.open(path)
    return f.read()
