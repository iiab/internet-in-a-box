import struct
import string

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
        self.f = open(filename, "r")
        self.header = dict(HeaderFormat().unpack_from_file(self.f))
        self.mimeTypeList = MimeTypeListFormat().unpack_from_file(self.f, self.header['mimeListPos'])

    def read_directory_entry(self, offset):
        """May return either a Redirect or Article entry depending on flag"""
        self.f.seek(offset)
        buf = self.f.read(2)
        fields = struct.unpack('H', buf)
        if fields[0] == 0xffff:  # Then redirect
            return self.redirectEntryFormat.unpack_from_file(self.f, offset)
        else:
            return self.articleEntryFormat.unpack_from_file(self.f, offset)

    def read_url_pointer(self, index):
        self.f.seek(self.header['urlPtrPos'] + 8 * index)
        buf = self.f.read(8)
        fields = struct.unpack('Q', buf)
        return fields[0]

    def read_directory_entry_by_index(self, index):
        ptr = self.read_url_pointer(index)
        return self.read_directory_entry(ptr)

    def print_directory(self):
        pass
