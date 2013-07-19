import re
import struct
import string
import timepro
import logging
import uuid

import sys
# Import lzma this way so we get the built in version for
# Python 3.3 or the backported one otherwize. Don't just
# do a try/catch for import lzma because the older
# pyliblzma uses that package name, and we do not want
# to use it.
if sys.version_info[0:3] >= (3,3,0):
    import lzma
else:
    try:
        from backports import lzma
    except ImportError as e:
        # On Fedora/OLPC we have a namespace conflict
        # with another package, so we had to rename the
        # namespace until we get it resolved upstream
        from backportslzma import lzma

from StringIO import StringIO

logger = logging.getLogger(__name__)

HEADER_FORMAT = [
    ('I', 'magicNumber'),
    ('I', 'version'),
    #('Q', 'uuidLow'),
    #('Q', 'uuidHigh'),
    ('B', 'uuid0'),
    ('B', 'uuid1'),
    ('B', 'uuid2'),
    ('B', 'uuid3'),
    ('B', 'uuid4'),
    ('B', 'uuid5'),
    ('B', 'uuid6'),
    ('B', 'uuid7'),
    ('B', 'uuid8'),
    ('B', 'uuid9'),
    ('B', 'uuid10'),
    ('B', 'uuid11'),
    ('B', 'uuid12'),
    ('B', 'uuid13'),
    ('B', 'uuid14'),
    ('B', 'uuid15'),
    ('I', 'articleCount'),
    ('I', 'clusterCount'),
    ('Q', 'urlPtrPos'),
    ('Q', 'titlePtrPos'),
    ('Q', 'clusterPtrPos'),
    ('Q', 'mimeListPos'),
    ('I', 'mainPage'),
    ('I', 'layoutPage'),
    ('Q', 'checksumPos')
]


ARTICLE_ENTRY_FORMAT = [
    ('H', 'mimetype'),
    ('B', 'parameterLen'),
    ('c', 'namespace'),
    ('I', 'revision'),
    ('I', 'clusterNumber'),
    ('I', 'blobNumber')
    # Null terminated url
    # Null terminated title
    # variable length parameter data
]


REDIRECT_ENTRY_FORMAT = [
    ('H', 'mimetype'),
    ('B', 'parameterLen'),
    ('c', 'namespace'),
    ('I', 'revision'),
    ('I', 'redirectIndex')
    # Null terminated url
    # Null terminated title
    # variable length parameter data
]


CLUSTER_FORMAT = [
    ('B', 'compressionType')
]


# A null byte
NULL = struct.pack('B', 0)


def format_from_rich(rich_format):
    return "<" + string.join([x[0] for x in rich_format], "")


def read_null_terminated(f, encoding='utf-8'):
    s = ""
    while True:
        b = f.read(1)
        if b == NULL:
            return s.decode(encoding)
        s = s + b


def binary_search(f, t, min, max):
    while 1:
        if max < min:
            return None
        m = (min + max) / 2
        v = f(m)
        if v < t:
            min = m + 1
        elif v > t:
            max = m - 1
        else:
            return m


def full_url(namespace, url):
    return namespace + '/' + url


class Format(object):
    def __init__(self, rich_format):
        self.rich_fmt = rich_format
        self.fmt = format_from_rich(rich_format)
        self.compiled = struct.Struct(self.fmt)
        self.size = self.compiled.size

    def unpack_format(self, buffer, offset=0):
        fields = self.compiled.unpack_from(buffer, offset)
        d = []
        for field, entry in zip(fields, self.rich_fmt):
            d.append((entry[1], field))
        return d

    def unpack_format_from_file(self, f, seek=None):
        if seek is not None:
            f.seek(seek)
        buf = f.read(self.size)
        d = self.unpack_format(buf)
        return d

    @timepro.profile()
    def unpack(self, buffer, offset=0):
        """Override this to get more complex behavior"""
        return self.unpack_format(buffer, offset)

    @timepro.profile()
    def unpack_from_file(self, f, seek=None):
        """Override this to get more complex behavior"""
        return self.unpack_format_from_file(f, seek)


