from __future__ import division
import httplib2,json
import zlib
import zipfile
import sys
import re
import datetime
import operator
import sqlite3
import os
from datetime import datetime
from datetime import date
import pytz 
from tzlocal import get_localzone
import requests
from termcolor import colored, cprint
from pygraphml import *
#from pygraphml.GraphMLParser import *
#from pygraphml.Graph import *
#from pygraphml.Node import *
#from pygraphml.Edge import *
from time import sleep
import numpy as np

from bs4 import BeautifulSoup as BS
from urllib import urlretrieve

from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import time,re,sys
from selenium.webdriver.common.keys import Keys
import datetime
from bs4 import BeautifulSoup
from StringIO import StringIO
import pickle

import getpass

from pyvirtualdisplay import Display

requests.adapters.DEFAULT_RETRIES = 10

PATH = os.getcwd()
FB_SCRAPE = True
HEADLESS = True

h = httplib2.Http(".cache")

if HEADLESS:
        display = Display(visible=0, size=(800, 600))
        display.start()

def get_creds():
        facebook_username = raw_input("please enter your facebook username: ")
        facebook_password = getpass.getpass("please enter your facebook password: ")
        
        return facebook_username, facebook_password

print facebook_username
print facebook_password

global uid
uid = ""
username = ""
internetAccess = True
cookies = {}
all_cookies = {}
reportFileName = ""

#For consonlidating all likes across Photos Likes+Post Likes
peopleIDList = []
likesCountList = []
timePostList = []
placesVisitedList = []

#Chrome Options
def init_chrome():
#if FB_SCRAPE:
        print "initializing chrome..."
        chromeOptions = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images":2}
        chromeOptions.add_experimental_option("prefs",prefs)
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        
        return driver
        
class fb_node(object):
        def __init__(self, i, key):
                self.i = i
                self.key = key

class fb_graph(object):
        def __init__(self, keys):
                self.key2i = {keys[i]: i for i in range(len(keys))}
                self.nodes = [fb_node(i, keys[i]) for i in range(len(keys))]
                self.adj_mat = np.zeros([len(keys)])
                self.curr_node = self.nodes[0]
        
        def insert_node(self, key, incoming, outgoing):
                '''incoming and outgoing are assumed to be keys'''
                index = len(self.nodes)
                nd = fb_node(index, key)
                self.nodes.append(nd)
                self.key2i[key] = index
                inVec = np.zeros(self.adj_mat.shape[0]) #n
                outVec = np.zeros(self.adj_mat.shape[1] + 1) #m + 1
                for neighbour in incoming:
                        inVec[self.key2i[neighbour]] = 1
                for neighbour in outgoing:
                        outVec[self.key2i[neighbour]] = 1
        
                        
def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True
#login

def loginFacebook(driver):
	driver.implicitly_wait(120)
	driver.get("https://www.facebook.com/")
	assert "Welcome to Facebook" in driver.title
	time.sleep(3)
	driver.find_element_by_id('email').send_keys(facebook_username)
	driver.find_element_by_id('pass').send_keys(facebook_password)
	driver.find_element_by_id("loginbutton").click()
	global all_cookies
	all_cookies = driver.get_cookies()
	html = driver.page_source
	if "Incorrect Email/Password Combination" in html:
		print "[!] Incorrect Facebook username (email address) or password"
		sys.exit()
#get id		

def convertUser2ID2(driver,username):
	url="http://graph.facebook.com/"+username
	resp, content = h.request(url, "GET")
	if resp.status==200:
		results = json.loads(content)
		if len(results['id'])>0:
			fbid = results['id']
			return fbid
	
	
#general
def google_search(query, driver):
        url = 'https://www.google.ca'
        driver.get(url)
        searchBX = driver.find_element_by_id('lst-ib')
        searchBX.click()
        searchBX.send_keys(query)
        searchBX.send_keys(Keys.RETURN)
        
#        driver.send_keys
        return driver, searchBX

def normalize(s):
	if type(s) == unicode: 
       		return s.encode('utf8', 'ignore')
	else:
        	return str(s)

def downloadFile(url):	
	global cookies
	for s_cookie in all_cookies:
			cookies[s_cookie["name"]]=s_cookie["value"]
	r = requests.get(url,cookies=cookies)
	html = r.content
	return html
			
#timeline
def downloadTimeline(username, driver):#not actually username; user id...should change
	url = 'https://www.facebook.com/'+username.strip()
	driver.get(url)	
	print "[*] Crawling Timeline"
	if "Sorry, this page isn't available" in driver.page_source:
		print "[!] Cannot access page "+url
		return ""
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
                lastCount = lenOfPage
                time.sleep(3)
                lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount==lenOfPage:
			print "[*] Looking for 'Show Older Stories' Link"
			try:
				clickLink = WebDriverWait(driver, 1).until(lambda driver : driver.find_element_by_link_text('Show Older Stories'))
				if clickLink:
					print "[*] Clicked 'Show Older Stories' Link"
					driver.find_element_by_link_text('Show Older Stories').click()
				else:
					print "[*] Indexing Timeline"
					break
		                        match=True
			except TimeoutException:				
				match = True
	return driver.page_source

