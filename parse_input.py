#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Command line interface for parsing varipus content with parsers in src/parsers


import argparse
import src.parsers.text_parser
from src.parsers.tweet_parser.parser import TwitterParser
import src.parsers.steam_parser
import src.parsers.poem_parser


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Parses various input to training data for text_generator.py")
	parser.add_argument("--text", help="Text parser for .txt folders", metavar="folder")
	#parser.add_argument("--twitter", nargs=2, help="Tweet parser for a Twitter handle timeline", metavar=("handle", "command"))
	parser.add_argument("--steam", help="Steam game description parser", metavar="sample_size", type=int, default=50)
	parser.add_argument("--poem", help="Poem parser for https://allpoetry.com/classics/famous_poems", action="store_true")

	subparsers = parser.add_subparsers(description="Twitter sub parser", dest="twitter")
	parser_twitter = subparsers.add_parser("twitter", help="foo")

	parser_twitter.add_argument("handle", help="Twitter handle")
	parser_twitter.add_argument("--fetch", action="store_true", help="Fetch new tweets since previous run")
	parser_twitter.add_argument("--parse", nargs=2, metavar=("date", "number of months"), help="Parse stored tweets as training data")

	args = parser.parse_args()
	print(args)

	if args.text:
		parser = src.parsers.text_parser.TextParser(args.text)
		parser.run()

	elif args.twitter:
		parser = TwitterParser(args.handle)

		if args.fetch:
			parser.fetch_new_tweets()

		elif args.parse:
			start_month = args.parse[0]
			number_of_months = int(args.parse[1])
			res = parser.save_training_data(start_month, number_of_months)
			print(res)



	elif args.steam:
		parser = src.parsers.steam_parser.SteamParser(args.steam)
		parser.run()

	elif args.poem:
		parser = src.parsers.poem_parser.PoemParser()
		parser.run()