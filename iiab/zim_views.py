# ZIM file URL views (for Wikipedia)
from flask import Blueprint, Response

from zim import Library, replace_paths
from config import config

blueprint = Blueprint('zim_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/<humanReadableId>')
def zim_main_page_view(humanReadableId):
    """Returns the main page of the zim file"""
    library_xml = config().get('KIWIX', 'library')
    lib = Library(library_xml)
    zimfile = lib.get_zimfile(humanReadableId)
    info = zimfile.get_info()
    article = zimfile.get_article_by_index(info.get('main page', 1))
    html = mangle_article(article, humanReadableId)
    return Response(html, mimetype=article.mime_type)


def mangle_article(article, humanReadableId):
    html = article.data
    if article.mime_type in ['text/html; charset=utf-8', 'stylesheet/css']:
        try:
            html = html.decode('utf-8')
        except UnicodeDecodeError:
            try:
                html = html.decode('latin1')
            except:
                return html
        html = replace_paths("iiab/zim/" + humanReadableId, html)
    return html


@blueprint.route('/<humanReadableId>/<namespace>/<path:url>')
def zim_view(humanReadableId, namespace, url):
    library_xml = config().get('KIWIX', 'library')
    lib = Library(library_xml)
    article = lib.get_article_by_url(humanReadableId, namespace, url)
    html = mangle_article(article, humanReadableId)
    return Response(html, mimetype=article.mime_type)
