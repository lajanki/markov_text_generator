#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generator class. Given a .dat file data/cache generates text by chaining randomly selected keys with
randomly selected successor words. Initial key is randomized, successive keys are are generated
by joining the rightmost n-2 keywords with the selected successor. Since keys in the cache file
are ngrams of length n-1, this method will result in valid keys.
"""

import codecs
import os
import random
import simplejson as json  # faster decoding than the standard llibrary module

from src import utils



class Generator():

	def __init__(self, cache_file):
		"""Load the cache file."""
		self.path_to_cache_file = os.path.join(utils.BASE, "data", "cache", cache_file)
		self.cache_data = self.get_cache_data()

	def generate(self, size = 25, complete_sentence = False):
		"""Generates a string of size words by randomly selecting words from the successor dictionary using the
		previous n-1 words as the key.
		Arg:
			size (int): number of words the text should contain.
			complete_sentence (boolean): whether to continue adding words past size to the sentence until a punctuation
				character or a capitalized word is encoutered.
		Return:
			the generated text
		"""
		words = []
		# Randomly select initial key to start generating from (note, key is not included in the actual text)
		cache_keys = list(self.cache_data.keys()) # convert dict_keys to list for random.choice
		key = random.choice(cache_keys)

		# Fetch new words until text is of correct length.
		while len(words) < size:
			word, key = self.next_word(key)
			words.append(word)

		# To complete a sentence, continue adding words until one that ends with a punctuation mark
		if complete_sentence:
			while not word.endswith((".", "!", "?", "...", u"…")):
				word, key = self.next_word(key)
				words.append(word)

		# Return a properly capitalized and punctuated string.
		return utils.cleanup(words)

	def generate_paragraphs(self, size, paragraphs):
		"""Generate text of number of paragraphs of given length.
		Args:
			size (int): word length of each paragraph
			paragraphs (int) number of paragraphs
		"""
		text = []
		# generate paragraph size from a normal distribution using size as the mean
		# and a fraction of size as the standard deviation
		for _ in range(paragraphs):
			p_sigma = max([int(size/3), 5])
			p_size = int(random.gauss(size, p_sigma))
			p = self.generate(p_size, True)
			text.append(p)

		return "\n\n".join(text)

	def next_word(self, key):
		"""Given a key to the cache data, chooses a random word successor. Also generates the
		next key.
		"""
		try:
			word = random.choice(self.cache_data[key])

			# Compute new key by joining the last n - 2 words of the previous key and the word chosen above
			key = key.split(utils.DELIMITER)[1:]
			key.append(word)
			key = utils.DELIMITER.join(key)

		# The random nature of the generation algorithm may attempt to use the last n-1 words of the last ngram as a key,
		# this might not be a valid key. In such case, choose a random key and successor.
		except KeyError as e:
			key = random.choice(self.cache_data.keys())
			word = random.choice(self.cache_data[key])

		return word, key

	def get_cache_data(self):
		"""Get the contents of the cache file as a dictionary."""
		try:
			with codecs.open(self.path_to_cache_file, "r", "utf8") as f:
				train_data = json.load(f)
				return train_data
		except FileNotFoundError:
			msg = "Invalid model: {}".format(self.path_to_cache_file)
			raise FileNotFoundError(msg)


