#!/usr/bin/env python3

# Parses famous poems from https://allpoetry.com/classics/famous_poems.
# Based on html parsing. 

import requests

from bs4 import BeautifulSoup
from src.parsers import base_parser
from src import utils



class PoemParser(base_parser.BaseParser):

	def __init__(self):
		super().__init__("poems.txt")

	def get_poem_urls(self):
		"""Reads urls for the list of 500 poems at https://allpoetry.com/classics/famous_poems?page=1.
		Note: unregistered users can only read the first 10 pages ~ 270 poems.
		"""
		urls = []
		# Iterate over the 10 pages in the list of poems.
		for i in range(1, 11):
			params = {"page": i}
			r = requests.get("https://allpoetry.com/classics/famous_poems", params=params)
			soup = BeautifulSoup(r.text, "html.parser")

			# Get div tags from this page
			url_tags = soup.select("div.clearfix [href]:first-child")

			# Get the url of the poem and pass to store the poem
			for tag in url_tags:
				poem_url = "https://allpoetry.com" + tag.get("href")
				urls.append(poem_url)

		return urls

	def parse(self):
		"""Parse poem text for each poem returned by get_poem_urls."""
		urls = self.get_poem_urls()
		texts = []
		for url in urls:
			r = requests.get(url)
			soup = BeautifulSoup(r.text, "html.parser")
			try:
				text = soup.select("div.poem_body")[0].text
				# split by newlines and drop the last line if it contains a copyright notice
				lines = text.split("\n")
				copy = "© by owner"
				lines = [line for line in lines if copy not in line]
				text = "\n".join(lines)

				texts.append(text)
			except IndexError:
				continue

		print("Parsed {} poems".format(len(texts)))
		self.content = " ".join(texts)


