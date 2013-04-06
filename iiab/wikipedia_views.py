from flask import Blueprint, render_template

from config import config
from kiwix import parse_library, get_languages


blueprint = Blueprint('wikipedia_views', __name__,
                      template_folder='templates')


@blueprint.route('/library/<language>')
def library_view(language=None):
    library_xml = config().get('KIWIX', 'library')
    kiwix_url = config().get('KIWIX', 'url')
    library = parse_library(library_xml)
    if language is not None:
        library = filter(lambda x: x.get('language') == language, library)
    if language is None:
        language_label = 'All Languages'
    elif len(library) > 0:
        language_label = library[0]['languageEnglish']
    else:
        language_label = 'No Matches'
    return render_template('kiwix_index.html', library=library, kiwix_url=kiwix_url, language=language_label)


@blueprint.route('/language/')
def language_view():
    library_xml = config().get('KIWIX', 'library')
    library = parse_library(library_xml)
    langs = get_languages(library)
    return render_template('wikipedia_languages.html', languages=langs)


@blueprint.route('/')
def wikipedia_view():
    library_xml = config().get('KIWIX', 'library')
    kiwix_url = config().get('KIWIX', 'url')
    library = parse_library(library_xml)
    langs = get_languages(library)
    return render_template('wikipedia_index.html', languages=langs, kiwix_url=kiwix_url)
