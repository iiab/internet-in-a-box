from flask import Blueprint, render_template, session, jsonify

from config import config

blueprint = Blueprint('settings', __name__,
                      template_folder='templates', static_folder='static')

def set_babel(babel_inst):
    global babel_instance
    babel_instance = babel_inst

def available_locales():
    "Returns a list of locales with translations available as well as the default locale"
    return babel_instance.list_translations() + [babel_instance.default_locale]

@blueprint.route('/')
def settings_view():
    return render_template('settings.html')

@blueprint.route('/languages')
def languages_json():
    "Returns a JSON container with the language code and their display name"

    trans_dict = { l.language: l.get_display_name() for l in available_locales() }
    return jsonify(trans_dict)

@blueprint.route('/language')
def user_language():
    query = None
    if query:
        trans_codes = [ l.language for l in available_locales() ]
        if lang not in trans_codes:
            return jsonify(result="not_found")
        else:
            session['preferred_language'] = lang

    preferred_lang = session.get('preferred_language', '')
    return jsonify(language=preferred_lang)
