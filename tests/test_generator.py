#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import json
import codecs
import string
import random

# change working directory in order for the relative paths in text_generator to work
# as well as to be able to import the module
os.chdir("../")
import text_generator




class TrainerTestCase(unittest.TestCase):
	"""Test cases for training a generator."""

	@classmethod
	def setUpClass(self):
		self.file_trainer = text_generator.Trainer("data/training/realDonaldTrump/realDonaldTrump.txt")
		self.folder_trainer = text_generator.Trainer("data/training/poems/")
		self.invalid_trainer = text_generator.Trainer("data/nosuchfile.ext")

	def testNgramLength(self):
		"""Are the created ngrams correct length?"""
		ngrams = self.file_trainer.ngrams()
		item = next(ngrams)
		self.assertEqual(len(item), self.file_trainer.n, "Created ngrams are not of correct length.")

	def testCacheLocation(self):
		"""Is the cache location correct?"""
		expected = "data/cache/realDonaldTrump.cache"
		self.assertEqual(self.file_trainer.cache, expected, "Cache location incorrect for the file based trainer.")

		# same for the folder trainer: in particular the cache file should not be called '.cache'
		expected = "data/cache/poems.cache"
		self.assertEqual(self.folder_trainer.cache, expected, "Cache location incorrect for the folder based trainer.")

	def testInvalidPathRaisesError(self):
		"""Does trying to use a non-existing path as a training data source raise an error?"""
		self.assertRaises(IOError, self.invalid_trainer.get_training_data)

	def testTrainingDataNotEmpty(self):
		"""Is the created cache file for a valid training file nonempty?"""
		# NOTE: this will overwrite any existing cache file for the poem trainer!
		# TODO (if I ever feel energetic enough): setup an actual testing environment
		self.folder_trainer.train()
		with codecs.open(self.folder_trainer.cache, "r", "utf8") as f:
			train_data = json.load(f)
		self.assertNotEqual(train_data, {})


class GeneratorTestCase(unittest.TestCase):
	"""Test cases for generating text."""

	@classmethod
	def setUpClass(self):
		self.file_generator = text_generator.Generator("data/cache/realDonaldTrump.cache")


	def testInvalidPathRaisesError(self):
		"""Does trying to create a generator with invalid path raise an Error?"""
		self.assertRaises(IOError, text_generator.Generator, "data/cache/nosuchfile.cache")

	def testSeedValidationOnInvalid(self):
		"""Does an invalid seed return the empty string?"""
		s = "ThisIsAlmostCertainlyAnInvalidSeed.ItSureWouldBeStrangeIfThereWereAllOneWordStringLikeThisInOneOfDonaldTrump'sTweets."
		seed = self.file_generator.validate_seed(s)
		self.assertEqual(seed, "", "The seed did not get set to the empty string on invalid entry.")

		def create_random_string():
			"""Nested helper function for creating a random 5 letter string."""
			return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))

		random_garbage = " ".join([create_random_string() for _ in range(10)])
		s = "This has more words but ends with random garbage " + random_garbage
		seed = self.file_generator.validate_seed(s)
		self.assertEqual(seed, "", "The seed did not get set to the empty string on invalid entry.")

	def testSeedValidationOnValid(self):
		"""Does the seed remain the same when actual tweet content is used?"""
		s = "I made a lot of money in Atlantic City and left"
		seed = self.file_generator.validate_seed(s)
		self.assertEqual(seed, s, "Validation incorrectly changed the seed")

	def testBeginsWithSeed(self):
		"""Does the generated text begin with (a valid) seed?"""
		s = "I made a lot of money in Atlantic City and left"
		text = self.file_generator.generate(seed = s)
		self.assertTrue(text.lower().startswith(s.lower()))

	def endsWithPunctuation(self):
		text = self.file_generator.generate()
		self.assertTrue(text.endswith((".", "!", "?", "...")))


if __name__ == "__main__":
	# Create a test suite and run the tests.
	# Note that this only matters when this script is run directly. Use
	# python -m unittest -v test_generator to run all tests!
	suite = unittest.TestLoader().loadTestsFromTestCase(TrainerTestCase)
	unittest.TextTestRunner(verbosity=2).run(suite)
