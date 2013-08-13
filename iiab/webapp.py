from flask import Flask, request, url_for, session
from flask.ext.babel import Babel
from flask.ext.autoindex import AutoIndex
import sys
import urlparse

from config import config
import top_views
import search_views
import map_views
import video_views
import gutenberg
import gutenberg_content_views
import wikipedia_views
import zim_views
import settings_views
from babel_patch import babel_patched_load


def create_app(debug=True, enable_profiler=False, profiler_quiet=False):
    """
    :param debug: whether to configure app for debug
    :param enable_profiler: enable flask profiler, causes function to return ProfilerMiddleware rather than Flask object which can be started by run_simple
    :param profiler_quiet: when profiler enabled sets whether profiler output echoed to stdout
    """
    app = Flask("iiab")
    app.url_map.strict_slashes = False
    app.use_x_sendfile = config().getboolean('WEBAPP', 'use_x_sendfile')
    app.secret_key = '1785132b4fd244a2a1ce6ae3f1d978ac'

    # Configuration items
    if debug:
        app.debug = True
        app.config['DEBUG'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    base_prefix = config().get('WEBAPP', 'base_prefix')

    blueprints = [
        (top_views.blueprint, base_prefix),
        (search_views.blueprint, base_prefix),
        (gutenberg.gutenberg, base_prefix + "books"),
        (map_views.blueprint, base_prefix + "maps"),
        (video_views.blueprint, base_prefix + "video"),
        (wikipedia_views.blueprint, base_prefix + "wikipedia"),
        (zim_views.blueprint, base_prefix + "zim"),
        (gutenberg_content_views.blueprint, base_prefix + "books"),
        (settings_views.blueprint, base_prefix + "settings"),
    ]
    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)

    gutenberg.set_flask_app(app)
    gutenberg.init_db()

    configure_babel(app)

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

    #print "URL MAP: ", app.url_map

    # Static handling from http://flask.pocoo.org/mailinglist/archive/2011/8/25/static-files-subdomains/#9237e5b3c217b2875c59daaac4c23487
    app.config['STATIC_ROOT'] = config().get_default('WEBAPP', 'static_url_path', None)

    def static(path):
        root = app.config.get('STATIC_ROOT', None)
        if root is None:  # fallback on the normal way
            return url_for('static', filename=path)
        return urlparse.urljoin(root, path)

    @app.context_processor
    def inject_static():
        return dict(static=static)

    return app


def configure_babel(app):
    # Load additional languages into the babel
    # cache.  We do this so we can add Haitian Creole
    # using french as a model.
    babel_patched_load('cpf')

    # flask-babel
    babel = Babel(app)

    # Wire Babel into the settings
    # and the settings code into Babel
    settings_views.set_babel(babel)
    babel.localeselector(settings_views.current_locale)

    return babel
