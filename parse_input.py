#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Command line interface for parsing varipus content with parsers in src/parsers


import argparse
import src.parsers.text_parser
import src.parsers.tweet_parser
import src.parsers.steam_parser
import src.parsers.poem_parser


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Parses various input to training data for text_generator.py")
	parser.add_argument("--text", help="Text parser for .txt folders", metavar="folder")
	parser.add_argument("--twitter", help="Tweet parser for a Twitter handle timeline", metavar="handle")
	parser.add_argument("--steam", help="Steam game description parser", metavar="sample_size", type=int, default=50)
	parser.add_argument("--poem", help="Poem parser for https://allpoetry.com/classics/famous_poems", action="store_true")
	args = parser.parse_args()


	if args.text:
		parser = src.parsers.text_parser.TextParser(args.text)
		parser.run()

	elif args.twitter:
		parser = src.parsers.tweet_parser.TweetParser(args.twitter)
		parser.run()

	elif args.steam:
		parser = src.parsers.steam_parser.SteamParser(args.steam)
		parser.run()

	elif args.poem:
		parser = src.parsers.poem_parser.PoemParser()
		parser.run()