def downloadAbout(username, driver):
        url = 'https://www.facebook.com/' + username + '/about'
        driver.get(url)
	print "[*] Crawling About Section list"
	if "Sorry, this page isn't available" in driver.page_source:
		print "[!] Cannot access page "+url
		return ""
	
	soup = BeautifulSoup(driver.page_source)
	soup = soup.find_all("div",{"class":"_4ms4"})
	info = {}
	
	overview = []
	for item in soup:
	        item = item.find_all(text=True)
	        overview.append(item)
	info['overview'] = overview[0]
	time.sleep(3)
	try:
                work_edu = driver.find_element_by_link_text('Work and Education')
	        work_edu.click()
	        soup = BeautifulSoup(driver.page_source)

	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	
	        work_edu = []
	        for item in soup:
	                item = item.find_all(text=True)
	                work_edu.append(item)
	        info['work_edu'] = work_edu[0]
	        time.sleep(3)
	except:
	        print "could not find work and education section"
	        
	try:	
	        places_lived = driver.find_element_by_partial_link_text('Places')
	        places_lived.click()
	        soup = BeautifulSoup(driver.page_source)
	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	        places = []
	        for item in soup:
	                item = item.find_all(text=True)
	                places.append(item)
	        info['places'] = places[0]
	        time.sleep(3)
	except:
	        print "could not find places lived section" 
	
	try:
	        contact_info = driver.find_element_by_link_text('Contact and Basic Info')
	        contact_info.click()
	        soup = BeautifulSoup(driver.page_source)
	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	        contact = []
	        for item in soup:
	                item = item.find_all(text=True)
	                contact.append(item)
	        info['contact'] = contact[0]
	except:
	        print "could not find contact and basic info section"
	
        try:
	        time.sleep(3)
	        family_relations = driver.find_element_by_link_text('Family and Relationships')
	        family_relations.click()
	        soup = BeautifulSoup(driver.page_source)
	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	        relations = []
	        for item in soup:
	                item = item.find_all(text=True)
	                relations.append(item)
	        info['relations'] = relations[0]
	        time.sleep(3)
	except:
	        print "could not find family and relationships section"
	        
	try:
	        details = driver.find_element_by_partial_link_text('Details About')
	        details.click()
	        soup = BeautifulSoup(driver.page_source)
	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	        more = []
	        for item in soup:
	                item = item.find_all(text=True)
	                more.append(item)
	        info['more'] = more[0]
	        time.sleep(3)
	except:
	        print "could not find more details section"
	try:
	        life_events = driver.find_element_by_link_text('Life Events')
	        life_events.click()
	        soup = BeautifulSoup(driver.page_source)
	        soup = soup.find_all("div",{"class":"_4ms4"})
	
	        events = []
	        for item in soup:
	                item = item.find_all(text=True)
	                events.append(item)
	        info['events'] = events[0]
	        time.sleep(3)
	except:
	        print "could not find about life events section"
	
                
	return info

def downloadFriends(username, driver):
        scroll = "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        url = 'https://www.facebook.com/' + username + '/friends'
        driver.get(url)
	print "[*] Crawling Friend list"
	if "Sorry, this page isn't available" in driver.page_source:
		print "[!] Cannot access page "+url
		return ""
	time.sleep(3)
        lenOfPage = driver.execute_script(scroll)
        lastCount = lenOfPage
        match=False
        pre = lenOfPage
        post = 0
        while (match==False):
#        for i in range(20):
#        while(match==False):
#                photos = driver.find_element_by_id('u_1a_n')
#                print photos 
                time.sleep(3)
                post = driver.execute_script(scroll)
#                print "pre: {}; post: {}".format(pre, post)
#                print pre == post
                if pre == post:
                        match = True
                pre = post
#                driver.find_element_by_link_text(
#                if photos != None:
#                        match = True
#			print "[*] Looking for 'See All' Link"
#			try:
#				clickLink = WebDriverWait(driver, 1).until(lambda driver : driver.find_element_by_link_text('Show Older Stories'))
#				if clickLink:
#					print "[*] Clicked 'See All' Link"
#					driver.find_element_by_link_text('See All').click()
#				else:
#					print "[*] Indexing About Section"
#					break
#		                        match=True
#			except TimeoutException:				
#				match = True
	return driver.page_source

