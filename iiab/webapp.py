from flask import Flask, request
#from flask.ext.mako import MakoTemplates
from flaskext.babel import Babel

from config import config
import top_views
#import search_views
import map_views
import video_views
import gutenberg
import wikipedia_views
import zim_views
from extensions import db
import sys


def create_app(debug=True, enable_profiler=False, profiler_quiet=False):
    """
    :param debug: whether to configure app for debug
    :param enable_profiler: enable flask profiler, causes function to return ProfilerMiddleware rather than Flask object which can be started by run_simple
    :param profiler_quiet: when profiler enabled sets whether profiler output echoed to stdout
    """
    app = Flask("Iiab")  #, static_folder="static")
    app.root_path += '/iiab'  # something changed so that root_path changed -- work around until identified
    app.url_map.strict_slashes = False
    #app.use_x_sendfile = True

    # Configuration items
    if debug:
        app.debug = True
        app.config['DEBUG'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    base_prefix = config().get('WEBAPP', 'base_prefix')

    # Static blueprint is used during development to serve static files
    #static_blueprint = Blueprint('static_blueprint', __name__, static_folder='static')
    blueprints = [
        #(static_blueprint, base_prefix),
        (top_views.blueprint, base_prefix),
        #(search_views.blueprint, base_prefix),
        (gutenberg.gutenberg, base_prefix + "books"),
        (map_views.blueprint, base_prefix + "maps"),
        (video_views.blueprint, base_prefix + "video"),
        (wikipedia_views.blueprint, base_prefix + "wikipedia"),
        (zim_views.blueprint, base_prefix + "zim")
    ]
    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)

    # set global config variables referenced by SQLAlchemy
    app.config['SQLALCHEMY_ECHO'] = config().getboolean('GUTENBERG', 'sqlalchemy_echo')
    app.config['SQLALCHEMY_DATABASE_URI'] = config().get('GUTENBERG', 'sqlalchemy_database_uri')

    configure_babel(app)
    db.init_app(app)

    print "URL MAP: ", app.url_map

    if enable_profiler:
        from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream
        f = open('profiler.log', 'w')
        if profiler_quiet:
            app = ProfilerMiddleware(app, f)
        else:
            stream = MergeStream(sys.stdout, f)
            app = ProfilerMiddleware(app, stream)

    return app


def configure_babel(app):
    # flask-babel
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        accept_languages = config().getjson('GUTENBERG', 'babel_accept_languages')
        return request.accept_languages.best_match(accept_languages)
