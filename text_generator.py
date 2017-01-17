#!/bin/python
# -*- coding: utf-8 -*-

"""
A random text generator using Markov chains. On the training phase pairs of consecutive words
are parsed for following words are stored as a cache. Text is then generated by randomly
picking 3-word combinations from the cache.

based on
https://gist.github.com/agiliq/131679#file-gistfile1-py
https://github.com/codebox/markov-text

3.1.2017
"""



import random
import json
import sys
import argparse
import codecs
import random
import glob
import os
import sqlite3 as lite

import parse_input


class MarkovGenerator():

	def __init__(self, *args, **kwargs):
		"""An initializer accepting two ways to create a new generator: either pass in a
		path to a training data file for training a new generator, or a path to an existing
		cache file when selecting one of previously trained generators.
		kwargs:
			input (string): path to a file to be used to train a generator
			cache (string): path to an existing .cache file
				Note: One of these should be present.
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

		# Either an input file or cache file needs to be present. (though this should always be the case
		# since creating a generator object is well controlled under main)
		if self.input is None and self.cache is None:
			print "ERROR: Neither a training file, nor an existing cache file was specified."
			sys.exit()

		# If the input argument was specified, check whether a file or folder with that
		# name actually exists, define a location for the cache and, if input is a folder,
		# dump its contents to a temporary file.
		if self.input:
			# Set path to for the cache: keep the basename and change the extension.
			filename = os.path.basename(self.input)
			self.cache = "training-data/" + os.path.splitext(filename)[0] + ".cache"

		
	def ngrams(self):
		"""Processes the input text into ngrams. For n=3 generates as
		"What a lovely day" => [ [What, a, lovely], [a, lovely, day] ]
		Yield:
			the next ngram
		"""
		# Read the training data from file and split by words.
		with codecs.open(self.input, "r", "utf8") as f:
			train_data = f.read().split()

		#n = self.depth
		if len(train_data) < self.depth:
			return
		
		# Yield the next batch of ngrams
		for i in range(len(train_data) - (self.depth - 1)): # the starting index should ignore the last n words
			yield train_data[i: i + self.depth]
			

	def train(self):
		"""Train a generator by storing all detected ngrams to a database with n word columns."""
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


		con = lite.connect(self.cache)
		cur = con.cursor()

		# Generate the SQL for "CREATE TABLE ngrams (w1 TEXT NOT NULL, w2 TEXT NOT NULL, ... wn TEXT NOT NULL, UNIQUE(w1, w2, ..., wn) )",
		# column names can't be targeted for parameter substitution.
		colnames = ["w" + str(i) for i in range(1, self.depth+1)]  # db column names w1, w2, ... wn

		sql = "CREATE TABLE ngrams ("
		for col in colnames:
			sql += col + " TEXT NOT NULL, "
		sql += "UNIQUE(" + ", ".join(colnames) + ") )"

		print "Building a database with depth {}...".format(self.depth-1)
		with con:
			cur.execute("DROP TABLE IF EXISTS ngrams")  # remove previous data
			cur.execute(sql)

			for ngram in self.ngrams():
				try:
					subs = ", ".join( ["?" for i in range(self.depth)] )  # a string of "?, ?, ..., ?" for parameter substitution
					sql = "INSERT INTO ngrams VALUES ({})".format(subs)
					col_values = () 
					cur.execute(sql, tuple(ngram))

				# Skip ngrams that are already in the database.
				except lite.IntegrityError:
					continue

		# Delete the input file if it was a temp file created in __init__().
		if temp_created:
			os.remove(self.input)
			print "Temporary files deleted."

		
	def generate_markov_text(self, size = 25):
		"""Generates a string of length size by randomly selecting words from the cache database such that
		the first n-1 words of the row fetched matches the last n-1 words of the current generated text.
		Arg:
			size (int): number of words the text should contain.
		Return:
			the generated text
		"""
		if not os.path.isfile(self.cache):
			print "ERROR: No cache file for " + self.input + ". Run with --train to create one first."
			sys.exit()

		con = lite.connect(self.cache)
		cur = con.cursor()

		# Randomly select 1 row from the database to act as a seed for text generation.
		words = []
		with con:
			cur.execute("SELECT * FROM ngrams ORDER BY RANDOM() LIMIT 1")
			row = cur.fetchone()
			words.extend(row[:-1])
			depth = len(row)

			# Fetch rows and add new words one at a time until text length == size.
			# The first n-1 words of the next row should match to the n-1 last words
			# of the previous row.
			while len(words) < size:
				# Format the SQL for a ...WHERE w1 = ? AND w2 = ? ... AND w(n-1) = ?
				cols = " AND ".join( ["w{} = ?".format(i) for i in range(1, depth)] )  # (range(1,n) ends at n-1!)
				sql = "SELECT * FROM ngrams WHERE {} ORDER BY RANDOM() LIMIT 1".format(cols)
				cur.execute(sql, tuple(row[1:]))
				row = cur.fetchone()
				words.append(row[-1])  # add the last word of the fetched row to words

		# Return a properly capitalized and punctuated string.
		return MarkovGenerator.normalize(words)


	####################
	# Helper functions #
	####################

	def get_depth(self):
		"""Determine the depth (ie. number of columns) of the cache file database."""
		con = lite.connect(self.cache)
		cur = con.cursor()

		with con:
			cur.execute("SELECT * FROM ngrams LIMIT 1")
			ncol = len(cur.fetchone())

		return ncol


	@staticmethod
	def normalize(sent):
		"""Normalize a sentence by capitalizing the first letter and any letters following end of sentences.
		TODO:
			* don't end the sentence with conjunctions like "and".
			* ignore paranthesis? randomly add missinf paranthesis?, replace ( with a comma?
		Arg:
			sent (list): the sentence to normalize as a list of words
		Return:
			the normalized sentence as a string
		"""
		# Capitalize the first word (calling capitalize() on the whole string would
		# decapitalize everyting else).
		sent[0] = sent[0].capitalize()
		
		# Randomly select a punctuation token from [., !, ?, ...] to append at the end.
		rand = random.random()
		if rand < 0.81:
			end = "."  # "." should have the greatest change of getting selected
		else:
			end = random.choice(("!", "?", "..."))  # choose evenly between the rest

		# Check that sent doesn't already end with a punctuation.
		sent[-1] = sent[-1].rstrip(",:- ")  # strip any non sentence ending punctuation
		if not sent[-1].endswith((".", "!", "?", "...")):
			sent[-1] = sent[-1] + end

		return " ".join(sent)


	@staticmethod
	def show_menu(files):
		"""Prints a list of existing .cache files and asks for user input on which
		generator to use.
		Args:
			files (list): a list of filepaths to .cache files in training-data
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


	########
	# Main #
	########

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
		files = glob.glob("training-data/*.cache")
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
		# Check user input is a valid path,
		# Note: it's enough to check for files since __init__() checks for folders anyway.
		if not (os.path.isfile(args.input) or os.path.isdir(args.input)):
			print "ERROR: No such file or folder " + args.input
			sys.exit()

		gen = MarkovGenerator(input = args.input, depth = args.depth + 1)

	if args.train:
		gen.train()
		print "Cache stored at", gen.cache

	elif args.generate:
		p = args.generate[0]
		n = args.generate[1]

		paragraphs = []
		for i in range(p):
			p_size = int(random.gauss(n, n/4.0))
			paragraphs.append(gen.generate_markov_text(p_size))

		text = "\n\n".join(paragraphs)
		print text
