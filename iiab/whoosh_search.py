import os

from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser

from .whoosh_multi_field_spelling_correction import MultiFieldQueryCorrector
import pagination_helper

def index_directory_path(base_path, zim_name):
    """Returns the directory where a ZIM file's index should be located, given
    a base path where all the index files are located as well as a filename
    or partial filename of the zim file.
    """

    index_dir = os.path.join(base_path, os.path.splitext(os.path.basename(zim_name))[0])
    return index_dir


def get_query_corrections(searcher, query, qstring):
    """
    Suggest alternate spelling for search terms by searching each column with
    spelling correction support in turn.

    :param searcher: whoosh searcher object
    :param query: whoosh query object
    :param qstring: search string that was passed to the query object
    :returns: MultiFieldQueryCorrector with one corrector for each corrected column
    """
    fieldnames = [name for name, field in searcher.schema.items() if field.spelling]
    correctors = {}
    for fieldname in fieldnames:
        if fieldname not in correctors:
            correctors[fieldname] = searcher.corrector(fieldname)
    terms = []
    for token in query.all_tokens():
        if token.fieldname in correctors:
            terms.append((token.fieldname, token.text))

    return MultiFieldQueryCorrector(correctors, terms, prefix=2, maxdist=1).correct_query(query, qstring)

def deduplicate_corrections(corrections):
    """
    Return list of correction that omits entries where the query is unmodified
    :param corrections: list of Corrector objects
    :returns: list of Corrector objects
    """
    # Using values from a dictionary comprehension rather than a list comprehension in order to deduplicate
    #return {c.string : c for c in corrections if c.original_query != c.query}.values()
    # We can't use dictionary comprehension because we are stuck on python 2.6 for Debian stable
    return dict((c.string, c) for c in corrections if c.original_query != c.query).values()


def paginated_search(index_dir, search_columns, query_text, page=1, pagelen=20, sort_column=None):
    """
    Return a tuple consisting of an object that emulates an SQLAlchemy pagination object and corrected query suggestion
    pagelen specifies number of hits per page
    page specifies page of results (first page is 1)
    """
    query_text = unicode(query_text)  # Must be unicode
    ix = open_dir(index_dir)
    with ix.searcher() as searcher:
        query = MultifieldParser(search_columns, ix.schema).parse(query_text)
        try:
            # search_page returns whoosh.searching.ResultsPage
            results = searcher.search_page(query, page, pagelen=pagelen, sortedby=sort_column)
            total = results.total
        except ValueError:  # Invalid page number
            results = []
            total = 0
        paginate = pagination_helper.Pagination(page, pagelen, total, [dict(r.items()) for r in results])
        corrections = deduplicate_corrections(get_query_corrections(searcher, query, query_text))  # list of Corrector objects

        #hf = whoosh.highlight.HtmlFormatter(classname="change")
        #html = corrections.format_string(hf)
        return (paginate, [c.string for c in corrections])
