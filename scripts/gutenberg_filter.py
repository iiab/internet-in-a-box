import os
import re

class GutenbergIndexFilter(object):
    # Extensions excluded from rsync of both ftp and cached/generated content
    EXCLUDED_EXT = ['.zip', '.wav', '.mp3', '.ogg', '.iso', '.ISO', '.rar', '.mpeg', '.m4b']
    # Additional extensions excluded from cached/generated files
    CACHE_EXCLUDED_EXT = ['.log', '.mobi', '.pdb', '.rdf', '.qioo.jar']

    def __init__(self):
        self.removed_texts = []
        self.notitle_count = 0

    def filter(self, record):
        """Return true if keep record, false if should discard record"""
        if self.is_description_record(record):
            has_title = 'title' in record and len(record['title']) > 0
            if not has_title:
                self.removed_texts.append(record['textId'])
                print "[omit %s notitle]" % record['textId']
                self.notitle_count += 1
            return has_title
        else:
            # NOTE: Changes to the record persist and are externally visible!
            # remove prepended '#' from text reference
            record['textId'] = record['textId'][1:]
            
            # adjust the file path (should add warning if path does not match pattern)
            FILE_PREFIX = '^http://www.gutenberg.org/dirs/'
            record['file'] = re.sub(FILE_PREFIX, 'data/gutenberg/', record['file'])
            CACHE_FILE_PREFIX = '^http://www.gutenberg.org/cache/epub/'
            record['file'] = re.sub(CACHE_FILE_PREFIX, 'data/cache/generated/', record['file'])

            # seems ugly - would multiple filters be better?  or maybe a filter stage followed by a transform stage?
            if record['file'].startswith('http'):
                print "[file prefix unexpected %s]" % record['file']

            # omit files based on three criteria:
            # (a) book description was omitted due to filter criteria above
            # (b) rsync script excluded the content (extensions and 'pgdvd')
            # (c) rsync script excluded the cached content (extensions and 'pgdvd')
            ext = self.get_extension(record['file'])
            return (record['textId'] not in self.removed_texts and 
                u'pgdvd' not in record['file'] and
                ext not in self.EXCLUDED_EXT and
                (not record['file'].startswith(u'data/cache/') or ext not in self.CACHE_EXCLUDED_EXT))
                
    def is_description_record(self, record):
        return record['record_type'] == 'DESCRIPTION'

    def get_extension(self, filename):
        name, ext = os.path.splitext(filename)
        return ext

