#!/usr/bin/env python3

# Parses tweets from a single Twitter handle.

import os
import json
import datetime
import argparse
import logging

import twython


BASE = os.path.dirname(os.path.abspath(__file__))
KEYFILE = os.path.join(BASE, "..", "twitter_keys.json")
METADATA_FILE = os.path.join(BASE, "tweet_metadata.json")

with open(KEYFILE) as f:
	keys = json.load(f)
	APP_KEY = keys["API_KEY"]
	APP_SECRET = keys["API_SECRET"]
	OAUTH_TOKEN = keys["OAUTH_TOKEN"]
	OAUTH_TOKEN_SECRET = keys["OAUTH_SECRET"]

	twitter = twython.Twython(APP_KEY, APP_SECRET,
					OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def _get_tweet_metadata():
	with open(METADATA_FILE) as f:
		return json.load(f)

def _write_tweet_metadata(metadata):
	with open(METADATA_FILE, "w") as f:
		json.dump(metadata, f, indent=2)



class TwitterParser():

	def __init__(self, handle):
		self.handle = handle

	def read_timeline_since(self, since_id):
		"""Fetch (most recent) tweets from user. 
		Args:
			screen_name (str): Twitter handle to search
			since_id (int): tweet id of earliest tweet to start searching.
		Return:
			The response from Twitter
		"""

		# fetch the first page with maximum number of tweets
		response = twitter.get_user_timeline(
			screen_name=self.handle,
			exclude_replies=True,
			include_rts=False,
			count=50,
			trim_user=True,
			tweet_mode="extended", # undocumented parameter to fetch full tweet text,
			#max_id=max_tweet_id,
			since_id=since_id
		)
		return response

	def write_tweets(self, tweets):
		today = datetime.datetime.today()

		storage_base = os.path.join(BASE, self.handle, today.strftime("%Y-%m"))
		path = os.path.join(storage_base, today.strftime("%Y-%m-%d") + ".json")

		if not os.path.isdir(storage_base):
			os.makedirs(storage_base)

		with open(path, "w") as f:
			json.dump(tweets, f)

	def parse_for_text(self, tweets):
		filtered = []
		for tweet in tweets:
			split = tweet["full_text"].split()
			text = " ".join( [word for word in split if not any(item in word for item in ("http://", "https://", "@", "#"))] )
			text = text.replace("&amp;", "&")

			filtered.append(text)
		
		return filtered


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Fetches users latest tweets from Twitter")
	parser.add_argument("handle", help="Twitter handle")
	args = parser.parse_args()

	parser = TwitterParser(args.handle)

	tweet_metadata = _get_tweet_metadata()
	latest_tweet_id = tweet_metadata[args.handle]

	response = parser.read_timeline_since(latest_tweet_id)
	tweet_metadata[args.handle] = response[0]["id"]  # update latest tweet id

	parser.write_tweets(response)
	_write_tweet_metadata(tweet_metadata)
