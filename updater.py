import requests
import json
import config
import os
import time
playerId = 20404838
baseURL = "https://na.api.pvp.net"
keyURL = "?api_key=" + config.key
getChampsURL = "/api/lol/static-data/na/v1.2/champion"
latestTime = 0
dataResponse = {}
champIdMap = {}
PLAYER = {"teamId": 0, "championId" : 0}

class Worker():
	"""Used to scrape URF data at regular intervals and save them to disk for later use"""

	def __init__(self, startTime):
		"""Start time is a valid long in EPOCH time. This time must be a number that corresponds to an exact 5-minute time
		For example, 11:05 (converted to EPOCh time) is valid, but 11:04 is not
		"""
		self.latestTime = int(startTime)
		self.keyURL = "?api_key=" + config.key
		self.matchQueue = [] #this is a list of tuples (matchId, timeBucket)
		print "Initialized Worker. Starting to scrape..."

	def getNewMatchList(self):
		"""We update self.matchQueue with the current results found at time self.latestTime
		Returns True upon a success and False otherwise"""
		try:
			pipe = requests.get("https://na.api.pvp.net/api/lol/na/v4.1/game/ids" + self.keyURL + "&beginDate=" + str(self.latestTime))
			self.matchQueue = self.matchQueue + map(lambda x: (x, self.latestTime), pipe.json())
			print "Added new data for time " + str(self.latestTime)
			return True
		except:
			print "Failed to get a new match list for time: " + str(self.latestTime)
			return False


	def getDay(self):
		"""Returns a string of the form [dayOfYearAsInt]_[YYYY]"""
		tm = time.localtime()
		return str(tm.tm_yday) + "_" + str(tm.tm_year)

	def updateTime(self):
		self.latestTime +=300

	def currentTime(self):
		return int(time.time())

	def writeMatch(self, matchId, day, tm):
		"""
		Writes '[matchId].json' to the directory [day] and subdirectory [tm]
		If the directories do not exist they are created.
		[day] should be a string without whitespace
		[tm] should be a string without whitespace
		"""
		path = os.path.join("data",day, tm)
		fileLocation = os.path.join(path, str(matchId)+'.json')
		#if not os.path.exists("data"):
		#	os.makedirs("data")
		#if not os.path.exists(day):
		#	os.makedirs(day)
		if not os.path.exists(path):
			os.makedirs(path)
		with open(fileLocation, 'wb') as temp_file:
			try:
				json.dump(getNewMatch(matchId), temp_file)
				print "Successfully wrote match " + str(matchId)
			except:
				print "Writing Match " + str(matchId) + " Failed."
				pass

	def updateInformation(self):
		"""Verifies that we do not need to update our matchQueue. If an udate is in order, update the matchQueue.
		After updating, we process a single element from the matchQueue. We assume this function is called with an adequate politeness policy (3 seconds between calls)"""
		#If our current time more than 25 minutes after the latest time, update 
		if self.currentTime() > self.latestTime + 1500 and self.getNewMatchList():
			self.updateTime()
			print "Queue Size is now " + str(len(self.matchQueue))
		if len(self.matchQueue) > 0:
			(matchId, tm) = self.matchQueue.pop(0)
			self.writeMatch(matchId, self.getDay(), str(tm))


		
def createMaps(validExtensions=[".json"]):
	allyMap = {}
	opponentMap = {}
	picMap = {}
	prefixMap = {}
	itemMap = getItemMap()
	champToItemsMap = {}
	refMap = getChampMapByKeys()
	refMap["Wukong"] = refMap["MonkeyKing"]
	refMap = createLowerCaseKeys(refMap)
	mainMap = getChampMap()

	#add a key for wukong
	
	for root, dirs, files in os.walk("."):
	    for name in files:
	    	key = os.path.join(root, name).replace("\\","/")
	        fileName, fileExtension = os.path.splitext(key)
	        if fileExtension.lower() in validExtensions:
				fileR = {}
				try:
					with open(key) as data_file:    
						fileR = json.load(data_file)
					updateMaps(fileR, allyMap, opponentMap, champToItemsMap)
				except:
					print "Failed to read " + key
					fileR = {}
	for champId in allyMap:
		picMap[str(champId)] = getChampPicture(str(champId), mainMap, False)
	prefixMap = createChampPrefixMap(refMap)

	with open('itemstats.json', 'wb') as data_file:
		json.dump(champToItemsMap, data_file)
	with open('imgData.json', 'wb') as data_file:
		json.dump(createItemMap(itemMap), data_file)
	with open('pmap.json', 'wb') as data_file:
		json.dump(prefixMap, data_file)
	with open('searchData.json', 'wb') as data_file:
		json.dump(refMap, data_file)
	with open('allies.json', 'wb') as data_file:
		json.dump(allyMap, data_file)
	with open('opponents.json', 'wb') as data_file:
		json.dump(opponentMap, data_file)
	with open('pictures.json', 'wb') as data_file:
		json.dump(picMap, data_file)

