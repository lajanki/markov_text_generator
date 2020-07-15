#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test cases for src/generator.py

import unittest
from unittest.mock import Mock
import os.path
import json

from src import generator
from src import utils


BASE =  os.path.dirname(__file__)


class GeneratorTestCase(unittest.TestCase):
	"""Test cases for generating text."""

	@classmethod
	def setUpClass(self):
		generator.Generator.get_cache_data = Mock()
		self.generator = generator.Generator("foofile")

		# Manually read training output from mock file
		with open(os.path.join(BASE, "mock_train_file.dat")) as f:
			self.generator.cache_data = json.load(f)

	def test_end_with_punctuation(self):
		"""Does the generated text end with punctuation?"""
		text = self.generator.generate(complete_sentence=True)
		punctuation = (".", "!", "?", "...", "…")
		self.assertTrue(text.endswith(punctuation))

	def test_cleanup(self):
		"""Does utils.cleanup capitalize the first letter and remove non-sentence ending
		punctuation?
		"""
		tokens1 = "some text here,".split()
		tokens2 = "Organized structure is required!".split()
		tokens3 = "i have never agreed with any of the above:".split()

		res1 = utils.cleanup(tokens1)
		res2 = utils.cleanup(tokens2)
		res3 = utils.cleanup(tokens3)

		self.assertEqual(res1, "Some text here")
		self.assertEqual(res2, "Organized structure is required!")
		self.assertEqual(res3, "I have never agreed with any of the above")


if __name__ == "__main__":
	unittest.main()