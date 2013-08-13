# -*- coding: utf-8 -*-

import os
import re

from flask import (Blueprint, render_template, request, Response,
                   flash, url_for, redirect, safe_join, make_response,
                   send_file, send_from_directory)
from flask.ext.babel import gettext as _
import json

from contextlib import closing

from .extensions import db
from gutenberg_models import (GutenbergBook, GutenbergFile,
                              GutenbergCreator, gutenberg_books_creator_map)
from gutenberg_content import find_htmlz, find_epub
from config import config

from whoosh_search import paginated_search
from whoosh.index import open_dir
from .endpoint_description import EndPointDescription

DEFAULT_RESULTS_PER_PAGE = 20
DEFAULT_SEARCH_COLUMNS = ['title', 'creator', 'contributor']  # names correspond to fields in whoosh schema

gutenberg = Blueprint('gutenberg', __name__, url_prefix='/books')
etext_regex = re.compile(r'^etext(\d+)$')


flask_app = None
is_init = False


def set_flask_app(app):
    global flask_app
    flask_app = app


def init_db():
    global is_init
    global flask_app
    if not is_init:
        if flask_app is None:
            raise Exception("init_db called when flask app not set")
        # set global config variables referenced by SQLAlchemy
        flask_app.config['SQLALCHEMY_ECHO'] = config().getboolean('GUTENBERG', 'sqlalchemy_echo')
        database_path = config().get_path('GUTENBERG', 'sqlalchemy_database_uri')
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath(database_path)
        db.init_app(flask_app)
        is_init = True


@gutenberg.route('/')
def index():
    return render_template('gutenberg/index.html')


@gutenberg.route('/search')
def search():
    query = request.args.get('q', '').strip()
    pagination = None
    if query:
        index_dir = config().get_path('GUTENBERG', 'index_dir')
        page = int(request.args.get('page', 1))
        (pagination, suggestion) = paginated_search(index_dir, DEFAULT_SEARCH_COLUMNS, query, page, sort_column='creator')
    else:
        flash(_('Please input keyword(s)'), 'error')
    #print pagination.items
    return render_template('gutenberg/search.html', pagination=pagination,
                           keywords=query, suggestion=suggestion, fn_author_to_query=author_to_query,
                           endpoint_desc=EndPointDescription('gutenberg.search', None),
                           files_exist=files_exist)


@gutenberg.route('/mirror/<path:filename>')
def gutenberg_mirror(filename):
    mirror_dir = config().get_path('GUTENBERG', 'gutenberg_mirror')
    print "mirror", mirror_dir, filename
    r = send_from_directory(mirror_dir, filename)
    return make_response(r, 200, {'Accept-Ranges': 'bytes'})


def author_to_query(author):
    """Helper function for template macro to convert an author string into a
    search query.

    :param author: unicode string from creator or contributor field of gutenberg index
    :returns: whoosh query string to search creator/contributor fields for given author.
    """
    # contributor field provides extra details about contirbutor's role in brackets -- strip that off so we can search for author in any role.
    author = re.sub(r'\[[^\]]+\]', '', author).strip()
    return u'creator:"{0}" OR contributor:"{0}"'.format(author)


@gutenberg.route('/titles')
def by_title():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE))
    pagination = GutenbergBook.query.order_by(GutenbergBook.title_order).paginate(page, per_page)
    return render_template('gutenberg/title-index.html', pagination=pagination, fn_author_to_query=author_to_query, endpoint_desc=EndPointDescription('.by_title', dict(per_page=per_page)))


@gutenberg.route('/authors')
def by_author():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE))
    pagination = GutenbergCreator.query.order_by(GutenbergCreator.creator).paginate(page, per_page)

    return render_template('gutenberg/author-index.html', pagination=pagination, endpoint_desc=EndPointDescription('.by_author', dict(per_page=per_page)))


@gutenberg.route('/author/<authorId>')
def author(authorId):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE))
    pagination = GutenbergBook.query.filter(gutenberg_books_creator_map.c.creator_id == authorId).filter(gutenberg_books_creator_map.c.book_id == GutenbergBook.textId).paginate(page, per_page)
    return render_template('gutenberg/title-index.html', pagination=pagination, fn_author_to_query=author_to_query, endpoint_desc=EndPointDescription('.author', dict(authorId=authorId, per_page=per_page)))


def mirror_path(filename):
    """Determines the full path to a gutenberg text in the mirror"""
    mirror_dir = config().get_path('GUTENBERG', 'gutenberg_mirror')
    path = os.path.join(mirror_dir, filename)
    return path


def mirror_exists(file_rec):
    path = mirror_path(file_rec.file)
    return os.path.exists(path)


def textId2number(textId):
    return int(textId[5:])


