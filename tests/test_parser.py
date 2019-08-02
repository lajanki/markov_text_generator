#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import unittest

from src.parsers import text_parser



class ParserTestCase(unittest.TestCase):
	"""Test cases for parsers (BaseParsers and custom parsers)."""

	@classmethod
	def setUp(self):
		self.parser = text_parser.TextParser("foo")

	def test_cleanup_adds_space_after_punctuation(self):
		"""Does cleanup add missing space after a punctuation?"""
		self.parser.content = "This sure is a lovely day.See you later!"
		self.parser.cleanup()
		expected = "This sure is a lovely day. See you later!"
		self.assertEqual(self.parser.content, expected)

		self.parser.content = "come,the day is ours"
		self.parser.cleanup()
		expected = "come, the day is ours"
		self.assertEqual(self.parser.content, expected)

		self.parser.content = "The email is gopa.almostnone@kapina.de"
		self.parser.cleanup()
		expected = "The email is gopa.almostnone@kapina.de"
		self.assertEqual(self.parser.content, expected)

		self.parser.content = "Not today... We'll continue tomorrow."
		self.parser.cleanup()
		expected = "Not today... We'll continue tomorrow."
		self.assertEqual(self.parser.content, expected)



if __name__ == "__main__":
	unittest.main()
