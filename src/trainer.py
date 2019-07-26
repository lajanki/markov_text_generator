#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trainer class. Given a plain text file in data/training a trainer splits it into ngrams and further
into a json file where keys are the n-1 leftmost words of each ngram and values are list of rightmost
words corresponding to each ngram.

A trainer outputs the resulting json file to data/cache which is given as an input to a generator.
Generating is done by choosing random n-1 rightmost words of the key + a random followup word.
"""

import codecs
import os
import collections
import simplejson as json  # faster decoding than the standard llibrary module

from src import utils




class Trainer():

	def __init__(self, train_text_file, n = 3):
		"""Define filename to the training plain text file in data/trainnig and output json file in data/cache.
		Also sets the size of the ngrams to use for training.
		"""
		self.path_to_train_file = os.path.join(utils.BASE, "data", "training", train_text_file)
		cache_filename = os.path.splitext(train_text_file)[0] + ".dat" # filename with new extension
		self.cache_file = os.path.join(utils.BASE, "data", "cache", cache_filename)

		self.n = n # the size of the ngrams for training, the keys of the output json file will be the first n-1 words

	def train(self):
		"""Create a the training file by ngramming the original text into n-1 predecessor and 1 succor key value
		dict and store to file.
		"""
		data = collections.defaultdict(list)
		for ngram in self.ngrams():
			# Use the first n-1 words as a key and add the last word to the list of successors.
			if utils.DELIMITER not in "".join(ngram[:-1]):  # ignore ngrams containing the key join delimiter character "_" 
				key = utils.DELIMITER.join(ngram[:-1])
				data[key].append(ngram[-1])

		# Store the result to the cache file
		with codecs.open(self.cache_file, "w", "utf8") as f:
			json.dump(data, f)

	def ngrams(self):
		"""Generator for creating ngrams from the training data. For instance,
		"What a lovely day" would create the following two 3-grams:
			[What, a, lovely], and
			[a, lovely, day]
		Yield:
			the next ngram
		"""
		# Read the training data from file and split by words.
		with codecs.open(self.path_to_train_file, "r", "utf8") as f:
			train_data = f.read()
			train_data = train_data.split()

		if len(train_data) < self.n:
			return

		# Yield each ngram
		for i in range(len(train_data) - (self.n - 1)):
			yield train_data[i: i + self.n]
