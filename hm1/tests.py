import unittest
from log_analyzer_reduced import is_gzip_file, median, parse_log_record


class TestIsGzipFileFunction(unittest.TestCase):
    def test_is_gzip_file__xml(self):
        self.assertEqual(is_gzip_file("testpath/file.xml"), False)

    def test_is_gzip_file__txt(self):
        self.assertEqual(is_gzip_file("testpath/file.txt"), False)

    def test_is_gzip_file__gzip(self):
        self.assertEqual(is_gzip_file("testpath/file.gz"), True)


class TestMedianFinction(unittest.TestCase):
    def test_median__even_len(self):
        self.assertEqual(median([1, 2, 3, 4, 5]), 3)

    def test_median__odd_len(self):
        self.assertEqual(median([1, 2, 3, 4, 5, 6]), 4)


class TestParseRecord(unittest.TestCase):
    def test_parse_record(self):
        str = b'1.196.116.32 -  - [29/Jun/2017:03:51:01 +0300] "GET /api/v2/banner/1662508 HTTP/1.1" 200 948 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697460-2190034393-4708-9753194" "dc7161be3" 0.689\n'
        self.assertEqual(parse_log_record(str), ("/api/v2/banner/1662508", "0.689\n"))


if __name__ == '__main__':
    unittest.main()
