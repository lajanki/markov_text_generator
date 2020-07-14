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
	parser = argparse.ArgumentParser(description="Generates Markov chain based random text based on input text")
	subparsers = parser.add_subparsers(description="Training and generator sub commands", dest="command")

	parser_trainer = subparsers.add_parser("train", help="Train a model using input plain text file from data/training")
	parser_trainer.add_argument("training_file", help="Input text file from data/training to use", metavar="training_file", choices=training_files)
	parser_trainer.add_argument("ngram", help="ngram size. Defaults to 3", nargs="?", metavar="n", type=int, default=3)

	parser_generator = subparsers.add_parser("generate", help="Generate text using a trained model in data/cache")
	parser_generator.add_argument("model", help="Model in data/cache to use", metavar="model", choices=models)
	parser_generator.add_argument("nword", help="Approximate number of words to generate for each paragraph. Defaults to 25", nargs="?", default=25, type=int)
	parser_generator.add_argument("paragraphs", help="Number of paragraphs to generate. Defaults to 1", nargs="?", default=1, type=int, metavar="paragraphs")
	args = parser.parse_args()

	if args.command == "train":
		trn = trainer.Trainer(args.training_file, args.ngram)
		trn.train()

	elif args.command == "generate":
		gen = generator.Generator(args.model)
		text = gen.generate_paragraphs(args.nword, args.paragraphs)
		print(text)