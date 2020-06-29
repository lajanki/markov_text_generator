#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Tweets generated texts
# usage: run from main folder as 
# 	python -m twitter.bot --trumpet


import os
import argparse
import random
import logging

import twython
from dotenv import load_dotenv

from src import generator


RELATIVE_BASE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(RELATIVE_BASE, "tweets.log")
TWITTER_KEY_FILE = os.path.join(RELATIVE_BASE, "twitter_keys.env")

logging.basicConfig(
	handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv(dotenv_path=TWITTER_KEY_FILE)

APP_KEY = os.environ["API_KEY"]
APP_SECRET = os.environ["API_SECRET"]
OAUTH_TOKEN = os.environ["OAUTH_TOKEN"]
OAUTH_TOKEN_SECRET = os.environ["OAUTH_SECRET"]

client = twython.Twython(APP_KEY, APP_SECRET,
	OAUTH_TOKEN, OAUTH_TOKEN_SECRET)


def tweet_trumpet():
	"""Generate and Tweet a realDonaldTrump text."""
	gen = generator.Generator("@realDonaldTrump.dat")
	text = gen.generate_paragraphs(25, 1)

	# replace any user mentions and urls
	text = text.replace("@", "")
	logging.info(text)
	#client.update_status(status=text)

def tweet_poem():
	"""Generate and Tweet a poem."""
	gen = generator.Generator("poems.dat")
	paragrags = random.choice([2,3,4])
	text = gen.generate_paragraphs(25, paragrags)

	#client.update_status(status=text)
	print(text)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Tweets randomized texts.")
	parser.add_argument("--trumpet", help="Tweet a trumpet", action="store_true")
	parser.add_argument("--poem", help="Tweet a poem", action="store_true")
	args = parser.parse_args()

	if args.trumpet:
		tweet_trumpet()

	elif args.poem:
		tweet_poem()
