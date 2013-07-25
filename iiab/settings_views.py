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

    avail_locales =  babel_instance.list_translations()
    lang_names = [ l.language for l in avail_locales ]
    if babel_instance.default_locale.language not in lang_names:
        avail_locales.append(babel_instance.default_locale)
    return avail_locales

def languages_dict():
    langs = {}
    for locale in available_locales():
        lang_code = locale.language
        if locale.territory != None:
            lang_code += "_" + locale.territory
        langs[lang_code] = locale.get_display_name()
    return langs

def current_locale():
    accepted_langs = languages_dict().keys()
    preferred_language = session.get("preferred_language", None)
    if preferred_language != None:
        return preferred_language
    else:
        return request.accept_languages.best_match(accepted_langs)

@blueprint.route('/')
def settings_view():
    "Render the settings page"
    return render_template('settings.html', software_version=__version__)

@blueprint.route('/languages')
def languages_json():
    "Returns a JSON container with the language code and their display name"

    return jsonify(languages_dict())

@blueprint.route('/language', methods = ['GET', 'PUT'])
def user_language():
    """Returns the language code stored in the session dict on a GET,
    sets a new language into the session on a PUT"""

    if request.form.get('language', None) != None:
        lang = request.form['language']
        if not languages_dict().has_key(lang):
            return jsonify(result="not_found")
        else:
            session['preferred_language'] = lang

    # current_locale() will return language from either
    # request header or from session variable
    preferred_lang = current_locale()
    return jsonify(language=preferred_lang)
