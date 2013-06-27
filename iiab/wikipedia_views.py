import os
from glob import glob
import logging

from flask import Blueprint, render_template

from config import config
from zimpy import ZimFile
from iso639 import iso6392

blueprint = Blueprint('wikipedia_views', __name__,
                      template_folder='templates')

logger = logging.getLogger()

def organize_books_by_language(filenames):
    languages = {} 
    print "Entering"
    for zim_fn in filenames:
        zim_obj = ZimFile(zim_fn)
        book_data = zim_obj.metadata()

        # Encode unicode into UTF-8
        for k,v in book_data.items():
            book_data[k] = v.decode('utf-8')

        # Format article count as string with commas
        book_data['articleCount'] = "{:,d}".format(zim_obj.header['articleCount'])
        book_data['humanReadableId'] = os.path.splitext(os.path.basename(zim_fn))[0]

        if not book_data.has_key('Language'):
            logger.info("Skipping book without metadata: %s" % zim_fn)
            continue

        if not languages.has_key(book_data['Language']):
            lang_data = {}
            if iso6392.has_key(book_data['Language']):
                lang_data['languageEnglish'] = iso6392[book_data['Language']]['english']
            else:
                lang_data['languageEnglish'] = "Unknown: " + book_data['Language']
            lang_data['languageCode'] = book_data['Language']
            lang_data['books'] = []
            languages[book_data['Language']] = lang_data 
        else:
            lang_data = languages[book_data['Language']]

        lang_data['books'].append(book_data)

    return languages.values()

@blueprint.route('/')
def wikipedia_view():
    zim_url = config().get('ZIM', 'url')
    wikipedia_zim_dir = config().get('ZIM', 'wikipedia_dir')
    langs = organize_books_by_language(glob(os.path.join(wikipedia_zim_dir, "*.zim")))
    ajax = False
    if zim_url == "/iiab/zim":
        zim_url = "/iiab/zim/iframe"
        ajax = True
    return render_template('wikipedia_index.html', languages=langs, zim_url=zim_url, ajax=ajax)
