# OpenStreetMap URL views
from flask import Blueprint, Response

from zim import Library, replace_paths
from config import config

blueprint = Blueprint('zim_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/<humanReadableId>/<namespace>/<path:url>')
def zim_view(humanReadableId, namespace, url):
    library_xml = config().get('KIWIX', 'library')
    lib = Library(library_xml)
    data = lib.get_article_by_url(humanReadableId, namespace, url)
    data = replace_paths("iiab/zim/" + humanReadableId, data)
    return data
