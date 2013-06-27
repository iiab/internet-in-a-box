# ZIM file URL views (for Wikipedia)
import os
import re

from flask import Blueprint, Response, render_template, request, flash, url_for
from flaskext.babel import gettext 

from zimpy import ZimFile
from config import config

from .endpoint_description import EndPointDescription
import pagination_helper

DEFAULT_RESULTS_PER_PAGE = 20

blueprint = Blueprint('zim_views', __name__,
                      template_folder='templates', static_folder='static')

def load_zim_file(humanReadableId):
    zim_dir = config().get_path("ZIM", "wikipedia_dir")
    zim_fn = os.path.join(zim_dir, humanReadableId + ".zim")
    return ZimFile(zim_fn)

def replace_paths(top_url, html):
    replace = u"\\1\\2" + top_url + "/\\3/"
    html = re.sub(u'(href|src)(=["\']/)([A-Z\-])/', replace, html)
    html = re.sub(u'(@import[ ]+)(["\']/)([A-Z\-])/', replace, html)
    return html

@blueprint.route('/<humanReadableId>')
def zim_main_page_view(humanReadableId):
    """Returns the main page of the zim file"""
    zimfile = load_zim_file(humanReadableId)
    try:
        article, mimetype, ns = zimfile.get_main_page()
        html = mangle_article(article, mimetype, humanReadableId)
        return Response(html, mimetype=mimetype)
    except OSError as e:
        html = "<html><body>"
        html += "<p>Error accessing article.</p>"
        html += "<p>Exception: " + str(e) + "</p>\n"
        html += "</body></html>"
        return Response(html)


def mangle_article(html, mimetype, humanReadableId):
    if mimetype in ['text/html; charset=utf-8', 'stylesheet/css', 'text/html']:
        try:
            html = html.decode('utf-8')
        except UnicodeDecodeError:
            try:
                print "utf-8 decoding failed, falling back to latin1"
                html = html.decode('latin1')
            except:
                print "utf-8 and latin1 decoding failed"
                return html
        html = replace_paths("iiab/zim/" + humanReadableId, html)
    return html


@blueprint.route('/<humanReadableId>/<namespace>/<path:url>')
def zim_view(humanReadableId, namespace, url):
    zimfile = load_zim_file(humanReadableId)
    article, mimetype, ns = zimfile.get_article_by_url(namespace, url)
    html = mangle_article(article, mimetype, humanReadableId)
    return Response(html, mimetype=mimetype)


@blueprint.route('/iframe/<humanReadableId>')
def iframe_main_page_view(humanReadableId):
    url = url_for('zim_views.zim_main_page_view', humanReadableId=humanReadableId)
    return render_template('zim/iframe.html', url=url, humanReadableId=humanReadableId)

@blueprint.route('/iframe/<humanReadableId>/<namespace>/<path:url>')
def iframe_view(humanReadableId, namespace, url):
    url = url_for('zim_views.zim_view', humanReadableId=humanReadableId, namespace=namespace, url=url)
    return render_template('zim/iframe.html', url=url, humanReadableId=humanReadableId)

def paginated_search(humanReadableId, query_text, page=1, pagelen=DEFAULT_RESULTS_PER_PAGE):
    zimfile = load_zim_file(humanReadableId)
    matched_results = []
    for item in zimfile.get_all_articles_info():
        if re.search(query_text, item['title'], re.IGNORECASE):
            matched_results.append(item)

    paginate = pagination_helper.Pagination(page, pagelen, len(matched_results), matched_results)
    return (paginate, None)

@blueprint.route('/iframe/search/<humanReadableId>')
def iframe_search(humanReadableId):
    url = url_for('zim_views.search', humanReadableId=humanReadableId, **request.args)
    return render_template('zim/iframe.html', url=url, humanReadableId=humanReadableId)

@blueprint.route('/search/<humanReadableId>')
def search(humanReadableId):
    query = request.args.get('q', '').strip()
    pagination = None
    if query:
        page = int(request.args.get('page', 1))
        (pagination, suggestion) = paginated_search(humanReadableId, query, page)
    else:
        flash(gettext('Please input keyword(s)'), 'error')
    return render_template('zim/search.html', humanReadableId=humanReadableId, pagination=pagination, suggestion=suggestion, keywords=query, endpoint_desc=EndPointDescription('zim_views.search', {'humanReadableId':humanReadableId}))
