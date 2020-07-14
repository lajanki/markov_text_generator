#!/usr/bin/env python3

# Parses tweets from a single Twitter handle.

import os
import json
import sys
import datetime
import argparse
import logging
import glob

from dateutil.relativedelta import relativedelta

import twython
from dotenv import load_dotenv




RELATIVE_BASE = os.path.dirname(os.path.abspath(__file__))
METADATA_FILE = os.path.join(RELATIVE_BASE, "tweet_metadata.json")
LOG_FILE = os.path.join(RELATIVE_BASE, "parser.log")
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


def _get_tweet_metadata():
	with open(METADATA_FILE) as f:
		return json.load(f)

def _write_tweet_metadata(metadata):
	with open(METADATA_FILE, "w") as f:
		json.dump(metadata, f, indent=2)

def filter_tweet(tweet_text):
	"""Filter a tweet text by removing urls, mentions, etc."""
	split = tweet_text.split()
	text = " ".join( [word for word in split if not any(item in word for item in ("http://", "https://", "@", "#"))] )
	text = text.replace("&amp;", "&")
	return text


class TwitterParser():

	def __init__(self, handle):
		self.handle = handle

	def fetch_new_tweets(self):
		"""Look for new tweets since previous run and save the raw json responses
		to as a date stamped file in the Twitter handle directory.
		""" 
		tweet_metadata = _get_tweet_metadata()
		latest_tweet = tweet_metadata[self.handle]

		logging.info("Fetching tweets since %s", latest_tweet["created_at"])
		response = self.read_timeline_since(latest_tweet["id"])
		tweet_metadata[self.handle] = response[0]  # update tweet metadata with latest tweet received

		self.write_tweets(response)
		_write_tweet_metadata(tweet_metadata)

	def parse(self, start_date, months):
		"""Parse selected saved tweets responses into a single string to be used for training.
		Args:
			start_date (str): folder name (ie. month in YYYY-MM) to start parsing from.
				Alternatively the literal string 'previous_month' to start from
				previous month as determined from current execution date.
			month (int): number of months (ie. folders) to parse
		Return:
			Contents of the parsed tweets as a string.
		"""
		parsed_texts = []
		if start_date == "previous_month":
			start_date = (datetime.datetime.today() - relativedelta(months=1)).strftime("%Y-%m")

		for i in range(months):
			d = datetime.datetime.strptime(start_date, "%Y-%m") - relativedelta(months=i)
	
			tweet_folder = os.path.join(RELATIVE_BASE, self.handle, d.strftime("%Y-%m"))
			for tweet_file in glob.glob(tweet_folder + "/*.json"):

				with open(tweet_file) as f:
					tweet_data = json.load(f)
				
				tweet_texts = [filter_tweet(t["full_text"]) for t in tweet_data]
				parsed_texts.extend(tweet_texts)
		
		return "\n".join(parsed_texts)

	def save(self, content):
		"""Save parsed training data to data/training."""
		output = os.path.join(RELATIVE_BASE, "..", "data", "training", "{}.txt".format(self.handle))
		with open(output, "w") as f:
			f.write(content)

		logging.info("Created a new parsed tweet dump at %s", os.path.abspath(output))

	def read_timeline_since(self, since_id):
		"""Fetch (most recent) tweets from user. 
		Args:
			screen_name (str): Twitter handle to search
			since_id (int): tweet id of earliest tweet to start searching.
		Return:
			The response from Twitter
		"""

		# fetch the first page with maximum number of tweets
		response = client.get_user_timeline(
			screen_name=self.handle,
			exclude_replies=True,
			include_rts=False,
			count=50,
			trim_user=True,
			tweet_mode="extended", # undocumented parameter to fetch full tweet text,
			#max_id=1,
			since_id=since_id
		)
		if not response:
			logging.warn("Empty response received, exiting")
			raise RuntimeError("Empty response received, aborting")

		elif len(response) == 1:
			logging.warn("Only 1 item in the response:")
			logging.warn(response[0])
			raise RuntimeError("Limited response, aborting")

		else:
			last = response[0]["created_at"]
			first = response[-1]["created_at"]
			logging.info("Fetched %d tweets between %s and %s", len(response), first, last)

		return response

	def write_tweets(self, tweets):
		today = datetime.datetime.today()

		storage_base = os.path.join(RELATIVE_BASE, self.handle, today.strftime("%Y-%m"))
		path = os.path.join(storage_base, today.strftime("%Y-%m-%d") + ".json")

		# Extend with existing file (if exists)
		if os.path.isfile(path):
			logging.info("Appending to existing file %s", path)
			with open(path) as f:
				tweets.extend(json.load(f))

		if not os.path.isdir(storage_base):
			os.makedirs(storage_base)

		with open(path, "w") as f:
			json.dump(tweets, f)
