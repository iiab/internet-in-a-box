# Top level URL views
import os
from flask import Blueprint, make_response, render_template, send_file, send_from_directory

from config import config

blueprint = Blueprint('top_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/')
def index():
    return render_template("index.html", kiwix_url=config().get('KIWIX', 'url'))


@blueprint.route('test')
def test():
    print "TEST"
    return make_response((send_file('/var/www/foo.webm', mimetype="video/webm"), 200, {'Accept-Ranges': 'bytes'}))


@blueprint.route('khanvideo/<path:filename>')
def khanvideo_view(filename):
    khanacademy_dir = config().get('VIDEO', 'khanacademy_dir')
    khanlinks = os.path.join(khanacademy_dir, 'khanlinks')
    print "khanlinks = ", khanlinks, " filename = ", filename
    r = send_from_directory(khanlinks, filename)
    return make_response(r, 200, {'Accept-Ranges': 'bytes'})