def files_exist(textId, record=None):
    """Returns true if any files exist for this e-text
    in the local dataset"""
    if record is None:
        record = GutenbergBook.query.filter_by(textId=textId).first()
    if record is None:
        return False
    for x in record.gutenberg_files:
        if mirror_exists(x):
            return True
    pgid = textId2number(textId)
    if find_htmlz(pgid) is not None:
        return True
    if find_epub(pgid) is not None:
        return True
    return False


@gutenberg.route('/text/<textId>/details')
def text(textId):
    # Profiling results showing occasional lags.
    # Lags can be minimized by disabling SQLALCHEMY_ECHO and
    # and debug mode.
    # Tested no options, joinedload and subqueryload with no consistent winner.
    record = GutenbergBook.query.filter_by(textId=textId).first()
    # if blueprint has a different static_folder specified we might need to use blueprint.static_folder but currently None
    for x in record.gutenberg_files:
        if not mirror_exists(x):
            print "WARNING: Gutenberg file " + mirror_path(x.file) + " not found"
    record.gutenberg_files = filter(mirror_exists, record.gutenberg_files)

    pgid = textId2number(textId)
    if find_htmlz(pgid) is not None:
        htmlz_url = url_for('gutenberg_content_views.htmlz', pgid=pgid, path='index.html')
    else:
        htmlz_url = None
    if find_epub(pgid) is not None:
        epub_url = url_for('gutenberg_content_views.epub_ext', pgid=pgid)
    else:
        epub_url = None

    # fields format is list of tuples:
    # (Table row heading for display, gutenberg_books col name,
    #  sub-table col name if applicable)
    fields = [
        (_('Title'), 'title', ''),
        (_('Author'), 'gutenberg_creators', 'creator'),
        (_('Contributor'), 'gutenberg_contributors', 'contributor'),
        (_('Subject'), 'gutenberg_subjects', 'subject'),
        (_('Category'), 'gutenberg_categories', 'category'),
        (_('Language'), 'gutenberg_languages', 'language')
    ]
    return render_template('gutenberg/book_details.html', record=record,
                           fields=fields, epub_url=epub_url, htmlz_url=htmlz_url)


@gutenberg.route('/text/<textId>/<int:textIndex>')
def read(textId, textIndex):
    data_dir = config().get_path('GUTENBERG', 'root_dir')
    files = GutenbergFile.query.filter_by(textId=textId).all()
    assert textIndex >= 0 and textIndex < len(files)
    fullpath = safe_join(os.path.abspath(data_dir), files[textIndex].file)
    return send_file(fullpath)


def choose_file(textId):
    files = GutenbergFile.query.filter_by(textId=textId)
    #for f in files:
    #    print f
    return files[0].file


@gutenberg.route('/autocomplete')
def autocomplete():
    term = request.args.get('term', '')
    if term != '':
        index_dir = config().get_path('GUTENBERG', 'index_dir')
        ix = open_dir(index_dir)
        with ix.searcher() as searcher:
            # might use whoosh.analysis.*Analyzer to break query up
            # for matching. However it isn't clear how to combine completion
            # of partial matches across several different columns without
            # lots of effort

            # Be aware that returning a json top-level array leaves us vulnerable to CSRF.
            # http://flask.pocoo.org/docs/security/ In this case this is not of significant
            # concern because the information is not sensitive.  We use a top-level array
            # because this is what jquery autocomplete demands for use without modification.
            suggestions = get_autocomplete_matches(term)
            return Response(response=json.dumps(suggestions), mimetype="application/json")
    else:
        # Choosing an inefficient redirect because still testing different
        # approaches and its easier to centralize the handling.  If we keep
        # this approach we can just change the referencing url
        return redirect(url_for("static", filename="gutenberg_wordlist.json"))


def get_autocomplete_matches(prefix, limit=10):
    def get_prefix_like(prefix):
        (result, _) = re.subn(r'\\', u'\\\\', prefix)
        (result, _) = re.subn(r'_', u'\_', result)
        (result, _) = re.subn(r'%', u'\%', result)
        (result, _) = re.subn(r'\s+', u'%', result)
        return '%' + result + '%'

    def make_sql(colname, tablename, limit):
        sql = "SELECT {0}, downloads FROM {1} WHERE {0} LIKE :like_clause ESCAPE '\\' ORDER BY downloads LIMIT {2};".format(colname, tablename, limit)
        return sql

    like_clause = get_prefix_like(prefix)
    search_fields = [('title', 'gutenberg_books'),
                     ('creator', 'gutenberg_creators'),
                     ('contributor', 'gutenberg_contributors')]
    results = []
    with closing(db.engine.connect()) as conn:
        for colname, tablename in search_fields:
            results.extend(conn.execute(make_sql(colname, tablename, limit), like_clause=like_clause).fetchall())
    return [row[0] for row in sorted(results, key=lambda r: r[1], reverse=True)]