def createItemMap(itemMap):
	"""Returns a smaller version of itemMap with global image locations"""
	newMap = {}
	for key in itemMap['data']:
		newMap[key] = {'id': itemMap['data'][key]['id'], 'name': itemMap['data'][key]['name'], 'image': getItemPicture(key, itemMap)}
	return newMap

def createLowerCaseKeys(mapWithKeys):
	"""We return a copy of mapWithKeys with lower-case keys, mapping from keys to a name, title, key, and id"""
	newMapWithKeys = {}
	for word in mapWithKeys:
		champ = mapWithKeys[word]
		newMapWithKeys[word.lower()] = {'name': champ['name'], 'title': champ['title'], 'key': champ['key'], 'id': champ['id'] }
	return newMapWithKeys

def createChampPrefixMap(mapWithKeys):
	"""Returns a prefix map containing the words (keys) of [mapWithKeys]
		"""
	pmap = {}
	
	for word in mapWithKeys:
		pmap_add_word(pmap, word.lower())
	return pmap

def pmap_add_word(pmap, word):
        """Adds a single word to a prefix map."""
        
        for index in range(len(word)+1):
            key = word[:index]
            nextletter = word[index] if index < len(word) else ''
            if(key in pmap):
                if(nextletter not in pmap[key]):
                    pmap[key].append(nextletter)
            else:
                pmap[key] = [nextletter]


def match(pmap, template,guessedletters):
	"""Returns the list of all valid words that match the given template.
	template: A template for a single word containing letters and '_', where '_' denotes
	an unknown character.
	guessedletters is a string containing all letters  guessed in this session"""
	return match_helper(pmap,'',template, guessedletters)


def match_helper(pmap, prefix,template, guessedletters):
	"""Returns the list of all valid words that start with the given prefix, and
	whose remaining letters match the given template."""
	if prefix not in pmap:
		return []
	if template == "":
		return [prefix] if "" in pmap[prefix] else []
	if template[0] != "_":
		return match_helper(prefix+template[0], template[1:], guessedletters)
	acc=[]
	for nextletter in pmap[prefix]:
		if nextletter != "" and nextletter not in guessedletters:
			acc += match_helper(prefix+nextletter, template[1:], guessedletters)
	return acc

def updateMaps(matchMap, friendMap, opponentMap, champItemsMap):
	"""Given a matchMap representing a valid game, updates friendArray and opponentArray in place given the 10
	champions in the game. 
	"""
	AChamps = []
	BChamps = []
	for champ in matchMap['participants']:
		updateItems(champ, champItemsMap)
		if champ['teamId'] ==100:
			AChamps.append(champ['championId'])
		else:
			BChamps.append(champ['championId'])
	updateAllies(AChamps, friendMap)
	updateAllies(BChamps, friendMap)
	updateOpponents(AChamps, BChamps, opponentMap)

def updateItems(champ, champItemsMap):
	for slot in range(0, 6):
		currentItem = champ['stats']['item'  + str(slot)]
		if currentItem !=0:
			updateMapKey(champ['championId'], currentItem, champItemsMap)

def updateOpponents(Alist, Blist, opponentMap):
	for champ in Alist:
		for enemy in Blist:
			updateMapKey(champ, enemy, opponentMap)
			updateMapKey(enemy, champ, opponentMap)


def updateAllies(friendList, friendMap):
	for champ in friendList:
		for ally in friendList:
			if ally is not champ:
				updateMapKey(champ, ally, friendMap)

def updateMapKey(initkey, key, map):
	"""Increases the value of map[key] by 1. If map[key] does not exist, map[key] is given a value of 1"""
	if initkey not in map:
		map[initkey] = {}
	if key not in map[initkey]:
		map[initkey][key] = 0
	map[initkey][key] = map[initkey][key] +1
	



def updateMatch():
	""" Makes a GET call to the Riot API to verify that the most recent game in which playerId died
	was not the game contained in matchId

	If the most recent game in which playerId died is a different game,matchId is updated with the new value

	The global variable matchId is updated with the ID of the most recent match
	The global variable PLAYER is updated with the ID of the player's team and their champion ID

	RETURNS: True if matchid.txt is updated with a new ID, False otherwise"""
	global matchId
	global PLAYER
	global keyURL
	try:
		pipe = requests.get("https://na.api.pvp.net/api/lol/na/v1.3/game/by-summoner/"+ str(playerId)+"/recent" + keyURL)
		wrapperMap = pipe.json()
		for game in wrapperMap["games"]:
			if 'numDeaths' in game['stats'] and game['stats']['numDeaths'] > 0:
				if game['gameId']!= matchId:
					#Update the cache, returns true
					matchId = game['gameId']
					PLAYER['teamId'] = game['teamId']
					PLAYER['championId'] = game['championId']
					return True
				else:
					return False
	except:
		print 'Failed to update match data.'
		#assume that nothing changed
		pass
	return False


