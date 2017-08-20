#!/bin/python
# -*- coding: utf-8 -*-

"""
A JSON based version of text_generator.py. The database version handles file accesses inefficiently
and is quite slow when generating.

This version stores training data as key, value pairs where key is "_" delimitted ngrams parsed
from the text and value is a list of consecutive words to the last word in the key.
"""



import random
import sys
import argparse
import codecs
import glob
import os
import time
import collections
import simplejson as json  # faster decoding than the standard llibrary module

import parse_input

DELIMITER = "_"  # define the delimiter character for the cache file globally, so both classes can access it easily

class Trainer():

	def __init__(self, path, n = 3):
		"""Define paths to the training and the output file as well as the size of the ngrams to look for
		in the training file. The key length in the created .cache file will be n-1
		"""
		self.path = path
		self.n = n # the size of the ngrams for training, the keys of the training dataset will be of length n-1
		cache = os.path.basename(path.rstrip("/"))  # filename + extension
		self.cache = "data/cache/" + os.path.splitext(cache)[0] + ".cache" # define a path for the resulting cache file

	def train(self):
		"""Creates a cache file of word, successors for each word encoutered in the training file.
		The resulting dictionary is stored in a .cache file in data/cache/
		"""
		data = collections.defaultdict(list)
		DELIMITER = "_"
		for ngram in self.ngrams():
			# Use the first n-1 words as a key and add the last word to the list of successors.
			if DELIMITER not in "".join(ngram[:-1]):  # ignore the ngram if the delimiter character is in it
				key = DELIMITER.join(ngram[:-1])
				data[key].append(ngram[-1])

		# Store the result to the cache file
		with codecs.open(self.cache, "w", "utf8") as f:
			json.dump(data, f)

	def ngrams(self):
		"""Generator for creating ngrams from the training data. For instance,
		"What a lovely day" would create the following 2 3-grams:
		[What, a, lovely] and [a, lovely, day]
		Yield:
			the next ngram
		"""
		# Read the training data from file and split by words.
		training_data = self.get_training_data()
		training_data = training_data.split()

		if len(training_data) < self.n:
			return

		# Yield the next batch of ngrams
		for i in range(len(training_data) - (self.n - 1)):
			yield training_data[i: i + self.n]

	def get_training_data(self):
		"""Get the text content of the training data. If self.path is a folder:
		merge it to single .txt file using parse_input.
		"""
		if os.path.isdir(self.path):
			parser = parse_input.TextParser(self.path)
			train_data = parser.parse_folder()
		else:
			with codecs.open(self.path, "r", "utf8") as f:
				train_data = f.read()

		return train_data


