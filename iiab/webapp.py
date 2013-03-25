from flask import Flask, request, Blueprint
from flask.ext.mako import MakoTemplates
from flaskext.babel import Babel

from config import config
import top_views
import search_views
import map_views
import gutenberg
from extensions import db


class IiabWebApp(object):
    def __init__(self, debug=True):
        self.app = Flask('IiabWebApp')
        self.app.root_path += '/iiab'  # something changed so that root_path changed -- work around until identified

        # Configuration items
        if debug:
            self.app.debug = True
            self.app.config['DEBUG'] = True
            self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        base_prefix = '/iiab/'
        # Static blueprint is used during development to serve static files
        static_blueprint = Blueprint('static_blueprint', __name__, static_folder='static')
        blueprints = [
            (static_blueprint, base_prefix),
            (top_views.blueprint, base_prefix),
            #(search_views.blueprint, base_prefix),
            (gutenberg.gutenberg, base_prefix + "books"),
            (map_views.blueprint, base_prefix + "maps")
        ]
        for blueprint, prefix in blueprints:
            self.app.register_blueprint(blueprint, url_prefix=prefix)

        #self.configure_mako_to_replace_jinja2()

        self.configure_babel()
        db.init_app(self.app)

    def configure_mako_to_replace_jinja2(self):
        # Ensure all templates are html escaped to guard against xss exploits
        self.app.config['MAKO_DEFAULT_FILTERS'] = ['h', 'unicode']
        self.mako = MakoTemplates(self.app)

    def configure_babel(self):
        # flask-babel
        babel = Babel(self.app)

        @babel.localeselector
        def get_locale():
            accept_languages = config().getjson('GUTENBERG', 'babel_accept_languages')
            return request.accept_languages.best_match(accept_languages)
