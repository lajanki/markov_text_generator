#!/usr/bin/env python3

import codecs
import os
import json

import twython
from src import utils



class TweetParser:
	"""Parse Twitter timelines to a single .txt file. Twitter API supports fetching upto 3 200 tweets,
	in pages of 200 tweets.
	Timeline can either be specified as the last 3 200 tweets or starting from a specified tweet id.
	"""

	def __init__(self, screen_name):
		"""Creates a parser for a specific Twitter screen_name (ie. @handle)"""
		self.twitter = self.build()
		self.screen_name = screen_name
		self.tweets = []

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
			screen_name = self.screen_name,
			exclude_replies = True,
			include_rts = False,
			count = 200,
			since_id=1
		)
		id_ = page[-1]["id"] # id of the earliest tweet
		tweets.extend(page)  # page is a list of tweets

		# Read the next n-1 pages by setting the max_id parameter to the earliest id of the previous page
		for _ in range(pages-1):
			page = self.twitter.get_user_timeline(
				screen_name = self.screen_name,
				exclude_replies = True,
				include_rts = False,
				count = 200,
				max_id = id_
			)
			# Return early if there are no more pages.
			if not page:
				self.tweets = tweets # set the tweets attribute before returning
				return

			id_ = page[-1]["id"]
			tweets.extend(page)

		self.tweets = tweets

	def dump_tweets(self):
		"""Join a list of tweets to a single text file as input for the text generator.
		Arg:
			tweets (list): a list of tweet objects as returned by the API
		"""
		 # drop urls and mentions
		texts = [self.filter_tweet(t) for t in self.tweets]
		texts = " ".join(texts)

		# Determine the date range of the tweets
		start = self.tweets[-1]["created_at"]  # eg. Tue Mar 01 19:34:01 +0000 2016
		end = self.tweets[0]["created_at"]

		# Parse as month day year
		start = [ start.split()[i] for i in (1, 2, 5) ]
		start = " ".join(start)
		end = [ end.split()[i] for i in (1, 2, 5) ]
		end = " ".join(end)

		# Store the tweets in /training directory under the screen_name.
		filename = self.screen_name + ".txt"
		output = os.path.join(utils.BASE, "data", "training", filename)  
		with codecs.open(output, mode="w", encoding="utf8") as f:
			f.write(texts)

		# Print an info message based on wheter tweets were added to an existing file or a new one was created.
		msg = "Wrote {} tweets between {} and {} to {}".format(len(texts), start, end, filename)
		print(msg)

	def filter_tweet(self, tweet):
		"""Filter a single tweet to better suit training data:
		Remove urls, user mentions and hashtags.
	 	"""
		split = tweet["text"].split()
		text = " ".join( [word for word in split if not any(item in word for item in ("http://", "https://", "@", "#"))] )
		text = text.replace("&amp;", "&")
		return text