import unittest
from log_analyzer_reduced import is_gzip_file

class TestIsGzipFileFunction(unittest.TestCase):
    def test_is_gzip_file__xml(self):
         self.assertEqual(is_gzip_file("testpath/file.xml"), False)

    def test_is_gzip_file__txt(self):
         self.assertEqual(is_gzip_file("testpath/file.txt"), False)

    def test_is_gzip_file__gzip(self):
         self.assertEqual(is_gzip_file("testpath/file.gz"), True)

if __name__ == '__main__':
    unittest.main()