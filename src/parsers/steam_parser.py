#!/usr/bin/env python3

# Parses Steam game descriptions to a plain text file. Uses both the official Steam API
# http://api.steampowered.com and the undocumented http://store.steampowered.com/api for
# fetching actual descriptions. See https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
# for community wiki on store.steampowered.com usage.
# 
# The database contains > 73 000 titles. In order to limit the output filesize, only a sample
# of all titles is used to generate the output. Sample size is passed to the initializer.
# Note that fetching app descriptions is done one at a time, ie. the default sample size of
# 200 results in 200 API calls.


import random
import os
import requests

from bs4 import BeautifulSoup
from src.parsers import base_parser
from src import utils


class SteamParser(base_parser.BaseParser):
	"""Parse game descriptions from the Steam storefront."""

	def __init__(self, size=200):
		"""Initialize parser with number of games whose description to read."""
		self.sample = random.sample(self.get_app_id_list(), size)
		self.s = requests.Session()
		super().__init__("steam.txt")

	def parse(self):
		"""Parses the sample of appids for game descriptions and store as self.content attribute.
		Note that not all apps in self.sample are games, usually running this will result is much
		smaller parsed appids than self.sample.
		"""
		descriptions = []
		for appid in self.sample:
			description = self.get_app_description(appid)
			# description is None if appid didn't match a valid game filter
			if description:
				descriptions.append(description)

		print("Parsed {} descriptions".format(len(descriptions)))
		self.content = " ".join(descriptions)

	def get_app_id_list(self):
		"""Fetch a list of games on the Steam store and their descriptions."""
		r = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v2")
		app_list = r.json()["applist"]["apps"]
		# excude trailers, soundtracks and demos as well titles not in english
		app_ids = [ app["appid"] for app in app_list if
			(not any( [token in app["name"] for token in ("Trailer", "Soundtrack", "OST", "Demo")] )
			and app["appid"] >= 10) 
			]

		return app_ids

	def get_app_description(self, appid):
		"""Fetch a single game description matching an API appid.
		Note: unlike api.steampowered.com this is an undocumented API and may change any time.
		"""
		url = "http://store.steampowered.com/api/appdetails"
		params = {"appids": appid, "cc": "us", "l": "english"}
		r = self.s.get(url, params=params)
		if r.status_code == 200:
			try:
				data = r.json()
				id_ = str(appid)
				# Exclude titles where English is not a supported languge.
				# This attempts to drop non-English descriptions, probably not perfect
				# but much faster than running a language detection API query.
				if "English" not in data[id_]["data"]["supported_languages"]:
					return

				valid_types = ("game", "dlc", "demo", "advertising", "mod")
				if data[id_]["data"]["type"] in valid_types:
					description = data[id_]["data"]["detailed_description"]
					# description is in html, use beautifulsoup to parse it as plain text
					soup = BeautifulSoup(description, "html.parser")

					return soup.text
			except (TypeError, KeyError):
				return

	def store_app_names(self):
		"""Write app names to a file."""
		r = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v2")
		app_list = r.json()
		app_list = app_list["applist"]["apps"]
		keywords = ("Trailer", "Soundtrack", "OST", "Demo", "DLC", "SDK", "Beta", "Map Pack")

		app_ids = [ app["name"] for app in app_list if (not any( [token in app["name"] for token in keywords] ) and app["appid"] >= 10) ]
		with open("steam_app_names.txt", "w") as f:
			for app in app_ids:
				f.write(app + "\n")