class Generator():

	def __init__(self, cache):
		"""Setup locations for cache file."""
		self.cache = cache
		self.cache_data = self.get_cache_data()

	def generate(self, size = 25, seed = None, complete_sentence = False):
		"""Generates a string of size words by randomly selecting words from the successor dictionary using the
		previous n-1 words as the key.
		Arg:
			size (int): number of words the text should contain.
			seed (string): the initial words for the text. If not set, the seed will be randomly selected
				from the training data. Raises a ValueError if the last n-1 words is not a key in the training data.
			complete_sentence (boolean): whether to continue adding words past size to the sentence until a punctuation
				character or a capitalized word is encoutered.
		Return:
			the generated text
		"""
		words = []
		key = random.choice(self.cache_data.keys())

		# check whether the seed was long enough and ends with a valid cache key
		if seed:
			seed = self.validate_seed(seed) # returns the empty string for invalid seeds
			words.append(seed) # the generated text should begin with the seed

		# Fetch new words until text is of correct length.
		while len(words) < size:
			word, key = self.next_word(key)
			words.append(word)

		# To complete a sentence, continue adding words until one that ends with a punctuation mark
		if complete_sentence:
			while not word.endswith((".", "!", "?", "...", ":", ";", ",", "-", u"…")):
				word, key = self.next_word(key)
				words.append(word)

		# Return a properly capitalized and punctuated string.
		return Generator.cleanup(words)

	def next_word(self, key):
		"""Given a key to the cache data, chooses a random word successor. Also generates the
		next key.
		"""
		word = random.choice(self.cache_data[key])

		# Compute new key by joining the last key_length - 1 words of the previous key and the previous word chosen
		key = key.split(DELIMITER)[1:]
		key.append(word)
		key = DELIMITER.join(key)

		return word, key

	def get_cache_data(self):
		"""Get the contents of the cache file as a dictionary."""
		with codecs.open(self.cache, "r", "utf8") as f:
			train_data = json.load(f)
			return train_data

	def validate_seed(self, seed):
		"""Check if a seed is long enough and that the tail matches a key in
		the cache file.
		"""
		key_size = len(self.cache_data.keys()[0].split(DELIMITER)) # the depth value used in training is key_size + 1
		split = seed.split()
		key = DELIMITER.join(split[-key_size:])  # last key_size words of the seed

		# for invalid seeds, return an empty seed and a random key
		if len(split) < key_size or key not in self.cache_data:
			return ""

		return seed



	#===========================================================================#
	# Static helper functions #
	#=========================#

	@staticmethod
	def cleanup(tokens):
		"""cleanup a sentence by capitalizing the first letter, remove conjuctions like "and" and "to"
		from the end and add a punctuation mark.
		Arg:
			tokens (list): the sentence to normalize as a list of words
		Return:
			the normalized sentence as a string
		"""
		# Capitalize the first word (calling capitalize() on the whole string would
		# decapitalize everyting else).
		tokens[0] = tokens[0].capitalize()
		text = " ".join(tokens)
		text = text.lstrip(" -*")

		# Replace opening parathesis with a comma and remove closing paranthesesis and
		# replace other inconvenient characters.
		replacements = [
			(" (", ","),
			("(", ""), # in case the first character of a sentence is "("
			(")", ""),
			("\"", ""),
			(u"“", ""),
			(u"”", ""),
			(u"”", ""),
			(u"•", ""),
			(u"●", ""),
			(u"—", ""),
			(u"…", "...")
		]
		for item in replacements:
			text = text.replace(item[0], item[1])


		text = text.rstrip(",;:- ")
		if not text.endswith((".", "!", "?", "...")):
			rand = random.random()
			if rand < 0.81:
				end = "."  # "." should have the greatest change of getting selected
			else:
				end = random.choice(("!", "?", "..."))  # choose evenly between the rest

			text += end

		return text


	@staticmethod
	def show_menu(files):
		"""Prints a list of existing .cache files and asks for user input on which
		generator to use.
		Args:
			files (list): a list of filepaths to .cache files in the data folder
		Return:
			the path to the .cache the user selected
		"""
		print "Select which existing generator to use:"
		for i, file in enumerate(files):
			print i+1, os.path.basename(file)

		# Ask for user input and create a generator.
		ans = int(raw_input("Input: "))
		path_to_cache = files[ans-1]

		return path_to_cache


	#===========================================================================#
	# Main #
	#======#

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates random text based on an input sample.")
	parser.add_argument("--train", help="Train the generator. Creates a cache file needed to generate random text.", nargs = 2, metavar = ("path", "depth"))
	parser.add_argument("--generate", help="Generate text with p paragraphs of about n words each.", nargs = 3, metavar = ("cache", "p", "n"))
	args = parser.parse_args()
	#print args


	if args.train:
		path = args.train[0]
		n = int(args.train[1])
		trainer = Trainer(path, n)

		# check whether the input path is valid and whether a cache file for it already exists
		if not os.path.isfile(path) and not os.path.isdir(path):
			print "ERROR: No such training file or folder:", path
			sys.exit()

		elif os.path.isfile(trainer.cache):
			ans = raw_input("WARNING: There already is a cache for " + trainer.path + ". Are you sure you want to replace it (N/y)?\n")
			if ans != "y":
				sys.exit()

		print "Building a dataset with size {}...".format(trainer.n)
		trainer.train()


	elif args.generate:
		cache = args.generate[0]
		p = int(args.generate[1])
		n = int(args.generate[2])

		try:
			generator = Generator(cache)
			paragraphs = []
			for i in range(p):
				p_size = int(random.gauss(n, n/4.0))
				paragraphs.append(generator.generate(p_size, complete_sentence = True))

			text = "\n\n".join(paragraphs)
			print text

		except IOError as err:
			print "ERROR: Invalid cache file:", cache
