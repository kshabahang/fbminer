from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial.distance import cdist, pdist
from bintrees import RBTree
import pickle
import numpy as np
from scipy.spatial import distance
from matplotlib import pyplot as plt
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans, DBSCAN
import os
from scipy.stats import pearsonr
import enchant
import scipy as sp
import pylab
from pylab import *
PATH = os.getcwd()
from psychopy.core import Clock
from wordcloud import WordCloud, STOPWORDS

def feature_dimension_fit(matrix, k_range, fName = None):
        Var = []
        timer = Clock()
        for k in k_range:
                print "Reducing feature-rank to {}".format(k)
                timer.reset()
                Rn = TruncatedSVD(n_components = k, random_state = 42).fit(matrix)
                t = timer.getTime()
                Var.append([k,sum(Rn.explained_variance_ratio_)*100,t])
                print "processing time (s): {}".format(t)
        Var = np.array(Var)
        if fName != None:
                plt.plot(Var.T[0],Var.T[1])
                plt.ylabel("%variance")
                plt.xlabel("dimension in feature space")
                plt.savefig(fName)
                plt.show()
        return Var, Rn
                

def scatter3d(data, categories = None):
        fig = pylab.figure()
        ax = Axes3D(fig)
        ax.scatter(data[0],data[1],data[2])
        plt.show()

def importTxt(fName):
	f = open(fName,'r')
	return f.readlines()
	
def getTags(tagList):
        newList = []
        for tag in tagList:
                if tag not in newList:
                        newList.append(tag.strip('/').strip('\n').strip('?'))
        
        return newList
                

def revIndx(searchList, token):
        for i in range(len(searchList)):
                if searchList[i] == token:
                        return i
                        
def vectorize():
        pass
                        
def simScores(matrix, user, users):
        index = revIndx(users, user)
        vector = matrix[index]
        scores = RBTree()
        for i in range(len(matrix)):
                if index == i:
                        pass
                        sim = 0
                        scores[round(sim,10)] = users[i]
                else:
                        sim = matrix[i].dot(vector)
        #                sim = distance.cosine(normed[i],vector)
                        scores[round(sim,10)] = users[i]
        return scores
        
def nthLargest(scores):
        nthLargest = []
        for similar in scores.nlargest(50):
                print "\n"
                print similar
                userData = data[similar[1]]
                count = 0
                print "{} categories".format(len(userData))
                if len(userData) < len(currentUserData):
                        for category in userData.keys():
                                if category in currentUserData.keys():
                                        shared = []
                                        for item in userData[category]:
                                                if item in userData[category]:
                                                        shared.append(item)
                                        if len(shared) > 0:
                                                print "shared category: {}".format(category)
                                                count += len(shared)
                                                for page in shared:
                                                        print page
                else:
                        for category in currentUserData.keys():
                                if category in userData.keys():
                                        shared = []
                                        for item in currentUserData[category]:
                                                if item in userData[category]:
                                                        shared.append(item)
                                                        count += len(shared)
                                        if len(shared) > 0:
                                                print "shared category: {}".format(category)
                                                for page in shared:
                                                        print page
                print "total pages in common: {}".format(count)
                #nthLargest.append([similar[0], count])
                nthLargest = np.array(nthLargest)
                
                return nthLargest
                
def makeWordCloud(text):
	#preprocess
	stopwords = STOPWORDS.copy()
#        text.replace("State","")
#        text.replace("year","")
#        text.replace("Congress","")
#        text.replace("will","")
	wC = WordCloud(max_words=2000, stopwords=stopwords, margin=5, random_state=1, width = 1600, height = 800).generate(text)
	plt.imshow(wC)
	plt.show()
                
#######Clustering###
def kMeansEval(X, k_range, fName = None):
#        print "running K-Means Algorithm with {} clusters...".format(k_range)
#        kMeansVar = [KMeans(n_clusters=k).fit(X) for k in k_range]
#        centroids = [x.cluster_centers_ for x in kMeansVar]
        kMeansVar = []
        centroids = []
#        time = []
        h1, = plt.plot([],[])
        
#        clk = clock.Clock()
        for k in k_range:
#                clk.reset()
                model = KMeans(n_clusters = k).fit(X)
#                t = clk.getTime()
                #print "Run Summary {} clusters in {} mscs".format(k, t)
                kMeansVar.append(model.fit(X))
                centroids.append(model.cluster_centers_)
#                time.append(t)
        
