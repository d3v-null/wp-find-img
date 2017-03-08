# -*- coding: utf-8 -*-

from context import wp_find_img
from wp_find_img.helpers import URLHelpers
from wp_find_img.spider import ImgSpider

import unittest

class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_absolute_truth_and_meaning(self):
        assert True

class HelperUrlTestSuite(unittest.TestCase):
    """URLHelper test cases."""

    def test_only_domain(self):
        self.assertEqual(URLHelpers.only_domain("http://www.example.com/example?p=1"), "example.com")
        self.assertEqual(URLHelpers.only_domain("http://localhost:8888/example?p=1"), "localhost")

    def test_no_dynamic(self):
        self.assertEqual("http://www.example.com/example", URLHelpers.no_dynamic("http://www.example.com/example?p=1"))

class SpiderTestSuite(unittest.TestCase):
    """spider test cases"""
    def test_exception_if_no_target(self):
        with self.assertRaises(UserWarning):
            spider = ImgSpider()

if __name__ == '__main__':
    unittest.main()
