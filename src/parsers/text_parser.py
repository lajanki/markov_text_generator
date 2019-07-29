#!/usr/bin/env python3

import codecs
import glob
import os.path

from src.parsers import base_parser
from src import utils


class TextParser(base_parser.BaseParser):
	"""Joins folder containing .txt files to a single file."""

	def __init__(self, folder):
		"""Setup path to folder containing text fiels to parse."""
		self.path_to_input = os.path.join(utils.BASE, "data", "training", folder)
		ofilename = folder + ".txt"
		super().__init__(ofilename)

	def parse(self):
		"""Reads the contents of files in the input folder into the self.content attribute."""
		if not os.path.isdir(self.path_to_input):
			raise FileNotFoundError("ERROR: no such folder: " + self.path_to_input)

		files = glob.glob(self.path_to_input + "/*.txt")
		combined_words = []
		for file_ in files:
			with codecs.open(file_, encoding="utf8") as f:
				word_list = f.read().split()
				combined_words.extend(word_list)

		self.content = " ".join(combined_words)