#        #using variance as a performance measure (adapted from Sarah Guido)
        
        k_euclid = [cdist(X, cent, 'euclidean') for cent in centroids]
        dist = [np.min(ke, axis = 1) for ke in k_euclid]
        SSwithin = [sum(d**2) for d in dist]
        SStotal = sum(pdist(X)**2)/X.shape[0]
        SSbetween = SStotal - SSwithin
        variance = SSbetween/SStotal
        if fName != None:
                fName = 'kMeansCluster.png'
                plt.plot(variance)
                plt.xlabel('K clusters')
                plt.ylabel("SSbetween/SStotal")
                plt.text(len(variance)/2, 0.3, "% max(Var): {} ".format(max(variance)), verticalalignment='center')
                plt.savefig(fName)
                plt.show()
        #time
#        plt.plot([x for x in range(1,len(time))],time)
#        plt.xlabel('K clusters')
#        plt.ylabel('Time (secs)')
#        plt.show()

        return variance#, time

def dbScan(X, k_range, fName = None):
#        print "running K-Means Algorithm with {} clusters...".format(k_range)
#        kMeansVar = [KMeans(n_clusters=k).fit(X) for k in k_range]
#        centroids = [x.cluster_centers_ for x in kMeansVar]
        DBSCANVar = []
        centroids = []
#        time = []
        h1, = plt.plot([],[])
        
#        clk = clock.Clock()
        for k in k_range:
#                clk.reset()
                model = DBSCAN(eps = 0.05, min_samples=2).fit(X)
#                t = clk.getTime()
                #print "Run Summary {} clusters in {} mscs".format(k, t)
                DBSCANVar.append(model.fit(X))
                centroids.append(model.cluster_centers_)
#                time.append(t)
        
#        #using variance as a performance measure (adapted from Sarah Guido)
        
        k_euclid = [cdist(X, cent, 'euclidean') for cent in centroids]
        dist = [np.min(ke, axis = 1) for ke in k_euclid]
        SSwithin = [sum(d**2) for d in dist]
        SStotal = sum(pdist(X)**2)/X.shape[0]
        SSbetween = SStotal - SSwithin
        variance = SSbetween/SStotal
        if fName != None:
                fName = 'kMeansCluster.png'
                plt.plot(variance)
                plt.xlabel('K clusters')
                plt.ylabel("SSbetween/SStotal")
                plt.text(len(variance)/2, 0.3, "% max(Var): {} ".format(max(variance)), verticalalignment='center')
                plt.savefig(fName)
                plt.show()
        #time
#        plt.plot([x for x in range(1,len(time))],time)
#        plt.xlabel('K clusters')
#        plt.ylabel('Time (secs)')
#        plt.show()

        return variance#, time
#######MAIN#########
#import tags
tags = importTxt('users.txt')
tags = getTags(tags)

skipList = ['marcin.mazur.73', 'profile.php', 'abdisalam.musse', 'craig.draeger', 'paul.vee.7', 'keelin.scully', 'rita.sitar', 'jillian.mumby1', 'josh.lister.39', 'heather.lemons.3', 'bobby.ghadery', 'reza.miri.752', 'steve.bunker.777', 'rikki.alida', 'dylonsnake']

print "opening status data from file..."
if not os.path.isfile(PATH + '/cleanPosts.pkl'):
        print "extracting posts"
        data = {}
        #dumpFile = open(PATH + '/profiles/events.pkl','rb')
        #events = pickle.load(dumpFile)
        #dumFile.close()
        dumpFile = open(PATH + '/profiles/completion.pkl', 'rb')
        profileDlComplete = pickle.load(dumpFile)
        dumpFile.close()
        dumpFile = open(PATH + '/profiles/names.pkl', 'rb')
        names = pickle.load(dumpFile)
        dumpFile.close()
        for tag in tags:
                if tag not in skipList:
                        dumpFile = open(PATH + '/profiles/statuses' + tag + '.pkl','rb')
                        data[tag] = pickle.load(dumpFile)
                        dumpFile.close()
        statuses = {}
        d = enchant.Dict("en_US")
        ownPost = {}
        for user in data.keys():
                print "User: {}; number of status records: {}".format(user, len(data[user]))
                n = len(data[user])
                posts = {}
                if len(data[user]) > 100:
                        statuses[user] = data[user]
                        for status in statuses[user].keys():
                                components = status.split('_')
                                current = components[0]
                                date = components[1]
                                convo = components[2]
                                content = statuses[user][status]
                                nm = names[user]
                                if len(nm) == len(convo):
                                        #own post
        #                                print "own post"
                                        posts[status] = content
                                else:
                                        if convo[0:len(nm)] == nm:
        #                                        print "other: {}"
                                                print convo
                                        elif convo[-len(nm):] == nm:
        #                                        print "other:"
                                                print convo
        #                                else:
        #                                        print "no match"
                        if len(posts) > 0:
                                ownPost[user] = posts
        print "cleaning posts..."
        illegal = '! ? # @ % & * ( ) > < | { } [ ] ; , .'.split(' ')
        percentExtracted = {}
        allCleanPosts = {}
        for user in ownPost.keys():
                posts = ownPost[user]
                extractedN = 0
                cleanPosts = {}
                for post in posts.keys():
                        content = posts[post]
                        if len(content) > 0:
                                text = content.split(' ')
                                isEnglish = []
                                clean = []
                                for token in text:
                                        for character in illegal:
                                                token = token.strip(character)
                                        try:
                                                isWord = d.check(token)
                                                isEnglish.append(isWord)
                                                clean.append(token)
                                        except:
                                                isEnglish.append(False)
                                percentEnglish = (sum(isEnglish)/float(len(text)))*100
                                if not (percentEnglish < 10 and len(text) > 2):
                                        extractedN += 1
                                        cleanPosts[post] = clean
                allCleanPosts[user] = cleanPosts
                percentExtracted[user] = extractedN/float(len(posts))
        dumpFile = open(PATH + '/cleanPosts.pkl', 'w')
        pickle.dump(allCleanPosts, dumpFile)
        dumpFile.close()
