#!/usr/bin/env python3

# Parses tweets from a single Twitter handle.

import os
import json

import twython
from src.parsers import base_parser
from src import utils



class TweetParser(base_parser.BaseParser):
	"""Parse Twitter timelines to a single .txt file. Twitter API supports fetching upto 3 200 tweets,
	in pages of 200 tweets.
	Timeline can either be specified as the last 3 200 tweets or starting from a specified tweet id.
	"""

	def __init__(self, screen_name):
		"""Creates a parser for a specific Twitter screen_name (ie. @handle)"""
		self.twitter = self.build()
		self.screen_name = screen_name
		super().__init__(screen_name + ".txt")

	def build(self):
		"""Build a Twitter object."""
		with open(os.path.join(utils.BASE, "twitter_keys.json")) as f:
			keys = json.load(f)

			API_KEY = keys["API_KEY"]
			API_SECRET = keys["API_SECRET"]
			OAUTH_TOKEN = keys["OAUTH_TOKEN"]
			OAUTH_SECRET = keys["OAUTH_SECRET"]

		twitter = twython.Twython(API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_SECRET)
		return twitter

	def get_timeline_history(self, pages=16):
		"""Fetch the n most recent pages from the given user's timeline.
		Note: Twitter API only returns upto 3 200 tweets, each page can contain
		upto 200 tweets.
		Args:
			pages (int): number of pages of tweets to read, defaults to the maximum of 16 (16 * 200 = 3 200)
		Return:
			a list of tweet objects as returned by Twitter.
		"""
		print("Fetching tweets for {}...".format(self.screen_name))
		tweets = []
		# fetch the first page with maximum number of tweets
		page = self.twitter.get_user_timeline(
			screen_name=self.screen_name,
			exclude_replies=True,
			include_rts=False,
			count=200,
			tweet_mode="extended",
			since_id=1
		)
		id_ = page[-1]["id"] # id of the earliest tweet
		tweets.extend(page)  # page is a list of tweets

		# Read the next n-1 pages by setting the max_id parameter to the earliest id of the previous page
		for _ in range(pages-1):
			page = self.twitter.get_user_timeline(
				screen_name=self.screen_name,
				exclude_replies=True,
				include_rts=False,
				count=200,
				tweet_mode="extended",
				max_id=id_
			)
			# Return early if there are no more pages.
			if not page:
				return tweets

			id_ = page[-1]["id"]
			tweets.extend(page)

		return tweets

	def parse(self):
		"""Join a list of tweets to a single text file as input for the text generator."""
		tweets = self.get_timeline_history()
		 # drop urls and mentions
		texts = [self.filter_tweet(t) for t in tweets]
		texts = " ".join(texts)

		# Determine the date range of the tweets
		start = tweets[-1]["created_at"]  # eg. Tue Mar 01 19:34:01 +0000 2016
		end = tweets[0]["created_at"]

		# Parse as month day year
		start = [ start.split()[i] for i in (1, 2, 5) ]
		start = " ".join(start)
		end = [ end.split()[i] for i in (1, 2, 5) ]
		end = " ".join(end)

		self.content = texts
		msg = "Parsed {} tweets between {} and {}".format(len(texts), start, end)
		print(msg)

	def filter_tweet(self, tweet):
		"""Filter a single tweet to better suit training data:
		Remove urls, user mentions and hashtags.
	 	"""
		split = tweet["full_text"].split()
		text = " ".join( [word for word in split if not any(item in word for item in ("http://", "https://", "@", "#"))] )
		text = text.replace("&amp;", "&")
		return text