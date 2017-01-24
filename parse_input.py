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
import os

from bs4 import BeautifulSoup



# Connect to Twitter for fetching timelines, requires valid keys in keys.json.

with open("./keys.json") as f:
	keys = json.load(f)

API_KEY = keys["TWITTER_API_KEY"]
API_SECRET = keys["TWITTER_API_SECRET"]
OAUTH_TOKEN = keys["TWITTER_OAUTH_TOKEN"]
OAUTH_SECRET = keys["TWITTER_OAUTH_SECRET"]

# Check if valid keys were found.
if API_KEY == API_SECRET:
	print "WARNING: couldn't find proper Twitter access tokens in keys.json. Fetching timelines disabled."


twitter = twython.Twython(API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_SECRET) # this will pass even if tokens are empty, fetching timelines will throw a TwythonAuthError 


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
	with codecs.open(output, mode="w", encoding="utf8") as f:
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
	output = "data/training/" + os.path.basename(folder) + ".txt"
	parse_files(files, output)

	return output


#####################
# Twitter timelines #
#####################

def get_recent_timeline(screen_name, since_id, n):
	"""Read n most recent tweets from the specified timeline. Only read one page.
	Args:
		screen_name (string): the Twitter account whose timeline to read
		since_id (int): read only tweets newer than this (higher id)
		n (int): how many tweets to read
	Return:
		the list of tweets returned by Twitter
	"""
	tweets = twitter.get_user_timeline(screen_name = screen_name, exclude_replies = True, include_rts = False, since_id = since_id, count = n)
	#tweets = twitter.cursor(twitter.get_user_timeline, screen_name = screen_name, exclude_replies = True, count = n)

	return tweets


def get_timeline_history(screen_name, n):
	"""Fetch the n most recent pages from the given user's timeline.
	Note: Twitter API only returns at most 3 200 tweets.
	Args:
		screen_name (string): a Twitter username
		n (int): number of pages of tweets to read
	Return:
		a list of tweet objects as returned by Twitter.
	"""
	print "Fetching tweets..."
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


def dump_tweets(tweets):
	"""Read a Twitter timeline and store all tweets to a text file to be used as
	training data for text_generator.py.
	Arg:
		tweets (list): a list of tweets as returned by the API
	"""
	#tweets = get_timeline_history(screen_name, n)
	texts = [filter_tweet(t) for t in tweets]  # drop urls and mentions
	texts = [t for t in texts if len(t.split()) > 3]  # drop short tweets
	n = len(texts)
	texts = " ".join(texts)

	# Date range of the tweets
	start = tweets[-1]["created_at"]  # eg. Tue Mar 01 19:34:01 +0000 2016
	end = tweets[0]["created_at"]

	# Parse as month day year
	start = [ start.split()[i] for i in (1, 2, 5) ]
	start = " ".join(start)
	end = [ end.split()[i] for i in (1, 2, 5) ]
	end = " ".join(end)
	
	# Store under its own folder as a txt file,
	# create a new directory if one doesn't exist already
	name = tweets[0]["user"]["screen_name"]
	path = "data/training/{0}".format(name)
	if not os.path.isdir(path):
		os.mkdir(path)
		print "Created a new directory", path

	# Store the tweets.
	file = "data/training/{0}/{0}.txt".format(name)
	with codecs.open(file, mode="a", encoding="utf8") as f:
		f.write(texts)

	# Store tweet id of the latest tweet to separate file
	file = "data/training/{}/timeline.dat".format(name)
	with open(file, "w") as f:
		f.write("This file contains the id of the latest tweet fetched from Twitter.\n{}".format(tweets[0]["id"]))

	print "Created a dump of {} tweets between {} and {} at {}.".format(n, start, end, file)


###################
# Washington Post #
###################

def get_article_text(url):
	"""Parse the url of an article to a text with links removed."""
	r = requests.get(url)
	soup = BeautifulSoup(r.text, "lxml")
	text = soup.find("article").text

	# Strip any part after "Read more"
	# Note: the actual phrase may be "Read more here", "Read more on this subject", etc.
	idx = text.find("Read more")
	text = text[:idx]

	# Store to file
	title = soup.title.text.rstrip(" - The Washington Post").rstrip(".")
	path = "data/training/washington_post/" + title + ".txt"
	with codecs.open(path, mode="w", encoding="utf8") as f:
		f.write(text)


def parse_headlines():
	"""Parse a frontpage of articles to separate files containing article texts."""
	r = requests.get("https://www.washingtonpost.com/opinions/the-posts-view")
	soup = BeautifulSoup(r.text, "lxml")
	
	print "Parsing article urls..."
	# Select elements with a href attribute under divs with class story-headline
	url_tags = soup.select("div.story-headline [href]")
	print "Found {} articles".format(len(url_tags))


	for tag in url_tags:
		print tag.text
		get_article_text(tag.get("href"))


#########
# Poems #
#########

def get_poem_text(url):
	"""Parse a poem from the specified url and store it to a file under data/training/poems."""
	r = requests.get(url)
	soup = BeautifulSoup(r.text, "lxml")
	try:
		text = soup.select("div.poem_body")[0].text
	except IndexError:
		return

	title = soup.title.text.split(" - ")[0]  # poem title with author
	path = "data/training/poems/" + title + ".txt"
	with codecs.open(path, mode="w", encoding="utf8") as f:
		f.write(text)


def parse_poem_urls():
	"""Ad hoc function to read urls from the list of 500 poems at https://allpoetry.com/classics/famous_poems?page=1.
	Note: unregistered users can only read the first 10 pages ~ 270 poems.
	"""
	# Iterate over the 10 pages in the list of poems.
	for i in range(1, 11):
		page = "?page="+str(i)
		r = requests.get("https://allpoetry.com/classics/famous_poems" + page)
		soup = BeautifulSoup(r.text, "lxml")

		# Get div tags from this page
		url_tags = soup.select("div.heading [href]")

		# Get the url of the poem and pass to get_poem_text() for 
		for tag in url_tags:
			title = tag.text
			print title

			poem_url = "https://allpoetry.com" + tag.get("href")
			get_poem_text(poem_url)





if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Parses various input to training data for text_generator.py")
	parser.add_argument("--parse-tweets", help="Store new tweets from the specified Twitter screen name to data/training/screen_name.", metavar="screen_name")
	parser.add_argument("--parse-wp", help="Store latest Washington Post editorials to data/training/washington_post.", action="store_true")

	args = parser.parse_args()
	#print args


	if args.parse_tweets:
		# Check whether there already is a folder for this username and either append
		# the most recent tweets to it, or initialize a new file with the last 50 pages of tweet results.
		screen_name = args.parse_tweets.lstrip("@")
		path = "data/training/" + screen_name
		if not os.path.isdir(path):
			tweets = get_timeline_history(screen_name, 50)
			dump_tweets(tweets)

		else:
			# Read the id of the most recent tweets fetched...
			with open(path + "/timeline.dat") as f:
				lines = f.readlines()
				id_ = lines[1]

			# ...fetch tweets newer than the id
			tweets = get_recent_timeline(screen_name, id_, 200)
			dump_tweets(tweets)


	elif args.parse_wp:
		parse_headlines()