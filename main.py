#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Program entrypoint. Provides a command line interface for training new models and generating text
using existing models.

For parsing new training data using one of the parsers in src/parsers, see input_parser.py
"""

import os
import argparse

from src import utils
from src import generator
from src import trainer



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates random text from sample input")
	parser.add_argument("--generate", help="Generate text using a model in data/cache", metavar="model")
	parser.add_argument("size", help="Generated text size", nargs="?", default=25, type=int, metavar="size")
	parser.add_argument("--complete-sentence", help="Continue geenrating past size until next punctuation ", action="store_true")	
	parser.add_argument("--train", help="Train a model usinginput plain text file from data/training", metavar="train-data")
 
	#subparsers = parser.add_subparsers(help='sub-command help')
	# create the parser for the generate subcommands


	args = parser.parse_args()
	print(args)

	if args.generate is not None:
		gen = generator.Generator(args.generate)
		text = gen.generate(args.size, args.complete_sentence)
		print(text)

	elif args.train is not None:
		trn = trainer.Trainer(args.train)
		trn.validate() # check existence of args.train
		trn.train()