else:
        print "loading posts from file..."
        dumpFile = open(PATH + '/cleanPosts.pkl', 'rb')
        allCleanPosts = pickle.load(dumpFile)
        dumpFile.close()
        
        
if not os.path.isfile(PATH + '/uniqueTokens.pkl'):
        print "beginning vectorization..."
        uniqueTokens = []
        token2i = {} #maps tokens to indices 
        i = 0
        for user in allCleanPosts.keys():
                posts = allCleanPosts[user]
                for post in posts.keys():
                        content = posts[post]
                        for token in content:
                                if token not in uniqueTokens:
                                        uniqueTokens.append(token)
                                        token2i[token] = i
                                        i += 1
        dumpFile = open(PATH + '/uniqueTokens.pkl', 'w')
        pickle.dump(uniqueTokens, dumpFile)
        dumpFile.close()
        dumpFile = open(PATH + '/uniqueTokensMap.pkl', 'w')
        pickle.dump(token2i, dumpFile)
        dumpFile.close()
else:
        print "loading token vector..."
        dumpFile = open(PATH + '/uniqueTokens.pkl', 'rb')
        uniqueTokens = pickle.load(dumpFile)
        dumpFile.close()
        
        dumpFile = open(PATH + '/uniqueTokensMap.pkl', 'rb')
        uniqueTokensMap = pickle.load(dumpFile)
        dumpFile.close()

if not os.path.isfile(PATH + '/personBytokenMat.pkl'):
        print "extracting person-by-token matrix"
        matrix = []
        users = []
        for user in allCleanPosts.keys():
                vector = np.zeros(len(uniqueTokens))
                posts = allCleanPosts[user]
                for post in posts.keys():
                        for token in posts[post]:
                                i = uniqueTokensMap[token]
                                vector[i] += 1
                matrix.append(vector)
                users.append(user)
        dumpFile = open(PATH + '/personBytokenMat.pkl', 'w')
        pickle.dump(matrix, dumpFile)
        dumpFile.close()
        dumpFile = open(PATH + '/personBytokenUsers.pkl', 'w')
        pickle.dump(users, dumpFile)
        dumpFile.close()
else:
        print "loading person-by-token matrix..."
        dumpFile = open(PATH + '/personBytokenMat.pkl', 'r')
        matrix = pickle.load(dumpFile)
        dumpFile.close()
        dumpFile = open(PATH + '/personBytokenUsers.pkl', 'r')
        users = pickle.load(dumpFile)
        dumpFile.close()
        


feature_rank = 283
if not os.path.isfile(PATH + '/RawMatrix.npy'):
        print "removing features with frequency = 1..."
        discarded = 0
        i2key = {}
        keys = uniqueTokensMap.keys()
        for i in range(len(keys)):
                i2key[i] = keys[i]
        matrix = np.array(matrix)
        newMat = []
        print "remove features"
        tokenSums = matrix.sum(axis=0)
        matrix = matrix.T
        for i in range(len(tokenSums)):
                if tokenSums[i] > 1:
                        newMat.append(matrix[i])
                else:
                        print "discarding token:"
                        print i2key[i]
                        discarded += 1
                        
        matrix = np.array(newMat)
        matrix = matrix.T
        print "discarded {} items".format(discarded)
        np.save(PATH + '/RawMatrix', matrix)
        tokenSums = matrix.sum(axis=0)
        subjectSums = matrix.sum(axis=1)
        normalized = matrix/tokenSums
        normalized = normalized.T/subjectSums
        normalized = normalized.T
        normalized = np.nan_to_num(normalized)
else:
        print "loading raw matrix after initial feature-reduction.."
        matrix = np.load(PATH + '/RawMatrix.npy')
        tokenSums = matrix.sum(axis=0)
        subjectSums = matrix.sum(axis=1)
        normalized = matrix/tokenSums
        normalized = normalized.T/subjectSums
        normalized = normalized.T
        normalized = np.nan_to_num(normalized)
        
