#!/bin/python
# -*- coding: utf-8 -*-

"""
A collection of various parser for processing various text sources as
input for the text generator.
Includes parsers for .txt files, Twitter timelines, Steam game descriptions
and various websites


16.8.2017
"""



import random
import codecs
import argparse
import json
import glob
import twython
import requests
import os

from bs4 import BeautifulSoup



class TextParser:
	"""Parse folders containing .txt files."""

	def __init__(self, path):
		self.path = path.rstrip("/")  # strip any trailing slash so that os.path.basename reads the proper folder name

	def parse_folder(self):
		"""A wrapper to parse_files, reads text files within a folder as a list and passes it
		to parse_files()
		Return:
			path to where the joined data was stored
		"""
		files = glob.glob(self.path + "/*.txt")
		combined_words = []
		for file in files:
			with codecs.open(file, encoding="utf8") as f:
				word_list = f.read().split()  # words of the file as a list
				combined_words.extend(word_list)

		text = " ".join(combined_words)
		return text

	def dump_text(self, text):
		"""Store text to a file."""
		output = "data/training/" + os.path.basename(self.path) + ".txt"
		with codecs.open(output, mode="w", encoding="utf8") as f:
			f.write(text)

		print "Created a dump at", output


class TwitterParser:
	"""Parse Twitter timelines. Either from the last n pages or starting from a specified
	tweet id.
	"""
	#Create a class level Twitter connection.
	with open("/home/pi/python/text_generator/keys.json") as f:
		keys = json.load(f)

	API_KEY = keys["API_KEY"]
	API_SECRET = keys["API_SECRET"]
	OAUTH_TOKEN = keys["OAUTH_TOKEN"]
	OAUTH_SECRET = keys["OAUTH_SECRET"]
	twitter = twython.Twython(API_KEY, API_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

	def __init__(self, screen_name):
		"""Creates a new parser for each Twitter screen name."""
		self.screen_name = screen_name
		self.basename = "data/training/{}".format(self.screen_name)

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
		print "Fetching tweets for {}...".format(self.screen_name)
		# fetch the first page with maximum number of tweets
		page = TwitterParser.twitter.get_user_timeline(
			screen_name = self.screen_name,
			exclude_replies = True,
			include_rts = False,
			count = 200,
			since_id = since_id
		)
		id_ = page[-1]["id"] # id of the last tweets in the results
		tweets = page

		# Read the next n-1 pages by setting the max_id parameter to the lowest id in the previous page
		for i in range(n-1):
			page = TwitterParser.twitter.get_user_timeline(
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

		print msg

	def get_most_recent_tweet_id(self):
		"""Read the tweet id of the most recent tweet fetched for this user from the
		corresponding metadata file. Returns None if the file does not exist.
		"""
		timeline_file = self.basename + "/timeline.dat"
		try:
			with open(timeline_file, "r") as f:
				lines = f.readlines()
				print "Existing tweets detected in {}".format(timeline_file)
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


class WPParser:
	"""Parse editorials from https://www.washingtonpost.com/opinions/the-posts-view."""

	def __init__(self):
		self.current_article = None  # the most recent article title parsed from the website

	def parse_headlines(self):
		"""Parse the editorial frontpage for articles to dump to a folder"""
		r = requests.get("https://www.washingtonpost.com/opinions/the-posts-view")
		soup = BeautifulSoup(r.text, "lxml")

		print "Parsing article urls..."
		# Select elements with a href attribute under divs with class story-headline
		url_tags = soup.select("div.story-headline [href]")
		print "Found {} articles".format(len(url_tags))

		for tag in url_tags:
			print tag.text
			text = self.get_article_text(tag.get("href"))
			self.store_text(text)

	def get_article_text(self, url):
		"""Parse the url of an article to a text with links removed."""
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "lxml")
		text = soup.find("article").text

		# Strip any part after "Read more"
		# Note: the actual phrase may be "Read more here", "Read more on this subject", etc.
		idx = text.find("Read more")
		text = text[:idx]

		# Store the name of the article
		self.current_article = soup.title.text
		return text

	def store_text(self, text):
		"""Write article text to a file."""
		title = self.current_article.rstrip(" - The Washington Post").rstrip(".")
		path = "data/training/washington_post/" + title + ".txt"
		with codecs.open(path, mode="w", encoding="utf8") as f:
			f.write(text)


class PoemParser:
	"""Parse famous poems from https://allpoetry.com/classics/famous_poems."""

	def parse_poem_urls(self):
		"""Reads urls from the list of 500 poems at https://allpoetry.com/classics/famous_poems?page=1.
		Note: unregistered users can only read the first 10 pages ~ 270 poems.
		"""
		# Iterate over the 10 pages in the list of poems.
		for i in range(1, 11):
			page = "?page="+str(i)
			r = requests.get("https://allpoetry.com/classics/famous_poems" + page)
			soup = BeautifulSoup(r.text, "lxml")

			# Get div tags from this page
			url_tags = soup.select("div.heading [href]")

			# Get the url of the poem and pass to store the poem
			for tag in url_tags:
				title = tag.text
				print title

				poem_url = "https://allpoetry.com" + tag.get("href")
				self.get_poem_text(poem_url)

	def get_poem_text(self, url):
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


class SteamParser:
	"""Parse game descriptions from the Steam storefront."""

	def dump_descriptions(self, ids):
		"""Fetch description for a random sample of n items from the Steam database and store to
		data/training/steam.
		Arg:
			ids (list): list of app ids of games whose descriptions to fetch
		"""
		count = 0
		error_count = 0
		for id_ in ids:
			try:
				title, text = self.get_app_description(id_)
				count += 1
				title = title.replace("/", "-")
				print title
				soup = BeautifulSoup(text, "lxml")
				# replace <br> tags with \ns
				for br in soup.find_all("br"):
					br.replace_with("\n")

				# Wrap various html tags in the description with newlines
				for tag in soup.select("h2.bb_tag, .bb_ul, h1"):
					tag.replace_with("\n" + tag.text + "\n")

				path = "data/training/steam/" + title + ".txt"
				with codecs.open(path, "w", "utf8") as f:
					f.write(soup.text)

			except TypeError: # thrown if get_app_description returned None
				error_count += 1
				continue

		print "Succesfully parsed {} titles with {} failed titles".format(count, error_count)

	def get_app_ids(self):
		"""Fetch a list of games on the Steam store and their descriptions."""
		r = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v2")
		app_list = r.json()
		app_list = app_list["applist"]["apps"]
		app_ids = [ app["appid"] for app in app_list if (not any( [token in app["name"] for token in ("Trailer", "Soundtrack", "OST", "Demo")] ) and app["appid"] >= 10) ]

		return app_ids

	def store_app_names(self):
		"""Write app names to a file."""
		r = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v2")
		app_list = r.json()
		app_list = app_list["applist"]["apps"]
		keywords = ("Trailer", "Soundtrack", "OST", "Demo", "DLC", "SDK", "Beta", "Map Pack")

		app_ids = [ app["name"] for app in app_list if (not any( [token in app["name"] for token in keywords] ) and app["appid"] >= 10) ]
		with open("data/training/steam/app_names.dat", "w") as f:
			for app in app_ids:
				name = app.encode("utf8")
				f.write(name + "\n")

	def get_app_description(self, id_):
		"""Fetch a game description matching an appid from store.steampowered.com/api.
		Note: this is an undocumented API and may change any time.
		"""
		url = "http://store.steampowered.com/api/appdetails?appids={}&cc=us&l=english".format(id_)
		r = requests.get(url)
		response = r.json()[str(id_)]

		if response["success"] and response["data"]["type"] == "game":
			name = response["data"]["name"]
			description = response["data"]["detailed_description"]

			return name, description




if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Parses various input to training data for text_generator.py")
	parser.add_argument("--tweets", help="Store new tweets from the specified Twitter screen name to data/training/screen_name.", metavar="screen_name")
	parser.add_argument("--wp", help="Store latest Washington Post editorials to data/training/washington_post.", action="store_true")
	parser.add_argument("--poem", help="Store famous poems to data/training/poems.", action="store_true")
	parser.add_argument("--steam", help="Store n random Steam game descriptions to data/training/steam", metavar="n", type=int)
	parser.add_argument("--folder", help="Merge the contents of a folder containing .txt files as one.")
	args = parser.parse_args()


	if args.tweets:
		screen_name = args.tweets.lstrip("@")
		tweet_parser = TwitterParser(screen_name)
		# check if there is a record of previously stored tweets
		id_ = tweet_parser.get_most_recent_tweet_id()

		try:
			tweets = tweet_parser.get_timeline_history(16, id_)
			tweet_parser.dump_tweets(tweets)
		except IndexError as e:
			print tweet_parser.basename, "already contains the most recent tweet"

	elif args.wp:
		wp_parser = WPParser()
		wp_parser.parse_headlines()

	elif args.poem:
		poem_parser = PoemParser()
		poem_parser.parse_poem_urls()

	elif args.steam:
		steam_parser = SteamParser()
		ids = steam_parser.get_app_ids()
		sample = random.sample(ids, args.steam)
		steam_parser.dump_descriptions(sample)

	elif args.folder:
		text_parser = TextParser(args.folder)
		text = text_parser.parse_folder()
		text_parser.dump_text(text)
