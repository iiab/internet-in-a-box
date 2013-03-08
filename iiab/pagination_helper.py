from math import ceil

"""
Emulate flask.ext.SQLAlchemy.Pagination
Adapted from http://flask.pocoo.org/snippets/44/
"""
class Pagination(object):

    def __init__(self, page, per_page, total_count, items):
        """
        :param page: integer current page number counting from 1
        :param per_page: integer number of results per page
        :param total_count: integer number of items all together
        :param items: list of objects associated with current page of results
        """
        self.page = page
        self.per_page = per_page
        self.total_count = total_count
        self.items = items

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