if not os.path.isfile(PATH + '/SVDRankReduced.npy'):
        print "reducing the rank of the matrix in the feature-space"
        R3 = TruncatedSVD(n_components = 3, random_state = 42).fit(normalized.T)
        print "matrix size: {}x{}".format(normalized.shape[0],normalized.shape[1])
        var, svd = feature_dimension_fit(normalized.T, range(1,80), 'feature_space_rank.png')
        rank = 80
        print "reducing rank of the matrix to {} in the feature-space".format(rank)
        rankReduced = TruncatedSVD(n_components = rank, random_state = 42).fit(normalized.T)
        rankReduced = rankReduced.components_
        np.save(PATH + '/SVDRankReduced', rankReduced)
else:
        print "loading rank-reduced matrix..."
        rankReduced = np.load(PATH + '/SVDRankReduced.npy')
        

#var = dbScan(rankReduced.T, range(1,10), fName = 'kMeansClustering.png')
#        
target = 'alex.duncan.9083477'
print "checking similarity scores for user: {}".format(target)
scores = simScores(rankReduced.T, target, users)



#htmlTags = importHtml("DariusShabster.html")
#frndURLs = frnds(htmlTags)

#data = pickle.load(open(PATH + "/data/dataDic.p","rb"))
#normedCat = np.load(PATH + '/data/normedCat.npy')
#normedLiked = np.load(PATH + '/data/normedLiked.npy')
#users = pickle.load(open(PATH + '/data/users', 'rb'))

#simDists = {}
#for target in users:
#target = 'siamal.sh'
#index = revIndx(users,target)
#vector = normedLiked[index]
#              
#svd = TruncatedSVD(n_components = 1024, random_state = 42)
#rankReduced = svd.fit_transform(normedLiked)
#scores = simScores(normedLiked, target, users)

#highSim = {}
#lowSim = {}

#keys = scores.keys()
#listForm = [[key,scores[key]] for key in keys]


#for user in scores.keys():
#        vals = scores.values()
#        if scores[user] >= np.mean(vals) + np.std(vals):
#                print "based on categories {} is very similar to {}".format(target, user)
#                highSim[user] = scores[user]
#for user in scores.keys():
#        vals = scores.values()
#        if scores[user] <= np.mean(vals) - 0.35*np.std(vals):
#                print "based on categories {} is very different from {}".format(target, user)
#                lowSim[user] = scores[user]

#plt.bar(range(len(highSim)), highSim.values(), align='center')
#plt.xticks(range(len(highSim)), highSim.keys(), rotation=25)
#plt.show()

#plt.bar(range(len(lowSim)), lowSim.values(), align='center')
#plt.xticks(range(len(lowSim)), lowSim.keys(), rotation=25)
#plt.show()
#A = data[target]
#for simUser in highSim.keys():
#        B = data[simUser]
#        if len(A) > len(B):
#                for category in B.keys():
#                        if category in A.keys():
#                                aLikes = A[category]
#                                bLikes = B[category]
#                                for item in aLikes:
#                                        if item in bLikes:
#                                                print "{} and {} both like {}".format(target, user, item)
#        else:
#                for category in A.keys():
#                        if category in B.keys():
#                                aLikes = A[category]
#                                bLikes = B[category]
#                                for item in aLikes:
#                                        if item in bLikes:
#                                                print "{} and {} both like {}".format(target, user, item)
#simDists[target] = vals
#plt.hist(vals)
#plt.savefig(target + '.png')
#plt.close()
#currentUserData = data[target]
#print "current user has {} like categories".format(len(currentUserData))
#simMat = np.array(simDists.values())
#print "User: {}".format(target)
#print "most similar"

#nthLargest = nthLargest(scores)

#plt.plot(nthLargest.T[0], nthLargest.T[1])
#plt.show()



#print pearsonr(nthLargest.T[0], nthLargest.T[1])

#nth = 1        
#print "nmost dissimilar" 
#for dissimilar in scores.nsmallest(5):
#        print "\n"
#        print dissimilar
#        userData = data[dissimilar[1]]
#        print "{} categories".format(len(userData))
#        if len(userData) < len(currentUserData):
#                for category in userData.keys():
#                        if category in userData.keys():
#                                shared = []
#                                for item in currentUserData[category]:
#                                        if item in userData[category]:
#                                                shared.append(item)
#                                if len(shared) > 0:
#                                        print "shared category: {}".format(category)
#                                        for page in shared:
#                                                print page
#        else:
#                for category in currentUserData.keys():
#                        if category in userData.keys():
#                                shared = []
#                                for item in currentUserData[category]:
#                                        if item in userData[category]:
#                                                shared.append(item)
#                                if len(shared) > 0:
#                                        print "shared category: {}".format(category)
#                                        for page in shared:
#                                                print page