def parseTimeline(html,username):
	soup = BeautifulSoup(html)	
	tlTime = soup.findAll("abbr")
	temp123 = soup.findAll("div",{"role" : "article"})
	placesCheckin = []
	timeOfPostList = []

	counter = 0

	for y in temp123:
		soup1 = BeautifulSoup(str(y))
		tlDateTimeLoc = soup1.findAll("a",{"class" : "uiLinkSubtle"})
		#Universal Time
		try:
			soup2 = BeautifulSoup(str(tlDateTimeLoc[0]))
			tlDateTime = soup2.find("abbr")	
			#Facebook Post Link	
			tlLink = tlDateTimeLoc[0]['href']

			try:
				tz = get_localzone()
				unixTime = str(tlDateTime['data-utime'])
				localTime = (datetime.datetime.fromtimestamp(int(unixTime)).strftime('%Y-%m-%d %H:%M:%S'))
				timePostList.append(localTime)
				timeOfPost = localTime
				timeOfPostList.append(localTime)

				print "[*] Time of Post: "+localTime
			except TypeError:
				continue
			if "posts" in tlLink:
				#print tlLink.strip()
				pageID = tlLink.split("/")

				parsePost(pageID[3],username)
				peopleIDLikes = parseLikesPosts(pageID[3])

				try:
					for id1 in peopleIDLikes:
						global peopleIDList
						global likesCountList
						if id1 in peopleIDList:
							lastCount = 0
							position = peopleIDList.index(id1)
							likesCountList[position] +=1
						else:
							peopleIDList.append(id1)
							likesCountList.append(1)
				except TypeError:
					continue
				
			if len(tlDateTimeLoc)>2:
				try:
					#Device / Location
					if len(tlDateTimeLoc[1].text)>0:
						print "[*] Location of Post: "+unicode(tlDateTimeLoc[1].text)
					if len(tlDateTimeLoc[2].text)>0:
						print "[*] Device: "+str(tlDateTimeLoc[2].text)
				except IndexError:
					continue	

			else:
				try:
					#Device / Location
					if len(tlDateTimeLoc[1].text)>0:
						if "mobile" in tlDateTimeLoc[1].text:
							print "[*] Device: "+str(tlDateTimeLoc[1].text)
						else:
							print "[*] Location of Post: "+unicode(tlDateTimeLoc[1].text)
					
				except IndexError:
					continue	
			#Facebook Posts
			tlPosts = soup1.find("span",{"class" : "userContent"})
			
			try:
				tlPostSec = soup1.findall("span",{"class" : "userContentSecondary fcg"})
				tlPostMsg = ""
			
				#Places Checked In
			except TypeError:
				continue
			soup3 = BeautifulSoup(str(tlPostSec))
			hrefLink = soup3.find("a")

			"""
			if len(str(tlPostSec))>0:
				tlPostMsg = str(tlPostSec)
				#if " at " in str(tlPostMsg) and " with " not in str(tlPostMsg):
				if " at " in str(tlPostMsg):
					print str(tlPostSec)

					print tlPostMsg
					#print hrefLink
					#placeUrl = hrefLink['href'].encode('utf8').split('?')[0]
					#print "[*] Place: "+placeUrl										
					#placesCheckin.append([timeOfPost,placeUrl])
			"""

			try:
				if len(tlPosts)>0:				
					tlPostStr = re.sub('<[^>]*>', '', str(tlPosts))
					if tlPostStr!=None:
						print "[*] Message: "+str(tlPostStr)
			except TypeError as e:
				continue


			tlPosts = soup1.find("div",{"class" : "translationEligibleUserMessage userContent"})
			try:
				if len(tlPosts)>0:
					tlPostStr = re.sub('<[^>]*>', '', str(tlPosts))
					print "[*] Message: "+str(tlPostStr)	
			except TypeError:
				continue
		except IndexError as e:
			continue
		counter+=1
	
	tlDeviceLoc = soup.findAll("a",{"class" : "uiLinkSubtle"})

	print '\n'

	global reportFileName
	if len(reportFileName)<1:
		reportFileName = username+"_report.txt"
	reportFile = open(reportFileName, "w")
	
	reportFile.write("\n********** Places Visited By "+str(username)+" **********\n")
	filename = username+'_placesVisited.htm'
	if not os.path.lexists(filename):
		html = downloadPlacesVisited(driver,uid)
		text_file = open(filename, "w")
		text_file.write(html.encode('utf8'))
		text_file.close()
	else:
		html = open(filename, 'r').read()
	dataList = parsePlacesVisited(html)
	count=1
	for i in dataList:
		reportFile.write(normalize(i[2])+'\t'+normalize(i[1])+'\t'+normalize(i[3])+'\n')
		count+=1
	
	reportFile.write("\n********** Places Liked By "+str(username)+" **********\n")
	filename = username+'_placesLiked.htm'
	if not os.path.lexists(filename):
		html = downloadPlacesLiked(driver,uid)
		text_file = open(filename, "w")
		text_file.write(html.encode('utf8'))
		text_file.close()
	else:
		html = open(filename, 'r').read()
	dataList = parsePlacesLiked(html)
	count=1
	for i in dataList:
		reportFile.write(normalize(i[2])+'\t'+normalize(i[1])+'\t'+normalize(i[3])+'\n')
		count+=1

	reportFile.write("\n********** Places checked in **********\n")
	for places in placesVisitedList:
		unixTime = places[0]
		localTime = (datetime.datetime.fromtimestamp(int(unixTime)).strftime('%Y-%m-%d %H:%M:%S'))
		reportFile.write(localTime+'\t'+normalize(places[1])+'\t'+normalize(places[2])+'\n')

	reportFile.write("\n********** Apps used By "+str(username)+" **********\n")
	filename = username+'_apps.htm'
	if not os.path.lexists(filename):
		html = downloadAppsUsed(driver,uid)
		text_file = open(filename, "w")
		text_file.write(html.encode('utf8'))
		text_file.close()
	else:
		html = open(filename, 'r').read()
	data1 = parseAppsUsed(html)
	result = ""
	for x in data1:
		reportFile.write(normalize(x)+'\n')
		x = x.lower()
		if "blackberry" in x:
			result += "[*] User is using a Blackberry device\n"
		if "android" in x:
			result += "[*] User is using an Android device\n"
		if "ios" in x or "ipad" in x or "iphone" in x:
			result += "[*] User is using an iOS Apple device\n"
		if "samsung" in x:
			result += "[*] User is using a Samsung Android device\n"
	reportFile.write(result)

	reportFile.write("\n********** Videos Posted By "+str(username)+" **********\n")
	filename = username+'_videosBy.htm'
	if not os.path.lexists(filename):
		html = downloadVideosBy(driver,uid)
		text_file = open(filename, "w")
		text_file.write(html.encode('utf8'))
		text_file.close()
	else:
		html = open(filename, 'r').read()
	dataList = parseVideosBy(html)
	count=1
	for i in dataList:
		reportFile.write(normalize(i[2])+'\t'+normalize(i[1])+'\n')
		count+=1

	reportFile.write("\n********** Pages Liked By "+str(username)+" **********\n")
	filename = username+'_pages.htm'
	if not os.path.lexists(filename):
		print "[*] Caching Pages Liked: "+username
		html = downloadPagesLiked(driver,uid)
		text_file = open(filename, "w")
		text_file.write(html.encode('utf8'))
		text_file.close()
	else:
		html = open(filename, 'r').read()
	dataList = parsePagesLiked(html)
	for i in dataList:
		pageName = normalize(i[0])
		tmpStr	= normalize(i[3])+'\t'+normalize(i[2])+'\t'+normalize(i[1])+'\n'
		reportFile.write(tmpStr)
	print "\n"

	c = conn.cursor()
	reportFile.write("\n********** Friendship History of "+str(username)+" **********\n")
	c.execute('select * from friends where sourceUID=?',(uid,))
	dataList = c.fetchall()
	try:
		if len(str(dataList[0][4]))>0:
			for i in dataList:
				#Date First followed by Username
				reportFile.write(normalize(i[4])+'\t'+normalize(i[3])+'\t'+normalize(i[2])+'\t'+normalize(i[1])+'\n')
				#Username followed by Date
				#reportFile.write(normalize(i[4])+'\t'+normalize(i[3])+'\t'+normalize(i[2])+'\t'+normalize(i[1])+'\n')
		print '\n'
	except IndexError:
		pass

	reportFile.write("\n********** Friends of "+str(username)+" **********\n")
	reportFile.write("*** Backtracing from Facebook Likes/Comments/Tags ***\n\n")
	c = conn.cursor()
	c.execute('select userName from friends where sourceUID=?',(uid,))
	dataList = c.fetchall()
	for i in dataList:
		reportFile.write(str(i[0])+'\n')
	print '\n'

	tempList = []
	totalLen = len(timeOfPostList)
	timeSlot1 = 0
	timeSlot2 = 0
	timeSlot3 = 0 
	timeSlot4 = 0
	timeSlot5 = 0 
	timeSlot6 = 0 
	timeSlot7 = 0 
	timeSlot8 = 0 

	count = 0
	if len(peopleIDList)>0:
		likesCountList, peopleIDList  = zip(*sorted(zip(likesCountList,peopleIDList),reverse=True))
	
		reportFile.write("\n********** Analysis of Facebook Post Likes **********\n")
		while count<len(peopleIDList):
			testStr = str(likesCountList[count]).encode('utf8')+'\t'+str(peopleIDList[count]).encode('utf8')
			reportFile.write(testStr+"\n")
			count+=1	

	reportFile.write("\n********** Analysis of Interactions between "+str(username)+" and Friends **********\n")
	c = conn.cursor()
	c.execute('select userName from friends where sourceUID=?',(uid,))
	dataList = c.fetchall()
	photosliked = []
	photoscommented = []
	userID = []
	
	photosLikedUser = []
	photosLikedCount = []
	photosCommentedUser = []
	photosCommentedCount = []
	
	for i in dataList:
		c.execute('select * from photosLiked where sourceUID=? and username=?',(uid,i[0],))
		dataList1 = []
		dataList1 = c.fetchall()
		if len(dataList1)>0:
			photosLikedUser.append(normalize(i[0]))
			photosLikedCount.append(len(dataList1))
	for i in dataList:
		c.execute('select * from photosCommented where sourceUID=? and username=?',(uid,i[0],))
		dataList1 = []
		dataList1 = c.fetchall()
		if len(dataList1)>0:	
			photosCommentedUser.append(normalize(i[0]))
			photosCommentedCount.append(len(dataList1))
	if(len(photosLikedCount)>1):	
		reportFile.write("Photo Likes: "+str(username)+" and Friends\n")
		photosLikedCount, photosLikedUser  = zip(*sorted(zip(photosLikedCount, photosLikedUser),reverse=True))	
		count=0
		while count<len(photosLikedCount):
			tmpStr = str(photosLikedCount[count])+'\t'+normalize(photosLikedUser[count])+'\n'
			count+=1
			reportFile.write(tmpStr)
	if(len(photosCommentedCount)>1):	
		reportFile.write("\n********** Comments on "+str(username)+"'s Photos **********\n")
		photosCommentedCount, photosCommentedUser  = zip(*sorted(zip(photosCommentedCount, photosCommentedUser),reverse=True))	
		count=0
		while count<len(photosCommentedCount):
			tmpStr = str(photosCommentedCount[count])+'\t'+normalize(photosCommentedUser[count])+'\n'
			count+=1
			reportFile.write(tmpStr)


	reportFile.write("\n********** Analysis of Time in Facebook **********\n")
	for timePost in timeOfPostList:
		tempList.append(timePost.split(" ")[1])
		tempTime = (timePost.split(" ")[1]).split(":")[0]
		tempTime = int(tempTime)
		if tempTime >= 21:
			timeSlot8+=1
		if tempTime >= 18 and tempTime < 21:
			timeSlot7+=1
		if tempTime >= 15 and tempTime < 18:
			timeSlot6+=1
		if tempTime >= 12 and tempTime < 15:
			timeSlot5+=1
		if tempTime >= 9 and tempTime < 12:
			timeSlot4+=1
		if tempTime >= 6 and tempTime < 9:
			timeSlot3+=1
		if tempTime >= 3 and tempTime < 6:
			timeSlot2+=1
		if tempTime >= 0 and tempTime < 3:
			timeSlot1+=1
	reportFile.write("Total % (00:00 to 03:00) "+str((timeSlot1/totalLen)*100)+" %\n")
	reportFile.write("Total % (03:00 to 06:00) "+str((timeSlot2/totalLen)*100)+" %\n")
	reportFile.write("Total % (06:00 to 09:00) "+str((timeSlot3/totalLen)*100)+" %\n")
	reportFile.write("Total % (09:00 to 12:00) "+str((timeSlot4/totalLen)*100)+" %\n")
	reportFile.write("Total % (12:00 to 15:00) "+str((timeSlot5/totalLen)*100)+" %\n")
	reportFile.write("Total % (15:00 to 18:00) "+str((timeSlot6/totalLen)*100)+" %\n")
	reportFile.write("Total % (18:00 to 21:00) "+str((timeSlot7/totalLen)*100)+" %\n")
	reportFile.write("Total % (21:00 to 24:00) "+str((timeSlot8/totalLen)*100)+" %\n")

	"""
	reportFile.write("\nDate/Time of Facebook Posts\n")
	for timePost in timeOfPostList:
		reportFile.write(timePost+'\n')	
	"""
	reportFile.close()
	
