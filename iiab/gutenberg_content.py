# Utility functions for Gutenberg content
# such as htmlz and epub datasets
import os

from config import config


def hashdir(n):
    return "%02i" % (int(n) % 100)


def build_htmlz_filename(n):
    return "pg%i.htmlz" % n


def build_epub_filename(n):
    return "pg%i.epub" % n


def find_htmlz(pgid):
    """Find an htmlz file from a gutenberg book id.
    Prefers htmlz with images if available, otherwise
    falls back to non-image version.  Returns None if
    no content exists"""
    htmlz_dir = config().get_path('GUTENBERG', 'htmlz_dir')
    htmlz_images_dir = config().get_path('GUTENBERG', 'htmlz_images_dir')
    hashpath = hashdir(pgid)
    filename = build_htmlz_filename(pgid)
    hashpath = os.path.join(hashpath, filename)
    htmlz_path = os.path.join(htmlz_images_dir, hashpath)
    if not os.path.exists(htmlz_path):
        htmlz_path = os.path.join(htmlz_dir, hashpath)
    if not os.path.exists(htmlz_path):
        return None
    return htmlz_path


def find_epub(pgid):
    """Find an epub file from a gutenberg book id.
    Prefers epub with images if available, otherwise
    falls back to non-image version.  Returns None if
    no content exists"""
    epub_dir = config().get_path('GUTENBERG', 'epub_dir')
    epub_images_dir = config().get_path('GUTENBERG', 'epub_images_dir')
    hashpath = hashdir(pgid)
    filename = build_epub_filename(pgid)
    hashpath = os.path.join(hashpath, filename)
    epub_path = os.path.join(epub_images_dir, hashpath)
    if not os.path.exists(epub_path):
        epub_path = os.path.join(epub_dir, hashpath)
    if not os.path.exists(epub_path):
        return None
    return epub_path
