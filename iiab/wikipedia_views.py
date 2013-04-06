from flask import Blueprint, render_template

from config import config
from kiwix import parse_library, get_languages


blueprint = Blueprint('wikipedia_views', __name__,
                      template_folder='templates')


@blueprint.route('/')
def wikipedia_view():
    library_xml = config().get('KIWIX', 'library')
    kiwix_url = config().get('KIWIX', 'url')
    library = parse_library(library_xml)
    langs = get_languages(library)
    return render_template('wikipedia_index.html', languages=langs, kiwix_url=kiwix_url)