def parsePost(id,username):
	filename = 'posts__'+str(id)
	if not os.path.lexists(filename):
		print "[*] Caching Facebook Post: "+str(id)
		url = "https://www.facebook.com/"+username+"/posts/"+str(id)
		driver.get(url)	
		if "Sorry, this page isn't available" in driver.page_source:
			print "[!] Cannot access page "+url
			return ""
        	lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        	match=False
        	while(match==False):
        	        time.sleep(1)
        	        lastCount = lenOfPage
               		lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                	if lastCount==lenOfPage:
                	        match=True
		html1 = driver.page_source	
		text_file = open(filename, "w")
		text_file.write(normalize(html1))
		text_file.close()
	else:
		html1 = open(filename, 'r').read()
	soup1 = BeautifulSoup(html1)
	htmlList = soup1.find("h5",{"class" : "_6nl"})
	tlTime = soup1.find("abbr")
	if " at " in str(htmlList):
		soup2 = BeautifulSoup(str(htmlList))
		locationList = soup2.findAll("a",{"class" : "profileLink"})
		locUrl = locationList[len(locationList)-1]['href']
		locDescription = locationList[len(locationList)-1].text
		locTime = tlTime['data-utime']
		placesVisitedList.append([locTime,locDescription,locUrl])


def parseLikesPosts(id):
	peopleID = []
	filename = 'likes_'+str(id)
	if not os.path.lexists(filename):
		print "[*] Caching Post Likes: "+str(id)
		url = "https://www.facebook.com/browse/likes?id="+str(id)
		driver.get(url)	
		if "Sorry, this page isn't available" in driver.page_source:
			print "[!] Cannot access page "+url
			return ""
        	lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        	match=False
        	while(match==False):
        	        time.sleep(1)
        	        lastCount = lenOfPage
               		lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                	if lastCount==lenOfPage:
                	        match=True
		html1 = driver.page_source	
		text_file = open(filename, "w")
		text_file.write(normalize(html1))
		text_file.close()
	else:
		html1 = open(filename, 'r').read()
	soup1 = BeautifulSoup(html1)
	peopleLikeList = soup1.findAll("div",{"class" : "fsl fwb fcb"})

	if len(peopleLikeList)>0:
		print "[*] Extracting Likes from Post: "+str(id)
		for x in peopleLikeList:
			soup2 = BeautifulSoup(str(x))
			peopleLike = soup2.find("a")
			peopleLikeID = peopleLike['href'].split('?')[0].replace('https://www.facebook.com/','')
			if peopleLikeID == 'profile.php':	
				r = re.compile('id=(.*?)&fref')
				m = r.search(str(peopleLike['href']))
				if m:
					peopleLikeID = m.group(1)
			print "[*] Liked Post: "+"\t"+peopleLikeID
			if peopleLikeID not in peopleID:
				peopleID.append(peopleLikeID)
		
		return peopleID	

