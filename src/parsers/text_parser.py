#!/usr/bin/env python3

import codecs
import glob
import os

from src import utils


class TextParser:
	"""Joins folder containing .txt files to a single file."""

	def __init__(self, folder):
		"""Set absolute path to the data folder."""
		self.folder = folder
		self.path = os.path.join(utils.BASE, "data", "training", folder)
		self.text = ""

	def parse(self):
		"""Reads the contents of files in the input folder into a single string.
		Result is stored as the self.text attribute.
		"""
		if not os.path.isdir(self.path):
			raise ValueError("ERROR: no such folder: " + self.folder)

		files = glob.glob(self.path + "/*.txt")
		combined_words = []
		for file_ in files:
			with codecs.open(file_, encoding="utf8") as f:
				word_list = f.read().split()
				combined_words.extend(word_list)

		self.text = " ".join(combined_words)

	def save(self):
		"""Store text to a file."""
		if not self.text:
			raise ValueError("ERROR: nothing to save, run parse first")

		# store output in the training folder with the same name as the input folder
		filename = self.folder + ".txt"
		output = os.path.join(utils.BASE, "data", "training", filename)  
		with codecs.open(output, mode="w", encoding="utf8") as f:
			f.write(self.text)

		print("Created a dump at", output)