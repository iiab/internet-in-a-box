import os
from glob import glob
import logging

from flask import Blueprint, render_template

from config import config
from zimpy import ZimFile
from iso639 import iso6392
from kiwix import Library

blueprint = Blueprint('wikipedia_views', __name__,
                      template_folder='templates')

logger = logging.getLogger()

def organize_books_by_language(filenames, library_file):
    kiwix_lib = Library(library_file)

    languages = {} 
    print "Entering"
    for zim_fn in filenames:
        zim_obj = ZimFile(zim_fn)
        book_data = zim_obj.metadata()

        # Make sure book has metadata, if not look up in kiwix library
        # This solution allows us to add zim files not in the kiwix library
        # while still having a backup for files that do not have metadata
        if not book_data.has_key('language'):
            logger.info("No metadata, looking for book in kiwix library: %s" % zim_fn)
            book_data = kiwix_lib.find_by_uuid(zim_obj.get_kiwix_uuid())
            if book_data == None:
                logger.info("Book missing in kiwix library as well, skipping: %s" % zim_fn)
                continue

        # Decode strings from UTF-8 into unicode objects
        for k,v in book_data.items():
            if type(v) is str:
                book_data[k] = v.decode('utf-8')

        # Format article count as string with commas
        book_data['articleCount'] = "{:,d}".format(zim_obj.header['articleCount'])
        book_data['humanReadableId'] = os.path.splitext(os.path.basename(zim_fn))[0]
        
        if not languages.has_key(book_data['language']):
            lang_data = {}
            if iso6392.has_key(book_data['language']):
                lang_data['languageEnglish'] = iso6392[book_data['language']]['english']
            else:
                lang_data['languageEnglish'] = "Unknown: " + book_data['language']
            lang_data['languageCode'] = book_data['language']
            lang_data['books'] = []
            languages[book_data['language']] = lang_data 
        else:
            lang_data = languages[book_data['language']]

        lang_data['books'].append(book_data)

    return languages.values()

@blueprint.route('/')
def wikipedia_view():
    wikipedia_zim_dir = config().get('ZIM', 'wikipedia_zim_dir')
    library_file = config().get('ZIM', 'kiwix_library_file')
    langs = organize_books_by_language(glob(os.path.join(wikipedia_zim_dir, "*.zim")), library_file)
    return render_template('wikipedia_index.html', languages=langs)