def getMatchData():
	"""Updates the global variable "dataResponse" with the string representation of a dictionary containing time and image data
	If any requests fail, "dataResponse" and "matchId" are left unchanged"""
	global matchId
	global PLAYER
	global champIdMap
	global dataResponse
	oldId = matchId
	sendBack = {}
	if updateMatch():
		try:
			timelineData = getNewMatch(matchId)
			deathData = getDeathInfo(timelineData, PLAYER)
			#Set match time:
			sendBack["deathTime"]=deathData["matchCreation"] + deathData["deathData"]["timestamp"]
			#Set icon picture:
			sendBack["killIcon"] = {"image": "img/crossed_swords.png"}
			#Set killer picture
			sendBack["killer"] = getChampPicture(deathData, champIdMap, deathData["deathData"]["killerId"], False)
			#Set victim picture
			sendBack["victim"] = getChampPicture(deathData, champIdMap, deathData["deathData"]["victimId"], False)
			if "assistingParticipantIds" in deathData["deathData"]:
				assistCounter = 0
				sendBack["assists"] = []
				for assistPlayer in deathData["deathData"]["assistingParticipantIds"]:
					sendBack["assists"].append(getChampPicture(deathData, champIdMap, assistPlayer, True))
			dataResponse = json.JSONEncoder().encode(sendBack)
		except:
			#If we failed to retrieve timeline data, set matchId to its previous value so we're forced to make a new call
			matchId = oldId


def getChampMap():
	"""Returns the champion map as a dictionary
	Returns the old championIdMap if the API has changed or the request fails"""
	global champIdMap
	global keyURL
	try:
		file = requests.get("https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion" + keyURL + "&dataById=true&champData=image")
		wrapperMap = file.json()
		if "data" in wrapperMap:
			return wrapperMap
	except:
		return champIdMap

def getItemMap():
	"""Returns the item map as a dictionary"""
	global keyURL
	try:
		file = requests.get("https://na.api.pvp.net/api/lol/static-data/na/v1.2/item" + keyURL + "&itemListData=all")
		wrapperMap = file.json()
		return wrapperMap
	except:
		return {}

def getChampMapByKeys():
	"""Returns the champion map as a dictionary. The keys are string representations of champions
	Returns the old championIdMap if the API has changed or the request fails"""
	global champIdMap
	global keyURL
	try:
		file = requests.get("https://na.api.pvp.net/api/lol/static-data/na/v1.2/champion" + keyURL + "&champData=image")
		wrapperMap = file.json()
		if "data" in wrapperMap:
			return wrapperMap["data"]
	except:
		return champIdMap

def setChampIdMap():
	"""Sets the global variable champIdMap to the map from champ IDs to their picture/name data"""
	global champIdMap
	champIdMap = getChampMap()
	print 'map updated'


def getNewMatch(match):
	"""Returns the match Dictionary from the API (including timeline data)
	Will raise an error upon an invalid return to the API call"""
	global keyURL
	file = requests.get("https://na.api.pvp.net/api/lol/na/v2.2/match/" + str(match) + keyURL + "&includeTimeline=true")
	return file.json()


def getPlayerId(matchData, playerData):
	"""Returns the player's ID in a given game
	matchData: a dictionary response from the Riot API for a match call
	playerData: a dictionary that must contain the keys "teamId" and "championId" """
	for partic in matchData['participants']:
		if partic['championId'] == playerData['championId'] and partic['teamId'] == playerData['teamId']:
			return partic['participantId']


def getChampPicture(champId, picMap, assists):
	"""Returns a dictionary where "image" maps to the non-local location of a champion's image
	If the "assists" parameter is true, additional sizing and positioning data is included
	and the target image is a sprite (rather than a portrait)"""
	picPrefix = "http://ddragon.leagueoflegends.com/cdn/"+ picMap['version'] + "/img/champion/"
	picSuffix = ".png"
	assistPicPrefix = "http://ddragon.leagueoflegends.com/cdn/"+ picMap['version'] + "/img/sprite/"
	champData = picMap["data"][str(champId)]
	if not assists:
		return {"image": picPrefix + champData["key"] + picSuffix}
	else:
		return {"image": assistPicPrefix + champData["image"]["sprite"],
				"w": champData["image"]["w"],
				"h": champData["image"]["h"],
				"x": champData["image"]["x"],
				"y": champData["image"]["y"]}

def getItemPicture(id, itemMap):
	"""Returns a string representing the non-local location of the item picture"""
	picPrefix = "http://ddragon.leagueoflegends.com/cdn/"+ itemMap['version'] + "/img/"+ itemMap['type'] +"/"
	try:
		return picPrefix + itemMap['data'][id]['image']['full']
	except:
		return ""

def getDeathInfo(timeline, playerData):
	"""Returns a dictionary containing relevant player data from the player's most recent deathData
	Raises an error if any of the inputs are malformed

	timeline: a dictionary containing the match response from the Riot API (this must contain timeline data)
	playerData: a dictionary that must contain "teamId" and "championId" as keys"""
	playerId = getPlayerId(timeline, playerData)
	info={	"matchMode" : timeline["matchMode"],
			"participants": timeline["participants"],
			"matchCreation": timeline["matchCreation"]}
	fList = timeline["timeline"]["frames"]
	#look at the most recent frames first
	for frame in reversed(fList):
		#look at the most recent event first
		for event in reversed(frame["events"]):
			if(event["eventType"]=="CHAMPION_KILL" and event['victimId'] == playerId):
				info["deathData"] = event
				return info
