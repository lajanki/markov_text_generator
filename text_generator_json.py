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


class MarkovGenerator():

	def __init__(self, *args, **kwargs):
		"""An initializer accepting two ways to create a new generator:
		  * A path to a training data file/folder to train a new generator, or
		  * A path to an existing cache file when selecting one of previously trained generators.
		kwargs:
			input (string): path to a file to be used to train a generator
			cache (string): path to an existing .cache file
			depth (int): the depth of the Markov chain used to train the generator. This only
			matters when "input" is present. Determines how many of the current
				text should be matched to new data from the cache. For a true Markov chain
				the default value of 1 should be used*. High values will generate text barely
				different from the original text.
				* A true Markov chain process would also consider probabilities when determining
				  the next word from the cache, this script chooses them randomly.
		"""
		self.input = kwargs.get("input", None)
		self.cache = kwargs.get("cache", None)
		self.depth = kwargs.get("depth", 2) # ngram length, ie. number of words to store in a database row
		self.delim = "_"  # a delimiter for joining training data words as dictionary keys, should be character not used in the data itself

		# Check that either an input file or cache file was specified.
		if self.input is None and self.cache is None:
			print "ERROR: Neither a training file, nor an existing cache file was specified."
			sys.exit()

		# If the input argument was specified, define a location for the cache under the data folder:
		# keep the basename and change the extension.
		if self.input:
			filename = os.path.basename(self.input)
			self.cache = "./data/" + os.path.splitext(filename)[0] + ".dat"


	#===========================================================================#
	# Training and generation #
	#=========================#

		
	def ngrams(self):
		"""Processes the input text into ngrams. For n=3 generates as
		"What a lovely day" => [ [What, a, lovely], [a, lovely, day] ]
		Yield:
			the next ngram
		"""
		# Read the training data from file and split by words.
		with codecs.open(self.input, "r", "utf8") as f:
			train_data = f.read().split()
			train_data = [word for word in train_data if not any(item in word for item in ("http://", "https://", "@", "#"))] # remove urls and email addresses

		if len(train_data) < self.depth:
			return
		
		# Yield the next batch of ngrams
		for i in range(len(train_data) - (self.depth - 1)): # the starting index should ignore the last n words
			yield train_data[i: i + self.depth]
			

	def train(self):
		"""Train a generator by creating a dictionary of word: [successors] for each word encoutered.
		The list of successors counts multiplicities. Finally, store the dictionary to file.
		"""
		# Check if a cache file already exists.
		if os.path.isfile(self.cache):
			ans = raw_input("WARNING: There already is a cache for " + self.input + ". Are you sure you want to replace it (N/y)?\n")
			if ans != "y":
				sys.exit()

		# Check if self.input is a folder and parse its contents to temp file for training.
		temp_created = False
		if os.path.isdir(self.input):
			self.input = parse_input.parse_folder(self.input)
			temp_created = True


		print "Building a dataset with depth {}...".format(self.depth-1)
		data = collections.defaultdict(list)
		for ngram in self.ngrams():
			# Use the first n-1 words as a key and add the last word to the list of successors.
			if self.delim not in "".join(ngram[:-1]):  # check that the delimiter is not an actual character in the ngram
				key = self.delim.join(ngram[:-1])
				data[key].append(ngram[-1]) 
				#data[key].add(ngram[-1]) 

		# Store to file.
		#data = {k: list(v) for k,v in data.items()}
		with codecs.open(self.cache, "w", "utf8") as f:
			json.dump(data, f)

		if temp_created:
			os.remove(self.input)
			print "Temporary files deleted."


	def generate_markov_text(self, size = 25, seed = None, complete_sentence = False):
		"""Generates a string of length size by randomly selecting words from the successor dictionary using the
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
		if not os.path.isfile(self.cache):
			print "ERROR: No cache file for " + self.input + ". Run with --train to create one first."
			sys.exit()


		words = []
		with codecs.open(self.cache, "r", "utf8") as f:
			train_data = json.load(f)
			depth = len(train_data.keys()[0].split(self.delim))

		if seed:
			split = seed.split()
			# Check if the seed is long enough:
			if len(split) < depth:
				raise ValueError("Invalid seed: Need at least {} words, received \"{}\"".format(depth, seed))

			# Is the first depth words of the seed a valid key?
			key = self.delim.join(split[:depth])
			if key not in train_data:
				raise ValueError("Invalid seed: training data doesn't contain {}".format(key))
			words.append(seed)

		else:
			key = random.choice(train_data.keys())

		# Fetch new words until text is correct length.
		while len(words) < size:
			word = random.choice(train_data[key])
			words.append(word)

			# Compute new key from the last depth-1 words of the previous key and the last word chosen. 
			key = key.split(self.delim)[1:]
			key.append(word)
			key = self.delim.join(key)


		# Continue adding words until one that ends with a sentence ending character.
		if complete_sentence:
			while not word.endswith((".", "!", "?", "...", ":", ";", ",", "-", u"…")):
				word = random.choice(train_data[key])
				words.append(word)

				key = key.split(self.delim)[1:]
				key.append(word)
				key = self.delim.join(key)
		

		# Return a properly capitalized and punctuated string.
		return MarkovGenerator.cleanup(words)


	#===========================================================================#
	# Helper functions #
	#==================#

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
	parser.add_argument("input", help="Text file containing a writing sample used to train the generator.", nargs="?")
	parser.add_argument("--train", help="Train the generator. Creates a cache file needed to generate random text.", action="store_true")
	parser.add_argument("--generate", help="Generate text with p paragraphs with about n words each.", nargs=2, type=int, metavar = ("p", "n"))
	parser.add_argument("--depth", help="How many previous words should be considered when generating new text. Valid values are 1,2 and 3.",
		nargs="?", metavar="depth", type=int, default=1, const=1, choices=[1,2,3])
	args = parser.parse_args()
	#print args


	# If no input file present, list the existing trained cache files and ask for user input.
	if not args.input:
		files = glob.glob("./data/*.dat")
		path_to_cache = MarkovGenerator.show_menu(files)

		# Generate a text of random length.
		gen = MarkovGenerator(cache = path_to_cache)
		n = int(random.gauss(25, 25/4.0)) # select text length from a Gaussian distribution

		print gen.generate_markov_text(n)

		# Display an interactive menu for generating more text, returning to the menu or exiting until the user exits.
		while True:
			ans = raw_input("***usage: [m]enu, [e]xit, any other key for more.***\n")
			if ans == "m":
				path_to_cache = MarkovGenerator.show_menu(files)
				gen = MarkovGenerator(cache = path_to_cache)
				print gen.generate_markov_text(n)

			elif ans in ("e", "q"):
				sys.exit()

			else:
				print gen.generate_markov_text(n)



	# Create a generator based on user input, invalid filepath causes a sys.exit() call.
	else:
		# Check user input is a valid path.
		if not (os.path.isfile(args.input) or os.path.isdir(args.input)):
			print "ERROR: No such file or folder " + args.input
			sys.exit()

		gen = MarkovGenerator(input = args.input, depth = args.depth + 1)

	if args.train:
		gen.train()
		print "Cache stored at", gen.cache

	elif args.generate:
		start = time.time()
		p = args.generate[0]
		n = args.generate[1]

		paragraphs = []
		for i in range(p):
			p_size = int(random.gauss(n, n/4.0))
			paragraphs.append(gen.generate_markov_text(p_size))
		end = time.time()

		text = "\n\n".join(paragraphs)
		print text
		#print end - start
	

