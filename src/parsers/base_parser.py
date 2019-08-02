#!/usr/bin/env python3

import abc
import codecs
import glob
import os.path

from src import utils


class BaseParser(abc.ABC):
	"""Base class for parsers."""

	def __init__(self, ofile):
		"""Setup path to output file where the result should be saved."""
		self.path_to_ofile = os.path.join(utils.BASE, "data", "training", ofile)
		self.content = None

	def run(self):
		"""Wrapper for running the parser and saving the results."""
		self.parse()
		self.cleanup()
		self.save()

	@abc.abstractmethod
	def parse(self):
		"""Parse input data for the trainer. Actual implementation depends on the type of content
		to parse and should be implemented in subclass. Result should be a string set as the 
		self.content attribute.
		"""
		pass

	def save(self):
		"""Store content to output file."""
		if not self.content:
			raise ValueError("ERROR: nothing to save, run parse first")

		output = os.path.join(utils.BASE, "data", "training", self.path_to_ofile)  
		with open(output, "w") as f:
			f.write(self.content)

		print("Created a dump at", output)

	def cleanup(self):
		"""Cleanup the content string: add missing space after puncutation."""
		for word in self.content.split():

			if len(word) > 3:
				# add missing space after period if not an email or url 
				if "." in word and not any([c in word for c in ("@", "http", "...", "www")]):
					new_word = word.replace(".", ". ").rstrip()
					self.content = self.content.replace(word, new_word)

				# for other characters, add the space and strip any extra space at the end
				for char in (",", "!", "?"):
					if char in word:
						new_word = word.replace(char, char + " ").rstrip()
						self.content = self.content.replace(word, new_word)