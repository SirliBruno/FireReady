import unittest
from pipeline.core import parse_utc
class TimestampTest(unittest.TestCase):
    def test_midnight(self):
        self.assertIsNotNone(parse_utc('2020-01-01','0000'))
