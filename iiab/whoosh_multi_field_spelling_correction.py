# adapted from whoosh.spelling

"""This module contains helper functions for correcting typos in user queries.
"""

from whoosh import query
from whoosh.spelling import QueryCorrector, Correction


# QueryCorrector objects

class MultiFieldQueryCorrector(QueryCorrector):
    """A simple query corrector based on a mapping of field names to
    :class:`Corrector` objects, and a list of ``("fieldname", "text")`` tuples
    to correct. And terms in the query that appear in list of term tuples are
    corrected using the appropriate corrector.
    """

    def __init__(self, correctors, terms, prefix=0, maxdist=2):
        """
        :param correctors: a dictionary mapping field names to
            :class:`Corrector` objects.
        :param terms: a sequence of ``("fieldname", "text")`` tuples
            representing terms to be corrected.
        :param prefix: suggested replacement words must share this number of
            initial characters with the original word. Increasing this even to
            just ``1`` can dramatically speed up suggestions, and may be
            justifiable since spellling mistakes rarely involve the first
            letter of a word.
        :param maxdist: the maximum number of "edits" (insertions, deletions,
            subsitutions, or transpositions of letters) allowed between the
            original word and any suggestion. Values higher than ``2`` may be
            slow.
        """

        self.correctors = correctors
        self.termset = frozenset(terms)
        self.prefix = prefix
        self.maxdist = maxdist

    def correct_query(self, q, qstring):
        correctors = self.correctors
        termset = self.termset
        prefix = self.prefix
        maxdist = self.maxdist

        corrected_tokens = []
        corrected_q = q
        field_names = [ t.fieldname for t in q.all_tokens() ]
        corrections_data = {}

        #    .... maybe see if q.... can filter by field_name.  create multiple correction obj one per fieldname and return list
        for token in q.all_tokens():
            fname = token.fieldname
            if (fname, token.text) in termset:
                sugs = correctors[fname].suggest(token.text, prefix=prefix,
                                                 maxdist=maxdist)
                if sugs:
                    if fname not in corrections_data:
                        corrections_data[fname] = { "corrected_q" : q, "corrected_tokens" : [] }
                    sug = sugs[0]
                    corrections_data[fname]['corrected_q'] = corrections_data[fname]['corrected_q'].replace(token.fieldname, token.text, sug)
                    token.text = sug
                    corrections_data[fname]['corrected_tokens'].append(token)

        return [Correction(q, qstring, corrections_data[f]['corrected_q'], corrections_data[f]['corrected_tokens']) for f in corrections_data]
        #return Correction(q, qstring, corrected_q, corrected_tokens)