def parseUserInfo(html):
	userEduWork = []
	userLivingCity = ""
	userCurrentCity = ""
	userLiveEvents = []
	userGender = ""
	userStatus = ""
	userGroups = []

	#try:
	soup = BeautifulSoup(str(html))
	
	pageLeft = soup.findAll("div", {"class" : "_4_g4 lfloat"})
	pageRight = soup.findAll("div", {"class" : "_4_g5 rfloat"})
	tempList = []

	try:
		soup1 = BeautifulSoup(str(pageLeft[0]))
		eduWork = soup.findAll("div", {"class" : "clearfix fbProfileExperience"})
		for i in eduWork:
			soup1 = BeautifulSoup(str(i))
			eduWorkCo = soup1.findAll("div", {"class" : "experienceTitle"},text=True)		
			eduWorkExp = soup1.findAll("div",{"class" : "experienceBody fsm fwn fcg"},text=True)
			try:
				strEduWork = eduWorkExp[0].encode('utf8')+'\t'+ eduWorkExp[1].encode('utf8')
				userEduWork.append(strEduWork)
			except IndexError:
				strEduWork = eduWorkExp[0].encode('utf8')				
				userEduWork.append(strEduWork)
				continue		
	except IndexError:
		pass
	relationships = soup.findAll("div", {"id" : "pagelet_relationships"})
	featured_pages = soup.findAll("div", {"id" : "pagelet_featured_pages"})
	bio = soup.findAll("div", {"id" : "pagelet_bio"})
	quotes = soup.findAll("div", {"id" : "pagelet_quotes"})

	hometown1 = soup.findAll("div", {"id" : "pagelet_hometown"})
	soup1 = BeautifulSoup(str(hometown1))
	hometown2  = soup1.findAll("div", {"id" : "hometown"},text=True)
	counter=0
	for z in hometown2:
		if z=="Current City":
			userCurrentCity = hometown2[counter+1]
			#print "CurrentCity: "+hometown2[counter+1]
		elif z=="Living":
			userLivingCity = hometown2[counter+1]
			#print "Living: "+hometown2[counter+1]
		counter+=1

	try:
		soup1 = BeautifulSoup(str(pageRight[0]))
		liveEvents = soup1.findAll("div",{"class" : "fbTimelineSection mtm fbTimelineCompactSection"},text=True)
		printOn=False
		for i in liveEvents:
			if printOn==True:
				userLiveEvents.append(i.encode('utf8'))
				#print "Life Events: "+i.encode('utf8')
			if i=="Life Events":
				printOn=True	
	except IndexError:
		pass
	basicInfo = soup1.findAll("div",{"class" : "fbTimelineSection mtm _bak fbTimelineCompactSection"},text=True)
	printOn=False
	counter=0
	for i in basicInfo:
		if printOn==True:
			if basicInfo[counter-1]=="Gender":
				#print "userGender: "+i.encode('utf8')
				userGender = i.encode('utf8')
			if basicInfo[counter-1]=="Relationship Status":
				#print "userStatus: "+i.encode('utf8')
				userStatus = i.encode('utf8')
			printOff=False
		if i=="Gender":
			printOn=True
		if i=="Relationship Status":
			printOn=True	
		counter+=1
	soup = BeautifulSoup(html)	
	groups = soup.findAll("div",{"class" : "mbs fwb"})
	r = re.compile('a href="(.*?)\"')
	for g in groups:
		m = r.search(str(g))
		if m:
			userGroups.append(['https://www.facebook.com'+m.group(1),g.text])
	#for x in userGroups:
	#	print x[0].encode('utf8')+'\t'+x[1].encode('utf8')
	tempList.append([userEduWork,userLivingCity,userCurrentCity,userLiveEvents,userGender,userStatus,userGroups])
	return tempList

