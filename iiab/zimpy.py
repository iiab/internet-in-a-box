import struct
import string
import liblzma

HEADER_FORMAT = [
    ('I', 'magicNumber'),
    ('I', 'version'),
    ('Q', 'uuidLow'),
    ('Q', 'uuidHigh'),
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

    def unpack(self, buffer, offset=0):
        """Override this to get more complex behavior"""
        return self.unpack_format(buffer, offset)

    def unpack_from_file(self, f, seek=None):
        """Override this to get more complex behavior"""
        return self.unpack_format_from_file(f, seek)


class HeaderFormat(Format):
    def __init__(self):
        super(HeaderFormat, self).__init__(HEADER_FORMAT)


class ClusterFormat(Format):
    def __init__(self):
        super(ClusterFormat, self).__init__(CLUSTER_FORMAT)


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

    def read_directory_entry(self, offset):
        """May return either a Redirect or Article entry depending on flag"""
        self.f.seek(offset)
        buf = self.f.read(2)
        fields = struct.unpack('H', buf)
        if fields[0] == 0xffff:  # Then redirect
            return dict(self.redirectEntryFormat.unpack_from_file(self.f, offset))
        else:
            return dict(self.articleEntryFormat.unpack_from_file(self.f, offset))

    def read_url_pointer(self, index):
        self.f.seek(self.header['urlPtrPos'] + 8 * index)
        buf = self.f.read(8)
        fields = struct.unpack('Q', buf)
        return fields[0]

    def read_cluster_pointer(self, index):
        """Returns a pointer to the cluster and the cluster size"""
        self.f.seek(self.header['clusterPtrPos'] + 8 * index)
        buf = self.f.read(16)
        fields = struct.unpack('QQ', buf)
        return fields[0], fields[1] - fields[0]

    def read_directory_entry_by_index(self, index):
        ptr = self.read_url_pointer(index)
        return self.read_directory_entry(ptr)

    def unpack_blob_ptr(self, buf, index):
        ptr = struct.unpack_from('I', buf, 4 * index)[0]
        return ptr

    def read_blob(self, cluster_index, blob_index):
        ptr, size = self.read_cluster_pointer(cluster_index)
        cluster = self.clusterFormat.unpack_from_file(self.f, ptr)
        cluster = dict(cluster)
        self.f.seek(ptr + 1)
        raw = self.f.read(size - 1)
        if cluster['compressionType'] in [0, 1]:
            pass  # uncompressed
        elif cluster['compressionType'] == 4:
            raw = liblzma.decompress(raw)
        else:
            raise Exception("Unknown ZIM file compression type in cluster " + str(cluster_index) + " got type " + str(cluster['compressionType']))
        blob0 = self.unpack_blob_ptr(raw, 0)
        # Number of blobs in cluster
        nblob = blob0 / 4
        if nblob < blob_index + 1:
            raise Exception("Blob index specified beyond end of cluster.  Blob " + str(blob_index) + " requested but only " + str(nblob) + " exist")
        p = self.unpack_blob_ptr(raw, blob_index)
        n = self.unpack_blob_ptr(raw, blob_index + 1)  # Next blob
        if n > len(raw):
            raise Exception("Blob specified beyond end of cluster. " + str(p) + " to " + str(n - 1) + " in cluster of length " + str(len(raw)))
        #length = n - p
        return raw[p:n - 1]

    def get_article_by_index(self, index):
        entry = self.read_directory_entry_by_index(index)
        data = self.read_blob(entry['clusterNumber'], entry['blobNumber'])
        mime = self.mimeTypeList[entry['mimetype']]
        namespace = entry['namespace']
        return data, mime, namespace

    def get_entry_by_url(self, namespace, url):
        for i in range(self.header['articleCount']):
            entry = self.read_directory_entry_by_index(i)
            if entry['url'] == url and entry['namespace'] == namespace:
                return i
        return None

    def get_article_by_url(self, namespace, url):
        idx = self.get_entry_by_url(namespace, url)
        if idx is None:
            return None
        return self.get_article_by_index(idx)

    def get_main_page(self):
        main_index = self.header['mainPage']
        return self.get_article_by_index(main_index)
