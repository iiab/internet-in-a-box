from flask import Blueprint, abort, send_file
import zipfile

from gutenberg_content import find_htmlz, find_epub


blueprint = Blueprint('gutenberg_content_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/htmlz/<int:pgid>/<path:path>')
def htmlz(pgid, path):
    htmlz_path = find_htmlz(pgid)
    if htmlz_path is None:
        print "HTMLZ Path not found " + str(pgid)
        abort(404)
    zf = zipfile.ZipFile(htmlz_path)
    f = zf.open(path)
    data = f.read()
    f.close()
    zf.close()
    return data


# This doesn't work because the relative paths are wrong
#@blueprint.route('/htmlz/<int:pgid>')
#def htmlz_index(pgid):
#    return htmlz(pgid, 'index.html')


@blueprint.route('/epub/<int:pgid>')
def epub(pgid):
    epub_path = find_epub(pgid)
    if epub_path is None:
        print "EPub Path not found " + str(pgid)
        abort(404)
    return send_file(epub_path, mimetype='application/epub+zip')


@blueprint.route('/epub/<int:pgid>.epub')
def epub_ext(pgid):
    return epub(pgid)
