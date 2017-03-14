# -*- coding: utf-8 -*-

import time

from context import wp_find_img
from wp_find_img.helpers import URLHelpers
from wp_find_img.helpers import TimeHelpers
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

class HelperTimeTestSuite(unittest.TestCase):
    """ TimeHelper test cases. """

    test_time_t = 489038141.726931
    test_time_str = '2017-03-09_16-42-21'

    def test_strptime(self):
        time_t = TimeHelpers.safeStrpTime(self.test_time_str)
        self.assertEqual(time_t, self.test_time_t)

    def test_timetostring(self):
        time_str = TimeHelpers.safeTimeToString(self.test_time_t)
        self.assertEqual(time_str, self.test_time_str)

    def test_timestamp(self):
        timestamp = TimeHelpers.getSafeTimeStamp()
        self.assertIsInstance(timestamp, str)

class SpiderTestSuite(unittest.TestCase):
    """spider test cases"""
    def test_exception_if_no_target(self):
        with self.assertRaises(UserWarning):
            spider = ImgSpider()

if __name__ == '__main__':
    unittest.main()
