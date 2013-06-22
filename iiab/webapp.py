from flask import Flask, request
#from flask.ext.mako import MakoTemplates
from flaskext.babel import Babel
from flask.ext.autoindex import AutoIndex
import os

from config import config
import top_views
#import search_views
import map_views
import video_views
import gutenberg
import wikipedia_views
import zim_views
import htmlz_views
from extensions import db
import sys


def create_app(debug=True, enable_profiler=False, profiler_quiet=False):
    """
    :param debug: whether to configure app for debug
    :param enable_profiler: enable flask profiler, causes function to return ProfilerMiddleware rather than Flask object which can be started by run_simple
    :param profiler_quiet: when profiler enabled sets whether profiler output echoed to stdout
    """
    app = Flask("iiab")
    app.url_map.strict_slashes = False
    app.use_x_sendfile = config().getboolean('WEBAPP', 'use_x_sendfile')

    # Configuration items
    if debug:
        app.debug = True
        app.config['DEBUG'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    base_prefix = config().get('WEBAPP', 'base_prefix')

    blueprints = [
        (top_views.blueprint, base_prefix),
        #(search_views.blueprint, base_prefix),
        (gutenberg.gutenberg, base_prefix + "books"),
        (map_views.blueprint, base_prefix + "maps"),
        (video_views.blueprint, base_prefix + "video"),
        (wikipedia_views.blueprint, base_prefix + "wikipedia"),
        (zim_views.blueprint, base_prefix + "zim"),
        (htmlz_views.blueprint, base_prefix + "htmlz")
    ]
    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)

    # set global config variables referenced by SQLAlchemy
    app.config['SQLALCHEMY_ECHO'] = config().getboolean('GUTENBERG', 'sqlalchemy_echo')
    database_path = config().get_path('GUTENBERG', 'sqlalchemy_database_uri')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath(database_path)
    print 'SQLALCHEMY_URI', app.config['SQLALCHEMY_DATABASE_URI']

    configure_babel(app)
    db.init_app(app)

    if enable_profiler:
        from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream
        f = open('profiler.log', 'w')
        if profiler_quiet:
            app = ProfilerMiddleware(app, f)
        else:
            stream = MergeStream(sys.stdout, f)
            app = ProfilerMiddleware(app, stream)

    # Auto Index the software repository
    autoindex = AutoIndex(app, add_url_rules=False)
    # FIXME: this should be done more elegantly -bcg'13

    @app.route(base_prefix + 'software/<path:path>')
    @app.route(base_prefix + 'software')
    def software_view(path='.'):
        software_dir = config().get_path('SOFTWARE', 'software_dir')
        return autoindex.render_autoindex(path, browse_root=software_dir, endpoint='software_view')

    print "URL MAP: ", app.url_map

    return app


def configure_babel(app):
    # flask-babel
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        accept_languages = config().get_json('GUTENBERG', 'babel_accept_languages')
        return request.accept_languages.best_match(accept_languages)
