import os
import re

class GutenbergIndexFilter(object):
    EXCLUDED_EXT = ['.zip', '.wav', '.mp3', '.ogg', '.iso', '.ISO', '.rar', '.mpeg', '.m4b']
    def __init__(self):
        self.removed_texts = []

    def filter(self, record):
        """Return true if keep record, false if should discard record"""
        if self.is_description_record(record):
            has_title = 'title' in record and len(record['title']) > 0
            if not has_title:
                self.removed_texts.append(record['textId'])
                print "[omit %s notitle]" % record['textId']
            return has_title
        else:
            # NOTE: Changes to the record persist and are externally visible!
            # remove prepended '#' from text reference
            record['textId'] = record['textId'][1:]
            
            # adjust the file path (should add warning if path does not match pattern)
            FILE_PREFIX = '^http://www.gutenberg.org/dirs/'
            record['file'] = re.sub(FILE_PREFIX, 'gutenberg/', record['file'])
            CACHE_FILE_PREFIX = '^http://www.gutenberg.org/cache/'
            record['file'] = re.sub(CACHE_FILE_PREFIX, 'cache/', record['file'])

            # seems ugly - would multiple filters be better?  or maybe a filter stage followed by a transform stage?
            if record['file'].startswith('http'):
                print "[file prefix unexpected %s]" % record['file']

            # omit files based on two criteria:
            # (a) book description was omitted due to filter criteria above
            # (b) rsync script excluded the content (extensions and 'pgdvd')
            return (record['textId'] not in self.removed_texts and 
                u'pgdvd' not in record['file'] and
                self.get_extension(record['file']) not in self.EXCLUDED_EXT)
                
    def is_description_record(self, record):
        return record['record_type'] == 'DESCRIPTION'

    def get_extension(self, filename):
        name, ext = os.path.splitext(filename)
        return ext

