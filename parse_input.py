#!/bin/python
# -*- coding: utf-8 -*-

"""
Parse input from various sources to the format used as training data for a random text generator.

3.1.2017
"""



import random
import sqlite3
import codecs
import argparse
import json
import glob
import twython
import requests
import os.path

from bs4 import BeautifulSoup


# Read Twitter API keys from file
with open("./keys.json") as f:
	keys = json.load(f)

API_KEY = keys["TWITTER_API_KEY"]
API_SECRET = keys["TWITTER_API_SECRET"]
OAUTH_TOKEN = keys["TWITTER_OAUTH_TOKEN"]
OAUTH_SECRET = keys["TWITTER_OAUTH_SECRET"]

twitter = twython.Twython(API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_SECRET)




##############
# Text files #
##############

def parse_files(files, output):
	"""Parses a list of files to a single training data file.
	Args:
		files (list): a list of filepaths of files to process
		output (string): the file where to store the output
	"""
	words = []
	for file in files:
		with codecs.open(file, encoding="utf8") as f:
			word_list = f.read().split()  # words of the file in a list
			words.extend(word_list)

	text = " ".join(words)
	with codecs.open(output, "w", "utf8") as f:
		f.write(text)

	print "Created a dump at", output


def parse_folder(folder):
	"""A wrapper to parse_files, reads text files within a folder as a list and passes it
	to parse_files()
	Arg:
		folder (string): the folder to parse
	Return:
		path to where the joined data was stored
	"""
	files = glob.glob(folder + "/*.txt")
	output = "training-data/" + os.path.basename(folder) + ".txt"
	parse_files(files, output)

	return output


#####################
# Twitter timelines #
#####################

def get_recent_timeline(screen_name, n):
	"""Read n most recent tweets from given account. Fetches at most 200 tweets."""
	tweets = twitter.get_user_timeline(screen_name = screen_name, exclude_replies = True, include_rts = False, count = n)
	#tweets = twitter.cursor(twitter.get_user_timeline, screen_name = screen_name, exclude_replies = True, count = n)
	texts = [t["text"] for t in tweets]

	return texts


def get_timeline_history(screen_name, n):
	"""Fetch the n most recent pages from the given user's timeline.
	Note: Twitter API only returns at most 3 200 tweets.
	Args:
		screen_name (string): a Twitter username
		n (int): number of pages of tweets to read
	Return:
		a list of tweet objects as returned by Twitter.
	"""
	page = twitter.get_user_timeline(screen_name = screen_name, exclude_replies = True, include_rts = False, count = 200)  # first page with maximum number of tweets
	id_ = page[-1]["id"] # id of the last tweets in the results
	tweets = page

	# Read the next n-1 pages by setting the max_id to the lowest id in the previous page
	for i in range(n-1):
		page = twitter.get_user_timeline(screen_name = screen_name, exclude_replies = True, include_rts = False, count = 200, max_id = id_)
		# Return early if there are no more pages.
		if not page:
			return tweets

		id_ = page[-1]["id"]
		tweets.extend(page)

	return tweets


def filter_tweet(tweet):
	"""Filter a single tweet to better suit training data:
	Remove urls and mentions.
 	"""
	split = tweet["text"].split()
	text = " ".join( [word for word in split if not any(item in word for item in ["http://", "https://", "@"])] )
	text = text.replace("&amp;", "&")
	return text


def dump_tweets(screen_name, n=15):
	"""Read a Twitter timeline and store all tweets to a text file to be used as
	training data for text_generator.py.
	Args:
		screen_name (string): a Twitter user name
		n (int): number of pages of tweets to read
	"""
	tweets = get_timeline_history(screen_name, n)
	texts = [filter_tweet(t) for t in tweets]  # drop urls and mentions
	texts = [t for t in texts if len(t.split()) > 3]  # drop short tweets
	n = len(texts)
	texts = " ".join(texts)

	# Date range of the tweets
	start = tweets[-1]["created_at"]  # eg. Tue Mar 01 19:34:01 +0000 2016
	end = tweets[0]["created_at"]

	# Parse as month day year'
	start = [ start.split()[i] for i in (1, 2, 5) ]
	start = " ".join(start)
	end = [ end.split()[i] for i in (1, 2, 5) ]
	end = " ".join(end)
	
	file = "training-data/" + screen_name.lstrip("@") + ".txt"
	with codecs.open(file, "w", "utf8") as f:
		f.write(texts)
	print "Created a dump of {} tweets between {} and {} at {}.".format(n, start, end, file)


##############################
# Washington Post Editorials #
##############################

def get_article_text(url):
	"""Parse the url of an article to a text with links removed."""
	r = requests.get(url)
	soup = BeautifulSoup(r.text, "lxml")
	text = soup.find("article").text

	# Strip any part after "Read more here:"
	idx = text.find("Read more here:")
	text = text[:idx]

	# Store to file
	title = soup.title.text.rstrip(" - The Washington Post").rstrip(".")
	path = "training-data/original/washington_post/" + title + ".txt"
	with codecs.open(path, "w", "utf8") as f:
		f.write(text)


def parse_headlines():
	"""Parse a frontpage of articles to separate files containing article texts."""
	r = requests.get("https://www.washingtonpost.com/opinions/the-posts-view/?utm_term=.323a5c68996a")
	soup = BeautifulSoup(r.text, "lxml")
	
	print "Parsing article urls..."
	# Select elements with a href attribute under divs with class story-headline
	url_tags = soup.select("div.story-headline [href]")
	print "Found {} articles".format(len(url_tags))


	for tag in url_tags:
		print tag.text
		get_article_text(tag.get("href"))