class HeaderFormat(Format):
    def __init__(self):
        super(HeaderFormat, self).__init__(HEADER_FORMAT)


class ClusterFormat(Format):
    def __init__(self):
        super(ClusterFormat, self).__init__(CLUSTER_FORMAT)

class ClusterData(object):
    def __init__(self, file_buffer, ptr):
        cluster_info = dict(ClusterFormat().unpack_from_file(file_buffer, ptr))
        self.compressed = cluster_info['compressionType'] == 4

        self.file_buf = file_buffer
        self.uncomp_buf = None
        self.ptr = ptr

        self.offsets = []

        if self.compressed:
            self._decompress()

        self.read_offsets()

    def _decompress(self, chunk_size=32):
        """Decompresses the cluster if compression flag was found. Stores
        uncompressed results internally."""

        if not self.compressed:
            return

        self.file_buf.seek(self.ptr + 1)

        # Store uncompressed cluster data for use as uncompressed data
        self.uncomp_buf = StringIO()

        decomp = lzma.LZMADecompressor()
        while not decomp.eof:
            comp_data = self.file_buf.read(chunk_size)

            uncomp_data = decomp.decompress(comp_data)
            self.uncomp_buf.write(uncomp_data)

        return self.uncomp_buf

    def source_buffer(self):
        """Returns the buffer to read from, either the file buffer
        passed or the uncompressed lzma data. Will seek to the
        beginning of the cluster after the 1 byte compression flag"""

        if self.compressed:
            self.uncomp_buf.seek(0)
            return self.uncomp_buf
        else:
            self.file_buf.seek(self.ptr + 1)
            return self.file_buf

    def unpack_blob_index(self, buf):
        ptr = struct.unpack('I', buf)[0]
        return ptr

    def read_offsets(self):
        """Reads the cluster header with the offsets of the blobs"""

        src_buf = self.source_buffer()

        raw = src_buf.read(4)
        offset0 = self.unpack_blob_index(raw)
        self.offsets.append(offset0)
        nblob = offset0 / 4

        for idx in range(nblob-1):
            raw = src_buf.read(4)
            offset = self.unpack_blob_index(raw)
            self.offsets.append(offset)

        return self.offsets

    def read_blob(self, blob_index):
        """Reads a blob from the cluster"""

        if blob_index >= len(self.offsets) - 1:
            raise IOError("Blob index exceeds number of blobs available: %s" % blob_index)

        src_buf = self.source_buffer()

        blob_size = self.offsets[blob_index+1] - self.offsets[blob_index]

        # For uncompressed data, seek from beginning of file
        # Otherwise seek the compressed data with just and offset
        if not self.compressed:
            seek_beg = self.ptr + 1
        else:
            seek_beg = 0
        src_buf.seek(seek_beg + self.offsets[blob_index])

        blob_data = src_buf.read(blob_size)

        return blob_data

class ArticleEntryFormat(Format):
    def __init__(self):
        super(ArticleEntryFormat, self).__init__(ARTICLE_ENTRY_FORMAT)

    def unpack(self, buffer, offset=0):
        raise Exception("Unimplemented")

    def unpack_from_file(self, f, seek=None):
        d = super(ArticleEntryFormat, self).unpack_from_file(f, seek)
        url = read_null_terminated(f)
        title = read_null_terminated(f)
        parameter = f.read(dict(d)['parameterLen'])
        d.extend([('url', url),
                  ('title', title),
                  ('parameter', parameter)]
                 )
        return d


