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


class IiabWebApp(object):
    def __init__(self, debug=True, enable_profiler=False, profiler_quiet=False):
        """
        :param debug: whether to configure app for debug
        :param enable_profiler: enable flask profiler, causes function to return ProfilerMiddleware rather than Flask object which can be started by run_simple
        :param profiler_quiet: when profiler enabled sets whether profiler output echoed to stdout
        """
        self.app = Flask('IiabWebApp')
        self.app.root_path += '/iiab'  # something changed so that root_path changed -- work around until identified
        self.app.url_map.strict_slashes = False
        self.app.use_x_sendfile = True

        # Configuration items
        if debug:
            self.app.debug = True
            self.app.config['DEBUG'] = True
            self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
            self.app.register_blueprint(blueprint, url_prefix=prefix)

        #self.configure_mako_to_replace_jinja2()

        # set global config variables referenced by SQLAlchemy
        self.app.config['SQLALCHEMY_ECHO'] = config().getboolean('GUTENBERG', 'sqlalchemy_echo')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = config().get('GUTENBERG', 'sqlalchemy_database_uri')

        self.configure_babel()
        db.init_app(self.app)

        print "URL MAP: ", self.app.url_map

        if enable_profiler:
            from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream
            f = open('profiler.log', 'w')
            if profiler_quiet:
                self.app = ProfilerMiddleware(self.app, f)
            else:
                stream = MergeStream(sys.stdout, f)
                self.app = ProfilerMiddleware(self.app, stream)

    # REMOVE
    #def configure_mako_to_replace_jinja2(self):
    #    # Ensure all templates are html escaped to guard against xss exploits
    #    self.app.config['MAKO_DEFAULT_FILTERS'] = ['h', 'unicode']
    #    self.mako = MakoTemplates(self.app)

    def configure_babel(self):
        # flask-babel
        babel = Babel(self.app)

        @babel.localeselector
        def get_locale():
            accept_languages = config().getjson('GUTENBERG', 'babel_accept_languages')
            return request.accept_languages.best_match(accept_languages)
