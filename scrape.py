import xlwt
from bs4 import BeautifulSoup
import re
import os
import pickle

PATH = os.getcwd()

def likedAnalys(dataDic):
        users = dataDic.keys()
        catList = []
        likedList = []
        for user in users:
                categories = dataDic[user]
                for category in categories.keys():
                        if category not in catList:
                                catList.append(category) 
                        likes = categories[category]
                        for like in likes:
                                if like not in likedList:
                                        likedList.append(like)
                
        return catList, likedList
        
def likedCatMat(data, catLbls):
        catMat = []
        users = []
        for user in data.keys():
                users.append(user)
                catVec = np.zeros(len(catsLbls))
                likeCats = data[user].keys()
                for i in range(len(catLbls)):
                        if catLbls[i] in likeCats:
                                catVec[i] = 1
                catMat.append(catVec)
                                
        return np.array(catMat), users
        
def likedMat(data, likedLbls):
        likedMat = []
        for user in data.keys():
                print "Extracting liked vector from {}".format(user)
                cats = data[user]
                likedVec = np.zeros(len(likedLbls))
                for cat in cats.keys():
                        liked = cats[cat]
                        for like in liked:
                                i = revIndx(likedLbls, like)
                                likedVec[i] = 1
                likedMat.append(likedVec)
                
        return np.array(likedMat)

def importHtml(fName):
	f = open(fName,'r')
	return f.read()
	
def importTxt(fName):
	f = open(fName,'r')
	return f.readlines()
	
def wt2Exl(fName, data):
        book = xlwt.Workbook(encoding='utf-8')
        sheet1 = book.add_sheet("sheet 1")
        for i in range(len(data)):
                for j in range(len(data[i])):
                        sheet1.write(i,j,data[i][j])
        book.save(fName)

def removeNums(string):
        nums = ['0','1','2','3','4','5','6','7','9','.','(',')',' ']
        newChar = ''
        for char in string:
                if char not in nums:
                        newChar = newChar + char
                        
        return newChar
	
def getTags(tagList):
        newList = []
        for tag in tagList:
                if tag not in newList:
                        newList.append(tag.strip('/').strip('\n').strip('?'))
        
        return newList
	
def cleanTxt(string):
	allowed = '0 1 2 3 4 5 6 7 8 9 a b c d e f g h i j k l m n o p q r s t u v w x y z :'.split()
	clean = ''
	for char in string:
		if char.lower() in allowed:
			clean += char
	return clean
	
def frnds(html):
        frnds = []
        soup = BeautifulSoup(html)
        timelineItem = soup.find_all("div", {"class":"fsl"})
        for item in timelineItem:
                link = item.find_all('a')[0]
                frnds.append(link.get('href'))
                print link.get('href')
        
        return frnds
	
def statuses(html):
	statuses = []
	soup = BeautifulSoup(html)
	print soup
	timelineItem = soup.find_all("div", {"class":"userContentWrapper"})
	print timelineItem
	for item in timelineItem:
		post = item.find_all("span", {"class":"userContent"})
		sentBy = item.find_all("span", {"class":"fwb"}, "a")
		if len(post) == 1:
			string = str(sentBy)
			postIDs = re.findall('\d\d\d+',string)
			if len(postIDs) == 1:
				timePr = item.find_all("abbr")
				time = re.findall('[MTWFS].*[pa]m\">', str(timePr))
				post = re.findall('>.*<',str(post))
				if len(post[0]) > 3 and 'http' not in post[0]:
					print "-"*20
					print post[0]
					statuses.append([post[0],time[0]])
					print '\n'
					print time[0]
					print '\n'
	return statuses, timelineItem
	
def pgsLiked(html):
        pgsLiked = {}
        soup = BeautifulSoup(html)
        likedItem = soup.find_all("div",{"class":"_5d-5"})
        categories = soup.find_all("div",{"class":"_glm"})
        i = 0
        for item in likedItem:
                category = categories[i]
                category = category.text.encode('ascii','ignore')
                category = removeNums(category)
                itm = item.text.encode('ascii','ignore')
                if not itm.isspace() and len(itm) > 1:
                        if category not in pgsLiked:
                                pgsLiked[category] = [itm]
                        else:
                                pgsLiked[category].append(itm)
                
#		post = item.find_all("span", {"class":"userContent"})
#		sentBy = item.find_all("span", {"class":"fwb"}, "a")profiles/kennethda1990_timeline.html
#		if len(post) == 1:
#			string = str(sentBy)
#			postIDs = re.findall('\d\d\d+',string)
#			if len(postIDs) == 1:
#				timePr = item.find_all("abbr")
#				time = re.findall('[MTWFS].*[pa]m\">', str(timePr))
#				post = re.findall('>.*<',str(post))
#				if len(post[0]) > 3 and 'http' not in post[0]:
#					print "-"*20
#					print post[0]
#					statuses.append([post[0],time[0]])reza.miri.752
#					print '\n'
#					print time[0]
#					print '\n'
                i += 1
                
        return pgsLiked

if __name__ == '__main__':
        extractBigEvents = False
        getNames = True
        users = getTags(importTxt('users.txt'))
