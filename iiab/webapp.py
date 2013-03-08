from flask import Flask, request, Blueprint 
from flask.ext.mako import MakoTemplates
from flaskext.babel import Babel

import re

from config import DevelopmentConfig, ProductionConfig
import top_views
import search_views
import gutenberg
from extensions import db


class IiabWebApp(object):
    def __init__(self, debug=True):
        self.app = Flask('IiabWebApp')
        self.app.root_path += '/iiab'  # something changed so that root_path changed -- work around until identified
        self.app.config.from_object(DevelopmentConfig())

        # Configuration items
        if debug:
            self.app.debug = True
            self.app.config['DEBUG'] = True
            self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        base_prefix = '/iiab/'
        static_blueprint = Blueprint('static_blueprint', __name__, static_folder='static') # purpose?
        blueprints = [
                #(static_blueprint, base_prefix),
                #(top_views.blueprint, base_prefix),
                #(search_views.blueprint, base_prefix),
                (gutenberg.gutenberg, base_prefix + "books")
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
            accept_languages = self.app.config.get('ACCEPT_LANGUAGES')
            return request.accept_languages.best_match(accept_languages)


