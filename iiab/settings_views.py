from flask import Blueprint, request, render_template, session, jsonify
from config import config
from iiab import __version__

blueprint = Blueprint('settings', __name__,
                      template_folder='templates', static_folder='static')

def set_babel(babel_inst):
    "Called from app initialization to set a variable containing the Babel instance"

    global babel_instance
    babel_instance = babel_inst

def available_locales():
    "Returns a list of locales with translations available as well as the default locale"
    return babel_instance.list_translations() + [babel_instance.default_locale]

@blueprint.route('/')
def settings_view():
    "Render the settings page"
    return render_template('settings.html', software_version=__version__)

@blueprint.route('/languages')
def languages_json():
    "Returns a JSON container with the language code and their display name"

    trans_dict = { l.language: l.get_display_name() for l in available_locales() }
    return jsonify(trans_dict)

@blueprint.route('/language', methods = ['GET', 'PUT'])
def user_language():
    """Returns the language code stored in the session dict on a GET,
    sets a new language into the session on a PUT"""

    if request.form.get('language', None) != None:
        lang = request.form['language']
        trans_codes = [ l.language for l in available_locales() ]
        if lang not in trans_codes:
            return jsonify(result="not_found")
        else:
            session['preferred_language'] = lang

    preferred_lang = session.get('preferred_language', '')
    return jsonify(language=preferred_lang)