#get app info
			
def downloadAppsUsed(driver,userid):
	driver.get('https://www.facebook.com/search/'+str(userid)+'/apps-used')
	if "Sorry, we couldn't find any results for this search." in driver.page_source:
		print "[!] Apps used list is hidden"
		return ""
	else:
	        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
       		match=False
        	while(match==False):
                	time.sleep(3)
                	lastCount = lenOfPage
                	lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                	if lastCount==lenOfPage:
                	        match=True
		return driver.page_source

def parseAppsUsed(html):
	soup = BeautifulSoup(html)	
	appsData = soup.findAll("div", {"class" : "_zs fwb"})
	tempList = []
	for x in appsData:
		tempList.append(x.text)
	return tempList
	
#get pages liked info

def downloadPagesLiked(driver,userid):
	driver.get('https://www.facebook.com/search/'+str(userid)+'/pages-liked')
	if "Sorry, we couldn't find any results for this search." in driver.page_source:
		print "Pages liked list is hidden"
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
                time.sleep(3)
                lastCount = lenOfPage
                lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount==lenOfPage:
                        match=True
	return driver.page_source


def parsePagesLiked(html):
	soup = BeautifulSoup(html)	
	pageName = soup.findAll("div", {"class" : "_zs fwb"})
	pageCategory = soup.findAll("div", {"class" : "_dew _dj_"})
	tempList = []
	count=0
	r = re.compile('a href="(.*?)\?ref=')
	for x in pageName:
		m = r.search(str(x))
		if m:
			try:
				pageCategory[count]
				tempList.append([uid,x.text,pageCategory[count].text,m.group(1)])
			except:
				continue
		count+=1
	return tempList
	
