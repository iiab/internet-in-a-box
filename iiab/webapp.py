from flask import Flask, Blueprint
from flask.ext.mako import MakoTemplates

import top_views


class IiabWebApp(object):
    def __init__(self, debug=True):
        self.app = Flask('IiabWebApp')

        # Configuration items
        if debug:
            self.app.debug = True
            self.app.config['DEBUG'] = True
            self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        # Ensure all templates are html escaped to guard against xss exploits
        self.app.config['MAKO_DEFAULT_FILTERS'] = ['h', 'unicode']

        static_blueprint = Blueprint('static_blueprint', __name__, static_folder='static')
        self.app.register_blueprint(static_blueprint, url_prefix='/iiab')
        self.app.register_blueprint(top_views.blueprint, url_prefix='/iiab/')
        self.mako = MakoTemplates(self.app)
