# -*- coding: utf-8 -*-

import re

from flask import (Blueprint, render_template, current_app, request, Response,
                   flash, url_for, redirect, session, abort, safe_join,
                   send_file, jsonify)
from flask.ext.mail import Message
from flaskext.babel import gettext as _

import whoosh
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from .whoosh_multi_field_spelling_correction import MultiFieldQueryCorrector

from .extensions import db
from gutenberg_models import (GutenbergBook, GutenbergBookFile, 
        GutenbergCreator, gutenberg_books_creator_map)

import pagination_helper
from .endpoint_description import EndPointDescription

gutenberg = Blueprint('gutenberg', __name__, url_prefix='/books')
etext_regex = re.compile(r'^etext(\d+)$')

@gutenberg.route('/')
def index():
    return render_template('gutenberg/index.html')


@gutenberg.route('/search')
def search():
    query = request.args.get('q', '').strip()
    pagination = None
    if query:
        page = int(request.args.get('page', 1))
        (pagination, suggestion) = paginated_search(query, page)
    else:
        flash(_('Please input keyword(s)'), 'error')
    print pagination.items
    return render_template('gutenberg/search.html', pagination=pagination, keywords=query, suggestion=suggestion, endpoint_desc=EndPointDescription('gutenberg.search', None))

def paginated_search(query_text, page=1, pagelen=20):
    """
    Return a tuple consisting of an object that emulates an SQLAlchemy pagination object and corrected query suggestion
    pagelen specifies number of hits per page
    page specifies page of results (first page is 1)
    """
    index_dir = current_app.config['GUTENBERG_INDEX_DIR']
    query_text = unicode(query_text)  # Must be unicode
    ix = open_dir(index_dir)
    search_column = ['title', 'creator']  # names correspond to fields in whoosh schema
    sort_column = 'creator'
    with ix.searcher() as searcher:
        query = MultifieldParser(search_column, ix.schema).parse(query_text)
        try:
            # search_page returns whoosh.searching.ResultsPage
            results = searcher.search_page(query, page, pagelen=pagelen, sortedby=sort_column)
            total = results.total
        except ValueError, e:  # Invalid page number
            results = []
            total = 0
        paginate = pagination_helper.Pagination(page, pagelen, total, [dict(r.items()) for r in results])
        corrections = deduplicate_corrections(get_query_corrections(searcher, query, query_text))  # list of Corrector objects

        #hf = whoosh.highlight.HtmlFormatter(classname="change")
        #html = corrections.format_string(hf)
        return (paginate, [c.string for c in corrections])


def deduplicate_corrections(corrections):
    """
    Return list of correction that omits entries where the query is unmodified
    :param corrections: list of Corrector objects
    :returns: list of Corrector objects
    """
    return {c.string : c for c in corrections if c.original_query != c.query}.values()

def get_query_corrections(searcher, query, qstring):
    fieldnames = [name for name, field in searcher.schema.items() if field.spelling]
    correctors = {}
    for fieldname in fieldnames:
        if fieldname not in correctors:
            correctors[fieldname] = searcher.corrector(fieldname)
    terms = []
    for token in query.all_tokens():
        if token.fieldname in correctors:
            terms.append((token.fieldname, token.text))

    return MultiFieldQueryCorrector(correctors, terms).correct_query(query, qstring)

@gutenberg.route('/by_title')
def by_title():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    pagination = GutenbergBook.query.order_by(GutenbergBook.title).paginate(page, per_page)
    return render_template('gutenberg/title-index.html', pagination=pagination, endpoint_desc=EndPointDescription('.by_title', dict(per_page=per_page)))

@gutenberg.route('/by_author')
def by_author():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    pagination = GutenbergCreator.query.order_by(GutenbergCreator.creator).paginate(page, per_page)

    return render_template('gutenberg/author-index.html', pagination=pagination, endpoint_desc=EndPointDescription('.by_author', dict(per_page=per_page)))

@gutenberg.route('/text/<textId>')
def text(textId):
    data_dir = current_app.config['GUTENBERG_ROOT_DIR']
    filename_relpath = choose_file(textId)
    fullpath = safe_join(data_dir, filename_relpath)
    return send_file(fullpath)

@gutenberg.route('/author/<authorId>')
def author(authorId):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    pagination = GutenbergBook.query.filter(gutenberg_books_creator_map.c.creator_id == authorId).filter(gutenberg_books_creator_map.c.book_id == GutenbergBook.textId).paginate(page, per_page)
    return render_template('gutenberg/title-index.html', pagination=pagination, endpoint_desc=EndPointDescription('.author', dict(authorId=authorId, per_page=per_page)))

def choose_file(textId):
    files = GutenbergBookFile.query.filter_by(textId=textId)
    #for f in files:
    #    print f
    return files[0].file

@gutenberg.route('/autocomplete')
def autocomplete():
    term = request.args.get('term', '')
    if term != '':
        response = ['abc','def']
        return jsonify(completions=response)
    else:
        # why the inefficiency? just change the referencing url
        return redirect(url_for("static", filename="gutenberg_wordlist.json"))

