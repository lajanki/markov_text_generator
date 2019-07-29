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
		self.save()

	@abc.abstractmethod
	def parse(self):
		"""This method should be implemented in subclass and set the self.content attribute
		to the parsed content.
		"""
		pass

	def save(self):
		"""Store content to output file."""
		if not self.content:
			raise ValueError("ERROR: nothing to save, run parse first")

		output = os.path.join(utils.BASE, "data", "training", self.path_to_ofile)  
		with codecs.open(output, mode="w", encoding="utf8") as f:
			f.write(self.content)

		print("Created a dump at", output)