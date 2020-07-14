#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Program entrypoint. Provides a command line interface for training new models and generating text
using existing models.

For parsing new training data using one of the parsers in src/parsers, see parse_input.py
"""

import os.path
import glob
import argparse

from src import utils
from src import generator
from src import trainer


# create list of valid input file for --train and --generate options
models = glob.glob("data/cache/*.dat")
models = list(map(os.path.basename, models))
training_files = glob.glob("data/training/*.txt")
training_files = list(map(os.path.basename, training_files))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates random text from sample input")
	parser.add_argument("--generate", help="Generate text using a model in data/cache", metavar="model", choices=models)
	parser.add_argument("nwords", help="Number of words to generate for each paragraph. Defaults to 25", nargs="?", default=25, type=int, metavar="size")
	parser.add_argument("paragraphs", help="Number of paragraphs to generate. Defaults to 1", nargs="?", default=1, type=int, metavar="paragraphs")	

	parser.add_argument("--train", help="Train a model usinginput plain text file from data/training", metavar="train-data", choices=training_files)
	parser.add_argument("ngram", help="ngram size for training. Defaults to 3", nargs="?", metavar="n", type=int, default=3) 
	args = parser.parse_args()

	if args.generate is not None:
		gen = generator.Generator(args.generate)
		text = gen.generate_paragraphs(args.size, args.paragraphs)
		print(text)

	elif args.train is not None:
		trn = trainer.Trainer(args.train, args.ngram)
		trn.train()