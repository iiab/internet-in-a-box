# Top level URL views
from flask import Blueprint, make_response, render_template, send_file, send_from_directory

from config import config

blueprint = Blueprint('top_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/')
def index():
    error = None
    if config().get_knowledge_dir() is None:
        error = "Could not find knowledge directory containing Internet-in-a-Box dataset.  "
        error += "The configured knowledge_dir path is " + config().get('DEFAULT', 'knowledge_dir')
        error += " and search_for_knowledge_dir is "
        if config().get('DEFAULT', 'search_for_knowledge_dir'):
            error += "ON, so all mounted filesystems were checked."
        else:
            error += "OFF, so other mounted filesystems were NOT checked."
    return render_template("index.html", kiwix_url=config().get('KIWIX', 'url'), error=error)


# This is a hack because of the double //static path issue
@blueprint.route('static/<path:filename>')
def static(filename):
    return blueprint.send_static_file(filename)


@blueprint.route('test')
def test():
    print "TEST"
    return make_response((send_file('/var/www/foo.webm', mimetype="video/webm"), 200, {'Accept-Ranges': 'bytes'}))
