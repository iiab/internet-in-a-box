import unittest
import sys

sys.path.append("../scripts")
import gutenberg_filter

class TestGutenbergFilter(unittest.TestCase):
    def setUp(self):
        self.gutfil = gutenberg_filter.GutenbergIndexFilter()
    def test_descr_no_title(self):
        rec = { "record_type" : "DESCRIPTION", "textId" : "etext123" }
        self.assertEqual(self.gutfil.filter(rec), False)

    def test_descr_empty_title(self):
        rec = { "record_type" : "DESCRIPTION", "textId" : "etext123", "title": "" }
        self.assertEqual(self.gutfil.filter(rec), False)

    def test_descr_basic_title(self):
        rec = { "record_type" : "DESCRIPTION", "textId" : "etext123", "title": "test title" }
        self.assertEqual(self.gutfil.filter(rec), True)

    def test_file_basic(self):
        rec = { "record_type" : "FILE", "textId" : ":etext123", "file": "text_file.txt" }
        self.assertEqual(self.gutfil.filter(rec), True)

    def test_file_omittedext(self):
        rec = { "record_type" : "FILE", "textId" : ":etext123", "file": "text_file.zip" }
        self.assertEqual(self.gutfil.filter(rec), False)
        # not affected by basic compound extension
        rec['file'] = "text_file.big.zip"
        self.assertEqual(self.gutfil.filter(rec), False)

    def test_file_omittedtitle(self):
        rec = { "record_type" : "DESCRIPTION", "textId" : "etext123" }
        self.assertEqual(self.gutfil.filter(rec), False)
        # omitted because description had not title
        rec = { "record_type": "FILE", "textId": ":etext123", "file": "text_file.txt" }
        self.assertEqual(self.gutfil.filter(rec), False)

    def test_file_jar(self):
        rec = { "record_type" : "FILE", "textId" : ":etext123", "file": "data/cache/text_file.qioo.jar" }
        self.assertEqual(self.gutfil.filter(rec), False)

        rec = { "record_type" : "FILE", "textId" : ":etext123", "file": "data/cache/text_file.jar" }
        self.assertEqual(self.gutfil.filter(rec), True)

        rec = { "record_type" : "FILE", "textId" : ":etext123", "file": "text_file.qioo.jar" }
        self.assertEqual(self.gutfil.filter(rec), True)


if __name__ == '__main__':
    unittest.main()