class RedirectEntryFormat(Format):
    def __init__(self):
        super(RedirectEntryFormat, self).__init__(REDIRECT_ENTRY_FORMAT)

    def unpack(self, buffer, offset=0):
        raise Exception("Unimplemented")

    def unpack_from_file(self, f, seek=None):
        d = super(RedirectEntryFormat, self).unpack_from_file(f, seek)
        url = read_null_terminated(f)
        title = read_null_terminated(f)
        parameter = f.read(dict(d)['parameterLen'])
        d.extend([('url', url),
                  ('title', title),
                  ('parameter', parameter)]
                 )
        return d


class MimeTypeListFormat(Format):
    def __init__(self):
        super(MimeTypeListFormat, self).__init__("")

    def unpack(self, buffer, offset=0):
        raise Exception("Unimplemented")

    def unpack_from_file(self, f, seek=None):
        if seek is not None:
            f.seek(seek)
        mimetypes = []
        while True:
            s = read_null_terminated(f)
            if s == "":
                return mimetypes
            mimetypes.append(s)


class ZimFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.redirectEntryFormat = RedirectEntryFormat()
        self.articleEntryFormat = ArticleEntryFormat()
        self.clusterFormat = ClusterFormat()
        self.f = open(filename, "r")
        self.header = dict(HeaderFormat().unpack_from_file(self.f))
        self.mimeTypeList = MimeTypeListFormat().unpack_from_file(self.f, self.header['mimeListPos'])

    def close(self):
        self.f.close()

    def get_uuid(self):
        """Returns the UUID for this ZIM file"""
        h = self.header
        uuid_bytes = [h['uuid0'], h['uuid1'], h['uuid2'], h['uuid3'], h['uuid4'],
                      h['uuid5'], h['uuid6'], h['uuid7'], h['uuid8'], h['uuid9'],
                      h['uuid10'], h['uuid11'], h['uuid12'], h['uuid13'], h['uuid14'],
                      h['uuid15']]
        s = string.join([chr(x) for x in uuid_bytes], "")
        return uuid.UUID(bytes=s)

    def get_kiwix_uuid(self):
        """Kiwix seems to have a bug in their library.xml which causes the
        third UUID group to be repeated."""
        u = self.get_uuid()
        s = str(u).split("-")
        return s[0] + "-" + s[1] + "-" + s[2] + "-" + s[2] + "-" + s[3] + s[4]

    @timepro.profile()
    def read_directory_entry(self, offset):
        """May return either a Redirect or Article entry depending on flag"""
        self.f.seek(offset)
        buf = self.f.read(2)
        fields = struct.unpack('H', buf)
        if fields[0] == 0xffff:  # Then redirect
            return dict(self.redirectEntryFormat.unpack_from_file(self.f, offset))
        else:
            return dict(self.articleEntryFormat.unpack_from_file(self.f, offset))

    @timepro.profile()
    def read_url_pointer(self, index):
        self.f.seek(self.header['urlPtrPos'] + 8 * index)
        buf = self.f.read(8)
        fields = struct.unpack('Q', buf)
        return fields[0]

    def read_title_pointer(self, index):
        self.f.seek(self.header['titlePtrPos'] + 4 * index)
        buf = self.f.read(4)
        fields = struct.unpack('L', buf)
        return fields[0]

    @timepro.profile()
    def read_cluster_pointer(self, index):
        """Returns a pointer to the cluster"""

        self.f.seek(self.header['clusterPtrPos'] + 8 * index)
        buf = self.f.read(8)
        fields = struct.unpack('Q', buf)
        return fields[0]

    @timepro.profile()
    def read_directory_entry_by_index(self, index):
        ptr = self.read_url_pointer(index)
        return self.read_directory_entry(ptr)

    @timepro.profile()
    def read_blob(self, cluster_index, blob_index):
        ptr = self.read_cluster_pointer(cluster_index)
        cluster_data = ClusterData(self.f, ptr)
        return cluster_data.read_blob(blob_index)

    @timepro.profile()
    def get_article_by_index(self, index, follow_redirect=True):
        entry = self.read_directory_entry_by_index(index)
        if 'redirectIndex' in entry.keys():
            if follow_redirect:
                logger.debug("REDIRECT TO " + str(entry['redirectIndex']))
                return self.get_article_by_index(entry['redirectIndex'], follow_redirect)
            else:
                return None, entry['redirectIndex'], entry['namespace']
        data = self.read_blob(entry['clusterNumber'], entry['blobNumber'])
        mime = self.mimeTypeList[entry['mimetype']]
        namespace = entry['namespace']
        return data, mime, namespace

    @timepro.profile()
    def get_entry_by_url_linear(self, namespace, url):
        for i in range(self.header['articleCount']):
            entry = self.read_directory_entry_by_index(i)
            if entry['url'] == url and entry['namespace'] == namespace:
                return i
        return None

    @timepro.profile()
    def get_entry_by_url(self, namespace, url):
        nsurl = full_url(namespace, url)

        def check(idx):
            entry = self.read_directory_entry_by_index(idx)
            return full_url(entry['namespace'], entry['url'])

        m = binary_search(check, nsurl, 0, self.header['articleCount'])
        if m is None:
            return None
        entry = self.read_directory_entry_by_index(m)
        return entry, m

    def get_article_by_url(self, namespace, url, follow_redirect=True):
        entry, idx = self.get_entry_by_url(namespace, url)
        if idx is None:
            return None
        return self.get_article_by_index(idx, follow_redirect=follow_redirect)

    def get_main_page(self):
        main_index = self.header['mainPage']
        return self.get_article_by_index(main_index)

    @timepro.profile()
    def metadata(self):
        metadata = {}
        for i in xrange(self.header['articleCount'] - 1, -1, -1):
            entry = self.read_directory_entry_by_index(i)
            if entry['namespace'] == 'M':
                m_name = entry['url']
                # Lower case first letter to match kiwix-library names convention
                m_name = re.sub(r'^([A-Z])', lambda pat: pat.group(1).lower(), m_name)
                metadata[m_name] = self.get_article_by_index(i)[0]
            else:
                break

        return metadata

    def articles(self):
        """Generator which iterates through all articles"""
        for i in range(self.header['articleCount']):
            entry = self.read_directory_entry_by_index(i)
            entry['fullUrl'] = full_url(entry['namespace'], entry['url']) + "\n"
            yield entry

    def validate(self):
        """This is a mostly a self-test, but will validate various assumptions"""
        # Test that URLs are properly ordered
        last = None
        for i in range(self.header['articleCount']):
            entry = self.read_directory_entry_by_index(i)
            assert entry is not None
            nsurl = full_url(entry['namespace'], entry['url'])
            if last is not None:
                assert nsurl > last
            last = nsurl
        timepro.log_all()
        timepro.reset()

        # Test load by url performance
        for i in range(0, self.header['articleCount'], 100):
            entry = self.read_directory_entry_by_index(i)
            entry2, idx = self.get_entry_by_url(entry['namespace'], entry['url'])
            assert entry2 is not None
        timepro.log_all()
        timepro.reset()

        # Test load of the last article
        article, mime, ns = self.get_article_by_index(self.header['articleCount'] - 1)
        entry = self.read_directory_entry_by_index(self.header['articleCount'] - 1)
        entry2, idx = self.get_entry_by_url(entry['namespace'], entry['url'])
        assert entry2 is not None

        # Test load subset of all articles
        for i in range(0, self.header['articleCount'], 100):
            if i % 1000 == 0:
                print i
            article, mime, ns = self.get_article_by_index(i)
            if article is None:  # Redirect
                assert mime is not None
        timepro.log_all()
        timepro.reset()

    def list_articles_by_url(self):
        """Mostly for testing"""
        s = ""
        for i in range(self.header['articleCount']):
            entry = self.read_directory_entry_by_index(i)
            s += full_url(entry['namespace'], entry['url']) + "\n"
        return s
