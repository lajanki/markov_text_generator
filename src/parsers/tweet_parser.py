#!/usr/bin/env python3

import codecs
import os
import json

import twython
from src import utils


class TwitterParser:
	"""Parse Twitter timelines to a single .txt file. Twitter API supports fetching upto 3 200 tweets,
	in pages of 200 tweets.
	Timeline can either be specified as the last 3 200 tweets or starting from a specified tweet id.
	"""

	def __init__(self, screen_name):
		"""Creates a parser for a specific Twitter screen_name (ie. @handle)"""
		self.twitter = self.build()
		self.screen_name = screen_name
		self.path = os.path.join(utils.BASE, "data", "training", screen_name) # path to the data folder

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

	def get_timeline_history(self, n, since_id = 1):
		"""Fetch the n most recent pages from the given user's timeline.
		Note: Twitter API only returns upto 3 200 tweets, each page can contain
		upto 200 tweets.
		Arg:
			n (int): number of pages of tweets to read
			since_id (int): a tweet id, only return tweets newer than this (higher id). By default, there
				is no id filtering.
		Return:
			a list of tweet objects as returned by Twitter.
		"""
		print("Fetching tweets for {}...".format(self.screen_name))
		# fetch the first page with maximum number of tweets
		page = self.twitter.get_user_timeline(
			screen_name = self.screen_name,
			exclude_replies = True,
			include_rts = False,
			count = 200,
			since_id = since_id
		)
		id_ = page[-1]["id"] # id of the last tweets in the results
		tweets = page

		# Read the next n-1 pages by setting the max_id parameter to the lowest id in the previous page
		for _ in range(n-1):
			page = self.twitter.get_user_timeline(
				screen_name = self.screen_name,
				exclude_replies = True,
				include_rts = False,
				count = 200,
				max_id = id_,
				since_id = since_id
			)
			# Return early if there are no more pages.
			if not page:
				return tweets

			id_ = page[-1]["id"]
			tweets.extend(page)

		return tweets

	def dump_tweets(self, tweets):
		"""Join a list of tweets to a single text file as input for the text generator.
		Arg:
			tweets (list): a list of tweets as returned by the API
		"""
		texts = [self.filter_tweet(t) for t in tweets]  # drop urls and mentions
		#texts = [t for t in texts if len(t.split()) > 3]  # drop short tweets
		n = len(texts)
		texts = " ".join(texts)

		# Determine the date range of the tweets
		start = tweets[-1]["created_at"]  # eg. Tue Mar 01 19:34:01 +0000 2016
		end = tweets[0]["created_at"]

		# Parse as month day year
		start = [ start.split()[i] for i in (1, 2, 5) ]
		start = " ".join(start)
		end = [ end.split()[i] for i in (1, 2, 5) ]
		end = " ".join(end)

		# Store under its own folder as a txt file,
		# create a new directory if one doesn't exist already
		new_path = False
		if not os.path.isdir(self.basename):
			os.mkdir(path)
			new_path = True

		# Store the tweets.
		filename = self.basename + "/" + self.screen_name + ".txt"
		with codecs.open(filename, mode="a", encoding="utf8") as f: # append in case the file already exists
			f.write(texts)

		# Store tweet id of the latest tweet to separate file
		timeline_file = self.basename + "/timeline.dat"
		with open(timeline_file, "w") as f:
			f.write("This file contains the id of the latest tweet fetched from Twitter.\n{}".format(tweets[0]["id"]))

		# Print an info message based on wheter tweets were added to an existing file or a new one was created.
		msg = "Added {} tweets between {} and {} to {}".format(n, start, end, filename)
		if new_path:
			msg = "Created a dump of {} tweets between {} and {} at {}.".format(n, start, end, filename)

		print(msg)

	def get_most_recent_tweet_id(self):
		"""Read the tweet id of the most recent tweet fetched for this user from the
		corresponding metadata file. Returns None if the file does not exist.
		"""
		timeline_file = os.path.join(self.path, "timeline.dat")
		try:
			with open(timeline_file, "r") as f:
				lines = f.readlines()
				print("Existing tweets detected in {}".format(timeline_file))
				return lines[1]  # the id is the second row in the file
		except IOError as e:
			return 1  # an id of 1 will result in no id filtering

	def filter_tweet(self, tweet):
		"""Filter a single tweet to better suit training data:
		Remove urls, user mentions and hashtags.
	 	"""
		split = tweet["text"].split()
		text = " ".join( [word for word in split if not any(item in word for item in ("http://", "https://", "@", "#"))] )
		text = text.replace("&amp;", "&")
		return text