#photos by

def downloadPhotosBy(driver,userid):
	driver.get('https://www.facebook.com/search/'+str(userid)+'/photos-by')
	if "Sorry, we couldn't find any results for this search." in driver.page_source:
		print "Photos commented list is hidden"
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
                time.sleep(3)
                lastCount = lenOfPage
                lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount==lenOfPage:
                        match=True
	return driver.page_source

	
def parsePhotosBy(html):
	soup = BeautifulSoup(html)	
	photoPageLink = soup.findAll("a", {"class" : "_23q"})
	tempList = []
	for i in photoPageLink:
		html = str(i)
		soup1 = BeautifulSoup(html)
		pageName = soup1.findAll("img", {"class" : "img"})
		pageName1 = soup1.findAll("img", {"class" : "scaledImageFitWidth img"})
		pageName2 = soup1.findAll("img", {"class" : "_46-i img"})	
		for z in pageName2:
			if z['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),z['alt'],z['src'],i['href'],username3])
		for y in pageName1:
			if y['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),y['alt'],y['src'],i['href'],username3])
		for x in pageName:
			if x['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),x['alt'],x['src'],i['href'],username3])
	return tempList
	

#photos of

def downloadPhotosOf(driver,userid):
	driver.get('https://www.facebook.com/search/'+str(userid)+'/photos-of')
	if "Sorry, we couldn't find any results for this search." in driver.page_source:
		print "Photos commented list is hidden"
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
                time.sleep(3)
                lastCount = lenOfPage
                lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                if lastCount==lenOfPage:
                        match=True
	return driver.page_source

def parsePhotosOf(html):
	soup = BeautifulSoup(html)	
	photoPageLink = soup.findAll("a", {"class" : "_23q"})
	tempList = []
	for i in photoPageLink:
		html = str(i)
		soup1 = BeautifulSoup(html)
		pageName = soup1.findAll("img", {"class" : "img"})
		pageName1 = soup1.findAll("img", {"class" : "scaledImageFitWidth img"})
		pageName2 = soup1.findAll("img", {"class" : "_46-i img"})	
		for z in pageName2:
			if z['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),z['alt'],z['src'],i['href'],username3])
		for y in pageName1:
			if y['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),y['alt'],y['src'],i['href'],username3])
		for x in pageName:
			if x['src'].endswith('.jpg'):
				url1 = i['href']
				r = re.compile('fbid=(.*?)&set=bc')
				m = r.search(url1)
				if m:
					filename = 'fbid_'+ m.group(1)+'.html'
					filename = filename.replace("profile.php?id=","")
					if not os.path.lexists(filename):
						#html1 = downloadPage(url1)
						html1 = downloadFile(url1)
						print "[*] Caching Photo Page: "+m.group(1)
						text_file = open(filename, "w")
						text_file.write(normalize(html1))
						text_file.close()
					else:
						html1 = open(filename, 'r').read()
				soup2 = BeautifulSoup(html1)
				username2 = soup2.find("div", {"class" : "fbPhotoContributorName"})
				r = re.compile('a href="(.*?)"')
				m = r.search(str(username2))
				if m:	
					username3 = m.group(1)
					username3 = username3.replace("https://www.facebook.com/","")
					username3 = username3.replace("profile.php?id=","")
					print "[*] Extracting Data from Photo Page: "+username3
					tempList.append([str(uid),x['alt'],x['src'],i['href'],username3])
	return tempList

###########################extra functions#############
def html2File(html, fName):
        f = open(fName,'w')
        f.write(normalize(html))
        f.close()

def importHtml(fName):
	f = open(fName,'r')
	return f.read()
	
def extractPhotos(html, name):
        soup = BS(html)
#        image = urllib.URLopener()
        i = 0
        for imtag in soup.find_all('img'):
                link = imtag['src']
                if link[-3:] == 'gif' or link[-3:] == 'png':
                        continue
                else:
                        return urlretrieve(link, str(i) + '_' + name + '.jpg')
#                        image.retrieve(link, str(i) + '_' + name + '.jpg')
                        i += 1
def importTxt(fName):
	f = open(fName,'r')
	return f.readlines()
	
def getTags(tagList):
        newList = []
        for tag in tagList:
                if tag not in newList:
                        newList.append(tag.strip('/').strip('\n').strip('?'))
        
        return newList
                

if __name__ == '__main__':
        ##init
        ##username = raw_input("Enter the name of username of interest: ")

        #loginFacebook(driver)
        #print "assessing user: {}".format(targ)
        #uid = convertUser2ID2(driver,username)

        ##timeline
        ##html = downloadTimeline(username)
        ##html2File(html, 'timeline.html')

        ##apps used
        #html = downloadAppsUsed(driver, uid)
        #appsUsed = parseAppsUsed(html)
        #html2File(html, 'appsUsed.html')

        ##pages liked
        #html = downloadPagesLiked(driver, uid)
        #pagesLiked = parsePagesLiked(html)
        #html2File(html, 'pagesLiked.html')

        ##photos by
        #html = downloadPhotosBy(driver, uid)
        #photosBy = parsePhotosBy(html)
        #html2File(html, 'photosBy.html')

        #html = downloadPhotosOf(driver, uid)
        #photosOf = parsePhotosOf(html)
        #html2File(html, 'photosOf.html')

        #print "pausing for {} seconds...".format(s)
        #time.sleep(s)

        ######preprocess data

        ##extract images
        ##folder = 'siamakShabahang'                              #change this

        #photosOf = importHtml('photosOf.html')
        #photosBy = importHtml('photosBy.html')

        #extractPhotos(photosOf, 'photosOf' + '_' + targ)
        #extractPhotos(photosBy, 'photosBy' + '_' + targ)
        

        tags = importTxt('users.txt')
        tags = getTags(tags) 
        skipList = ['marcin.mazur.73', 'profile.php', 'abdisalam.musse', 'craig.draeger', 'paul.vee.7', 'keelin.scully', 'rita.sitar', 'jillian.mumby1', 'josh.lister.39', 'heather.lemons.3', 'bobby.ghadery', 'reza.miri.752', 'steve.bunker.777', 'rikki.alida', 'dylonsnake']
        skipInfo = ['dafne.vassetti']
        s = 3 #seconds sleep time
        count = 0
        info = {}
        if FB_SCRAPE:
                #init
                #username = raw_input("Enter the name of username of interest: ")
                driver = init_chrome()
                loginFacebook(driver)
                for targ in tags:
                        if targ in skipList + skipInfo:
                                continue
                        #print "assessing user: {}".format(targ)
                        uid = convertUser2ID2(driver,targ)
                        k = 0
                        while (uid == None or k > 10):
                                time.sleep(s)
                                uid = convertUser2ID2(driver,targ)
                                k += 1
                        if uid == None:
                                print "skipping user: {}".format(targ)
                                continue

                        #timeline
                        wrote = False
                        fTL = PATH + '/profiles/' + targ + '_timeline.html' 
                        if not os.path.isfile(fTL):
                                html = downloadTimeline(uid, driver)
                                html2File(html, fTL)
                                wrote = True

                        #apps used
                        fApps = PATH + '/appsUsed/' +targ + "_" + 'appsUsed.html'
                        if not os.path.isfile(fApps):
                                html = downloadAppsUsed(driver, uid)
                                appsUsed = parseAppsUsed(html)
                                html2File(html, fApps)
                                wrote = True

                        #pages liked
                        fPgLikes = PATH + '/likedPages/' + targ + "_" + 'pagesLiked.html'
                        if not os.path.isfile(fPgLikes):
                                html = downloadPagesLiked(driver, uid)
                                pagesLiked = parsePagesLiked(html)
                                html2File(html, fPgLikes)
                                wrote = True
                                
                        count += 1
                        print "{} profiles scanned...".format(count)
        #                #photos by
        #                html = downloadPhotosBy(driver, uid)
        #                photosBy = parsePhotosBy(html)
        #                html2File(html, targ + "_" + 'photosBy.html')

        #                html = downloadPhotosOf(driver, uid)
        #                photosOf = parsePhotosOf(html)
        #                html2File(html, targ + "_" + 'photosOf.html')
                        
                        if wrote:
                                print "pausing for {} seconds...".format(s)
                                time.sleep(s)
                                
                        #miscelaneous
                        frnds = PATH + '/miscelaneous/' + targ + '_' + 'friends.html'
                        if not os.path.isfile(frnds):
                                print "crawling {}'s friend section...".format(targ)
                                html = downloadFriends(targ, driver)
                                html2File(html, frnds)
                                
                        about = PATH + '/miscelaneous/contact_info_' + targ + '.txt'
                        if not os.path.isfile(about):
                                print "crawling {}'s about section...".format(targ)
                                contact = downloadAbout(targ, driver)
                                print "finished extracting contact information:"
                                print "saving to file..."
                                dumpFile = open(about, 'w')
                                for key in contact.keys():
                                        dumpFile.write(key + ';\n')
                                        for item in contact[key]:
                                                try:
                                                        dumpFile.write(item + '\n')
                                                except:
                                                        print "not ascii:"
                                                        print item
                                dumpFile.close()
        
#        targ = 'dylan.clark1'
#        driver = init_chrome()
#        loginFacebook(driver)                                
#        f = open(PATH + '/profiles/names.pkl','rb')
#        names = pickle.load(f)
#        f.close()
#                driver, searchBox = google_search(names(targ) + ' LinkedIn',driver)
                        #####preprocess data

                        #extract images
                        #folder = 'siamakShabahang'                              #change this

        #                photosOf = importHtml('photosOf.html')
        #                photosBy = importHtml('photosBy.html')

        #                extractPhotos(photosOf, 'photosOf' + '_' + targ)
        #                extractPhotos(photosBy, 'photosBy' + '_' + targ)
        G = fb_graph(tags)
         
        display.stop()
