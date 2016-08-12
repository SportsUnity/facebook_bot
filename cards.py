import config

import requests
from PIL import Image, ImageDraw
import numpy

from time import time, ctime
from datetime import datetime, timedelta

from traceback import print_exc

import json
from urllib2 import quote
from StringIO import StringIO
import os

class SportsCards:
	def __init__(self, server=""):
		self.server = server
		pass

	def __get_api_response(self, api_url):
		'''
		  This method checks the status of the request returned and returns the response in json on success.
		'''
		try:
			# sending get request to the API and getting the response in json
			r = requests.get(api_url)
			# if request is successfull that is no HTTPError Occured
			if r.ok:
				response = r.json()
				# rechecking by the status of 'success' param
				if response['success']:
					return response
				else:
					print "ERROR : in SportsCards.get_api_response; Failed to get successful Results.\n"
					return False
			else:
				print 'ERROR : in SportsCards.get_api_response; Failed API request, status > '+str(r.status_code)
				return False
		except Exception, e:
			print 'EXCEPTION : in SportsCards.get_api_response; '+str(e)+'.\n'
			return False

	def __is_game_today(self, epoch):
		'''
			This method returns True if date of the match is same as present day's date.
		'''
		# if the match epoch is less than present epoch, then return False
		if epoch < time():
			return False

		# convert the epoch of the match and present day epoch to one
		# format and check if they are equal
		present_day_date = datetime.fromtimestamp(time()).strftime("%Y-%m-%d")
		match_time = datetime.fromtimestamp(epoch).strftime("%Y-%m-%d")
		return match_time == present_day_date
	

	def __get_cricket_matches(self, match_list):
		'''
			This method returns the cricket matches that are on present day.
			(sport_type, series_name, series_id, match_id, home_team, away_team)
		'''
		try:
			games = []
			for match in match_list:
				# check with epoch time if date of match is equal to today's match's date
				if self.__is_game_today(match['match_time']):
					params = {}
					params['args'] = ('cricket', match['series_name'],
										match['series_id'], match['match_id'],
										match['home_team'],match['away_team']
									)
					params['countdown'] = match['match_time'] - time()
					games.append(params)
			return games
		except Exception, e:
			print 'EXCEPTION : SportsCards.__get_cricket_matches; '+str(e)+'.\n'
			return []


	def __home_vs_away(self, match):
		try:
			title = ""
			title += match['home_team_short_name'] if match['home_team_short_name'] else match['home_team']
			title += " vs "
			title += match['away_team_short_name'] if match['away_team_short_name'] else match['away_team']
			return title
		except:
			return "Today's Game"


	def __get_cropped_image(self, im, shape):
		# code : http://stackoverflow.com/questions/22588074/polygon-crop-clip-using-python-pil

		# convert the more to RGBA includes alpha param for transparency
		img = im.convert("RGBA")

		# convert to numpy
		imArray = numpy.asarray(img)

		# create mask with the shape provided in the function
		maskIm = Image.new('L', (imArray.shape[1], imArray.shape[0]), 0)
		ImageDraw.Draw(maskIm).polygon(shape, outline=1, fill=1)
		mask = numpy.array(maskIm)

		newImArray = numpy.empty(imArray.shape,dtype='uint8')

		# colors (three first columns, RGB)
		newImArray[:,:,:3] = imArray[:,:,:3]

		# transparency (4th column)
		newImArray[:,:,3] = mask*255

		# back to Image from numpy
		newIm = Image.fromarray(newImArray, "RGBA")
		return newIm


	def __combine_the_images(self, img1, img2, name):
		try:
			# get the StringIO instance (from response content) of the both the images and  save it in image object
			a = Image.open(img1)
			b = Image.open(img2)

			# # create a new Image obj with width = width of image 1 + width of image 2
			# # and height = max of both the hieghts
			# new_image = Image.new('RGB', (a.size[0]+b.size[0], max(a.size[1], b.size[1])))

			# # paste first image first to the new image
			# new_image.paste(a, (0, 0))

			# # now paste another image to the new image with offset equals widht of first image
			# new_image.paste(b, (a.size[0], 0))

			# # save the new image
			# new_image.save('images/'+name)

			shape = [(0, 0), (a.size[0], 0), (0, a.size[1])]
			img1 = self.__get_cropped_image(a, shape)

			shape = [(a.size[0], 0), (0, a.size[1]), a.size]
			img2 = self.__get_cropped_image(b, shape)

			img1.paste(img2, (0, 0), img2)

			img_dir = os.getcwd()+'/images'

			if not os.path.exists(img_dir):
				os.makedirs(img_dir)

			img1.save('images/'+name)

			# return True on no error in above statements
			return True
		except Exception as e:
			print 'EXCEPTION : SportsCards.__combine_the_images; '+str(e)+'.\n'
			return False

	def __get_vs_image_url(self, url1, url2, image_name):
		try:
			# set the image file name to be saved
			image_name = ((image_name.replace(" ", "")).lower())+".png"

			# check if the image already exists
			if not os.path.exists(os.getcwd()+"/images/"+image_name):
				# download the images and combine them, if combining process is unsucessful, return the default logo image
				if not self.__combine_the_images(StringIO((requests.get(url1)).content), StringIO((requests.get(url2)).content), image_name):
					return "https://pbs.twimg.com/profile_images/718021447386443777/dIipQWNy.jpg"

			return self.server+"/images/"+image_name
		except:
			# if in case anything goes wrong, return the defult sportsunity logo
			return "https://pbs.twimg.com/profile_images/718021447386443777/dIipQWNy.jpg"


	def __get_payload_for_card(self, sport, match_id, series_id, epoch):
		result = {"sport":sport, "match_id":match_id, "series_id":series_id, "epoch": epoch}
		return json.dumps({"type": "follow", "result": result})



	def __get_deeplink_for_match(self, sport, match_id, series_id):
		try:
			# get base url of the app
			url = config.app_deeplink

			# construct parameters for the present game
			ss = {}

			# set the flag for the right sport type
			ss["s"] = 1 if sport=='cricket' else 2

			# "r" - status: n = upcoming, l = live, f = finished
			# so in this case since we're showing the matches that
			# will happen present day (but not started yet), this
			# flag will be 'n'; i.e. upcoming match
			ss["r"] = 'n'

			ss["l"] = str(series_id)
			ss["m"] = str(match_id)

			# constructing url by encoding (quoting) the reserved characters
			# in the path section of url (quoting defined as per RFC 2396 for URI)
			# (for more info see doc of urrlib2.quote function from python lib)
			url += quote(json.dumps(ss))
			return url
		except:
			return config.app_deeplink # return playstore link of app


	def __get_buttons_for_cricket_card(self, match):
		buttons = []

		# creating postback button that will register user to follow a
		# particular match out of matches for presen day
		postback = {"type": "postback", "title": "Follow"}
		postback.update({"payload": self.__get_payload_for_card('cricket', match['match_id'], match['series_id'], match['match_time'])})
		buttons.append(postback)

		# creating button that will redirect to user to the match section (using deeplinking)
		# inside the app, if the app is installed; else it will redirect to play store link
		match_link = {"type":"web_url", "title": "View in App"}
		match_link.update({"url": self.__get_deeplink_for_match('cricket', match['match_id'], match['series_id'])})
		buttons.append(match_link)

		return buttons


	def __get_cricket_matches(self, match_list):
		'''
			This method returns the cricket matches that are on present day.
			(sport_type, series_name, series_id, match_id, home_team, away_team)
		'''
		try:
			games = []
			for match in match_list:
				# check with epoch time if date of match is equal to today's match's date
				if self.__is_game_today(match['match_time']):
					doc = {}
					doc['sport'] = 'cricket'
					doc['epoch'] = match['match_time']
					doc['series_id'] = match['series_id']
					doc['match_id'] = match['match_id']

					# creating a card element
					an_element = {}
					an_element["title"] = self.__home_vs_away(match)
					an_element["image_url"] = self.__get_vs_image_url(match['home_team_flag'], match['away_team_flag'], an_element["title"])
					an_element["subtitle"] = str(match['series_name'])
					an_element["buttons"] = self.__get_buttons_for_cricket_card(match)
					doc['element'] = an_element

					# appending the data into the docs
					games.append(doc)
			return games
		except Exception, e:
			print 'EXCEPTION : SportsCards.__temp_get_cricket_matches; '+str(e)+'.\n'
			return []

	def __get_buttons_for_football_card(self, match):
		buttons = []

		# creating postback button that will register user to follow a
		# particular match out of matches for presen day
		postback = {"type": "postback", "title": "Follow"}
		postback.update({"payload": self.__get_payload_for_card('football', match['match_id'], match['league_id'], match['match_date_epoch'])})
		buttons.append(postback)

		# creating button that will redirect to user to the match section (using deeplinking)
		# inside the app, if the app is installed; else it will redirect to play store link
		match_link = {"type":"web_url", "title": "View in App"}
		match_link.update({"url": self.__get_deeplink_for_match('football', match['match_id'], match['league_id'])})
		buttons.append(match_link)

		return buttons

	def __get_football_matches(self, match_list):
		'''
			This method returns the cricket matches that are on present day.
			(sport_type, series_name, series_id, match_id, home_team, away_team)
		'''
		try:
			games = []
			for match in match_list:
				# check with epoch time if date of match is equal to today's match's date
				if self.__is_game_today(match['match_date_epoch']):
					doc = {}
					doc['sport'] = 'football'
					doc['epoch'] = match['match_date_epoch']
					doc['series_id'] = match['league_id']
					doc['match_id'] = match['match_id']
					an_element = {}
					an_element["title"] = self.__home_vs_away(match)
					an_element["image_url"] = self.__get_vs_image_url(match['home_team_flag'], match['away_team_flag'], an_element["title"])
					an_element["subtitle"] = str(match['league_name'])
					an_element["buttons"] = self.__get_buttons_for_football_card(match)
					doc['element'] = an_element
					games.append(doc)
			return games
		except Exception, e:
			print 'EXCEPTION : SportsCards.__temp_get_football_matches; '+str(e)+'.\n'
			return []


	def __get_fixtures(self, data):
		'''
			This method returns all the games that are going to take place today.
		'''
		try:
			games_today = []
			# get today's cricket matches
			games_today += self.__get_cricket_matches(data['cricket'])
			# get today's football matches
			games_today += self.__get_football_matches(data['football'])
			return games_today
		except Exception, e:
			print 'EXCEPTION : SportsCards.__get_present_day_matches; '+str(e)+'.\n'

	def __save_data_into_mongo_db(self, data):
		'''
		This method saves the data into the mongo db database
		'''
		try:
			coll = config.mongo_conn.su_bot.today_matches
			coll.insert(data)
		except Exception, e:
			print 'EXCEPTION : SportsCards.__save_data_into_mongo_db; '+str(e)+'.\n'

	def get_game_cards(self):
		try:
			response = self.__get_api_response("http://scoreslb-822670678.ap-northeast-2.elb.amazonaws.com/v1/get_all_matches_list")
			if response:
				fixtures = self.__get_fixtures(response['data'])
				self.__save_data_into_mongo_db(fixtures)
			else:
				return
		except Exception, e:
			print 'EXCEPTION : SportsCards.schedule_matches; '+str(e)+'.\n'
			return