#        for user in users[0:1]:
#                profile = importHtml(PATH + '/profiles/' + user + '_timeline.html')
#                statuses, tl = statuses(profile)
        skipList = ['marcin.mazur.73', 'profile.php', 'abdisalam.musse', 'craig.draeger', 'paul.vee.7', 'keelin.scully', 'rita.sitar', 'jillian.mumby1', 'josh.lister.39', 'heather.lemons.3', 'bobby.ghadery', 'reza.miri.752', 'steve.bunker.777', 'rikki.alida', 'dylonsnake']
        count = 0
        mjEvents = {}
        dlComlplete = {}
        names = {}
        for user in users:
                if user in skipList:
                        continue               
                count += 1
                if os.path.isfile(PATH + '/profiles/statuses' + user + '.pkl'):
                        print "user, {}, is already stored".format(user)
                else:
                        print "extracting status update information from: {}".format(user)
                        statusUpdates = {}
                        html = importHtml(PATH + '/profiles/' + user + '_timeline.html')
                        soup = BeautifulSoup(html)
                        name = soup.find_all("span", {"id":"fb-timeline-cover-name"})[0].text
                        timelineItems = soup.find_all("div", {"class":"userContentWrapper"})
                        for timelineItem in timelineItems:
                                sentBy = timelineItem.find_all("span", {"class":"fwb"})
                                if len(sentBy) > 0:
                                        sentBy = sentBy[0].text
                                timeSent = timelineItem.find_all("abbr", {"class":"_5ptz"})
                                if len(timeSent) > 0:
                                        timeSent = str(timeSent[0])
                                        timeSent = re.search('le=\".*\"', timeSent)
                                        if timeSent != None:
                                                timeSent = timeSent.group(0)
                                                timeSent = timeSent.strip('le=')
                                                timeSent = timeSent.strip('\"')
        #                                        timeSent = timeSent.split(' ')
                                content = timelineItem.find_all("div",{"class":"_5pbx"})
                                if len(content) > 0:
                                        content = content[0].text
                                assert(timeSent != None and sentBy != None and content != None)
                                if sentBy == []:
                                        sentBy = '&'
                                if timeSent == []:
                                        timeSent = '&'
                                statusUpdates[user + '_' + timeSent + '_' + sentBy] = content
                        dumpFile = open(PATH + '/profiles/statuses' + user + '.pkl','wr')
                        pickle.dump(statusUpdates, dumpFile)
                        dumpFile.close()
                        print "{} status updates stored from user {}".format(len(statusUpdates),user)
                        print "{} users stored so far".format(count)
                
                if extractBigEvents:
                        print "checking if {}\'s html file fully completed".format(user)
                        html = importHtml(PATH + '/profiles/' + user + '_timeline.html')
                        soup = BeautifulSoup(html)
                        bigEvents = soup.find_all("a",{"class":"uiLinkDark"})
                        completed = False
                        try:
                                if bigEvents[-1].text == 'Born':
                                        completed = True
                        except:
                                completed = False
                                
                        print "complete: {}".format(completed)                                
                        
                        print "extracting major events"
                        if bigEvents != None:
                                events = []
                                for event in bigEvents:
                                        events.append(event.text)
                                
                                mjEvents[user] = events
                                dlComlplete[user] = completed
                                print events
                        dumpFile = open(PATH + '/profiles/events.pkl','w')
                        pickle.dump(events,dumpFile)
                        dumpFile.close()
                        
                        dumpFile = open(PATH + '/profiles/completion.pkl', 'w')
                        pickle.dump(dlComlplete, dumpFile)
                        dumpFile.close()
                
                if getNames:
                        print "getting the name of user {}...".format(user)
                        html = importHtml(PATH + '/profiles/' + user + '_timeline.html')
                        soup = BeautifulSoup(html)
                        soup = soup.find_all("a",{"class":"_8_2"})[0]
                        soup = soup.find_all("span",{"id":"fb-timeline-cover-name"})[0]
                        names[user] = soup.text
                        try:
                                print "name found: {}".format(soup.text)
                        except:
                                continue
        if getNames:
                dumpFile = open(PATH + '/profiles/names.pkl','w')
                pickle.dump(names, dumpFile)
                dumpFile.close()
        
#data = {}
#for targ in tags:book.com/
#        try:
#                html = importHtml(PATH + '/likedPages/' + targ + '_' + 'pagesLiked.html')
#                print "processing {}".format(targ)
#        except:
#                print "{} not found".format(targ)
#                continue
#        data[targ] = pgsLiked(html)

#        users = data.keys()
#        dataNew = {}
#        for user in users:
#                if len(data[user]) > 0:
#                        dataNew[user] = data[user]
#                              
#        data = dataNew

#catsLbls, likedLbls = likedAnalys(data)
#catMat, users = likedCatMat(data, catsLbls)
#catMatNormed = catMat/catMat.sum(axis = 0)
#caseMatNormed = catMatNormed.T/catMatNormed.sum(axis=1)
#normedCat = caseMatNormed.T

#likedMat = likedMat(data, likedLbls)
#likedMatNormed = likedMat/likedMat.sum(axis=0)
#likedMatNormed = likedMatNormed.T/likedMatNormed.sum(axis=1)
#normedLiked = likedMatNormed.T
#        
##with open(PATH + '/data/users.txt','w') as f:
##        pickle.dump(users,f)

#np.save(PATH + '/data/normedCat',normedCat)
#np.save(PATH + '/data/normedLiked',normedLiked)

