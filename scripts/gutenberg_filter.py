import os
import re

# Support library for processing Gutenberg records. Modify filepaths and remove unsupported file 
# types that occur in the gutenberg.org RDF records for use in the IIAB project.
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
            record['file'] = re.sub(FILE_PREFIX, 'data/', record['file'])
            CACHE_FILE_PREFIX = '^http://www.gutenberg.org/cache/epub/'
            record['file'] = re.sub(CACHE_FILE_PREFIX, 'data/cache/generated/', record['file'])

            # seems ugly - would multiple filters be better?  or maybe a filter stage followed by a transform stage?
            if record['file'].startswith('http'):
                print "[file prefix unexpected %s]" % record['file']

            # omit files based on three criteria:
            # (a) book description was omitted due to filter criteria above
            # (b) rsync script excluded the content (extensions and 'pgdvd')
            # (c) rsync script excluded the cached content (extensions and 'pgdvd')
            return (record['textId'] not in self.removed_texts and 
                u'pgdvd' not in record['file'] and
                not self.extension_match(record['file'], self.EXCLUDED_EXT) and
                (not record['file'].startswith(u'data/cache/') or not self.extension_match(record['file'], self.CACHE_EXCLUDED_EXT)))
                
    def is_description_record(self, record):
        return record['record_type'] == 'DESCRIPTION'

    def extension_match(self, filename, extension_list):
        for ext in extension_list:
            if filename.endswith(ext):
                return True
        return False

