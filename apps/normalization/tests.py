"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from apps.normalization.handlers import NormalizationHandler


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
        
    def test_from_numeric(self):
        normalizer = NormalizationHandler()
        self.assertEqual(normalizer.from_numeric("621st"),["six","hundred","twenty","first"])
        self.assertEqual(normalizer.from_numeric("11"),["eleven"])
#         print(normalizer.from_numeric("13"))
#         print(normalizer.from_numeric("11th"))
#         print(normalizer.from_numeric("3rd"))
#         print(normalizer.from_numeric("611th"))
#         print(normalizer.from_numeric("611"))
#         print(normalizer.from_numeric("21"))
#         print(normalizer.from_numeric("20"))
#         print(normalizer.from_numeric("2342nd"))
#         print(normalizer.from_numeric("600"))
#         print(normalizer.from_numeric("4600th"))
#         print(normalizer.from_numeric("1112th"))

    def test_split_abbreviations(self):
        normalizer = NormalizationHandler()
        self.assertEqual(normalizer.split_abbreviations("ABC1234ABC1"), ["ABC","1234","ABC","1"]) 