# ZIM file URL views (for Wikipedia)
import os
import re

from flask import Blueprint, Response, render_template, request, flash, url_for, abort
from flask.ext.babel import gettext as _
from whoosh import scoring, sorting

from zimpy import ZimFile
from config import config

from whoosh_search import paginated_search
from utils import whoosh_open_dir_32_or_64

from .endpoint_description import EndPointDescription

DEFAULT_RESULTS_PER_PAGE = 20

blueprint = Blueprint('zim_views', __name__,
                      template_folder='templates', static_folder='static')

def load_zim_file(humanReadableId):
    zim_dir = config().get_path("ZIM", "wikipedia_zim_dir")
    zim_fn = os.path.join(zim_dir, humanReadableId + ".zim")
    return ZimFile(zim_fn)

def replace_paths(top_url, html):
    replace = u"\\1\\2" + top_url + "/\\3/"
    html = re.sub(u'(href|src)(=["\']/)([A-Z\-])/', replace, html)
    html = re.sub(u'(@import[ ]+)(["\']/)([A-Z\-])/', replace, html)
    return html

def mangle_article(html, mimetype, humanReadableId):
    if mimetype in ['text/html; charset=utf-8', 'stylesheet/css', 'text/html']:
        try:
            html = html.decode('utf-8','replace')
        except UnicodeDecodeError:
            try:
                print "utf-8 decoding failed, falling back to latin1"
                html = html.decode('latin1')
            except:
                print "utf-8 and latin1 decoding failed"
                return html
        html = replace_paths("iiab/zim/" + humanReadableId, html)
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
        html += "<p>" + _('Error accessing article.') + "</p>"
        html += "<p>" + _('Exception: %(error)s', error=str(e)) + "</p>\n"
        html += "</body></html>"
        return Response(html)

@blueprint.route('/<humanReadableId>/<namespace>/<path:url>')
def zim_view(humanReadableId, namespace, url):
    zimfile = load_zim_file(humanReadableId)
    article, mimetype, ns = zimfile.get_article_by_url(namespace, url)
    if article is None:
        abort(404)
    html = mangle_article(article, mimetype, humanReadableId)
    return Response(html, mimetype=mimetype)

@blueprint.route('/iframe/<humanReadableId>')
def iframe_main_page_view(humanReadableId):
    url = url_for('zim_views.zim_main_page_view', humanReadableId=humanReadableId)
    return render_template('zim/iframe.html', main_page=True, url=url, humanReadableId=humanReadableId)

@blueprint.route('/iframe/<humanReadableId>/<namespace>/<path:url>')
def iframe_view(humanReadableId, namespace, url):
    url = url_for('zim_views.zim_view', humanReadableId=humanReadableId, namespace=namespace, url=url)
    return render_template('zim/iframe.html', main_page=False, url=url, humanReadableId=humanReadableId)

@blueprint.route('/search/<humanReadableId>')
def search(humanReadableId):
    query = request.args.get('q', '').strip()
    pagination = None
    if query:
        index_base_dir = config().get_path("ZIM", "wikipedia_index_dir")
        index_dir = os.path.join(index_base_dir, humanReadableId)
        page = int(request.args.get('page', 1))
    
        # Load index so we can query it for which fields exist
        ix = whoosh_open_dir_32_or_64(index_dir)

        # Set a higher value for the title field so it is weighted more
        weighting = scoring.BM25F(title_B=1.0)

        # Sort pages with "Image:" in their title after
        # regular articles
        def image_pages_last(searcher, docnum):
            fields = searcher.stored_fields(docnum)
            if fields['title'].find("Image:") == 0:
                return 1;
            else:
                return 0;

        # Support older whoosh indexes that do not have a reverse_links field
        if 'reverse_links' in ix.schema.names():
            sortedby = sorting.MultiFacet([ sorting.FunctionFacet(image_pages_last),
                                            sorting.ScoreFacet(),
                                            sorting.FieldFacet("reverse_links", reverse=True),
                                           ])
        else:
            sortedby = sorting.MultiFacet([ sorting.FunctionFacet(image_pages_last),
                                            sorting.ScoreFacet(),
                                           ])

        (pagination, suggestion) = paginated_search(ix, ["title", "content"], query, page, weighting=weighting, sort_column=sortedby)
    else:
        flash(_('Please input keyword(s)'), 'error')

    return render_template('zim/search.html', humanReadableId=humanReadableId, pagination=pagination, suggestion=suggestion, keywords=query, endpoint_desc=EndPointDescription('zim_views.search', {'humanReadableId':humanReadableId}))
