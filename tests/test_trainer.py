#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test cases for src/trainer.py


import unittest
from unittest.mock import patch, mock_open
import os.path

from src import trainer
from src import utils


BASE =  os.path.dirname(__file__)

class TrainerTestCase(unittest.TestCase):
	"""Test cases for training a generator."""

	@classmethod
	def setUpClass(self):
		self.trainer = trainer.Trainer("foofile")

		# Manaully reset the training input and output file paths to existing files
		self.trainer.path_to_train_file = os.path.join(BASE, "mock_train_file.txt")
		self.trainer.cache_file = os.path.join(BASE, "mock_train_file.dat")

		self.trainer.train()

	def test_ngram_length(self):
		"""Are created ngram of correct length?"""
		ngrams = self.trainer.ngrams()
		item = next(ngrams)
		self.assertEqual(len(item), self.trainer.n)

	@patch("builtins.open", new_callable=mock_open, read_data="What a lovely day, I go!")
	def test_ngram_value2(self, mock_open):
		"""Does ngrams output expected ngrams?"""
		dummy_train_data = "What a lovely day, I go!"

		ngrams = self.trainer.ngrams()

		expected = [
				["What", "a", "lovely"],
				["a", "lovely", "day,"],
				["lovely", "day,", "I"],
				["day,", "I", "go!"],
		]

		self.assertEqual(list(ngrams), expected)

	def test_validate_raises_error_on_invalid_training_file(self):
		"""Does validate raise error if trainer is created with invalid filename?"""
		orig_path_to_train_file = self.trainer.path_to_train_file
		self.trainer.path_to_train_file = "foofile"
		self.assertRaises(FileNotFoundError, self.trainer.validate)

		# set path attribute back to the original value
		self.trainer.path_to_train_file = orig_path_to_train_file




if __name__ == "__main__":
	unittest.main()
