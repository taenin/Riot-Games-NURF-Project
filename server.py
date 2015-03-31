from pyramid.config import Configurator
from pyramid.response import Response
from paste.httpserver import serve
import updater
import timers
import json
import os.path


"""Add any singleton static files to this list that are in the same directory as the main server (this file)
   Files in this list are automatically given a config view to allow for GET calls"""
quickLinks = ['./tiles.json', './time.js', "./olympics_data.json", './theme.css', './info.json', './indexjs.js', './indexstyle.css', './matthewpersons_resume.pdf']
localCache = {}
validExtensions = ['.html', '.htm', '.json', '.png', '.jpg', '.ttf', '.woff', '.svg', '.css', 'eot', '.map', '.js', '.pdf', '.txt']
def createCache():
	global validExtensions
	cacheMap = {}
	for root, dirs, files in os.walk("."):
	    for name in files:
	    	key = os.path.join(root, name).replace("\\","/")
	        fileName, fileExtension = os.path.splitext(key)
	        if fileExtension.lower() in validExtensions:
				fileR = ""
				try:
					fileReader = open(key, "rb")
					fileR = fileReader.read()
					fileReader.close()
					print "Read " + key
				except:
					print "Failed to read " + key
					fileR = ""
				cacheMap[fileName + fileExtension.lower()] = fileR
	return cacheMap

def hello_world(request):
	#can cache this later
	global localCache
	#testPage = open('../test.html')
	#res = testPage.read()
	#testPage.close()
	return Response(localCache['./test.html'])

def serveRiotApp(request):
	global localCache
	return Response(localCache['./riotapp.html'])

def serveVisualIndex(request):
	global localCache
	return Response(localCache['./d3visual.html'])

def serveMoodRhythm(request):
	global localCache
	return Response(localCache['./moodrhythm.html'])

def goodbye_world(request):
    return Response('Goodbye world!')

def deathApp(request):
	return Response(updater.dataResponse, content_type='application/json')

def testRq(request):
	global localCache
	return Response(localCache['./test.jpg'], content_type='application/image')

def timeJS(request):
	global localCache
	#can cache this later
	#jsFile = open('../time.js')
	#res = jsFile.read()
	#jsFile.close()
	return Response(localCache['./newtime.js'], content_type = 'application/javascript')

def imgRequest(request):
	global localCache
	return Response(localCache['./img/crossed_swords.png'], content_type='image')

def notfound(request):
	global localCache
	return Response(localCache['./notfound.html'], status='404 Not Found')


def testHomePage(request):
	global localCache
	return Response(localCache['./index.html'], content_type="text/html")


def getViewLambda(cachekey):
	global localCache
	content = getContentType(cachekey)
	return lambda x: Response(localCache[cachekey], content_type = content)

def getContentType(key):
	extension = os.path.splitext(key)[1][1:].lower()
	if extension=="js":
		return 'application/javascript'
	elif extension=="png":
		return 'image/png'
	elif extension=="json":
		return 'application/json'
	elif extension=="html" or extension =="txt":
		return 'text/html'
	return ""

def imgReturn(request):
	global localCache
	key = "./img/" + request.matchdict['file']
	if key in localCache:
		return Response(localCache[key], content_type = getContentType(key))
	else:
		return notfound(request)

def fontRouteReturn(request):
	global localCache
	reqDict = request.matchdict
	key = "./font-awesome-4.2.0/" + reqDict['subfold'] + "/" + reqDict['file']
	if key in localCache:
		return Response(localCache[key], content_type = getContentType(key))
	else:
		return notfound(request)


def riotRouteReturn(request):
	global localCache
	reqDict = request.matchdict
	key = "./riot/" + request.matchdict['file']
	if key in localCache:
		return Response(localCache[key], content_type = getContentType(key))
	else:
		return notfound(request)



if __name__ == '__main__':
	
	localCache = createCache()
	config = Configurator()

	#Dynamically creates a route for every quicklink file in the cache
	for doc in quickLinks:
		if doc in localCache:
			print "Generating Quick Link for: " + doc
			config.add_view(getViewLambda(doc), name=os.path.basename(doc))
	config.add_route("fontroute", "/font-awesome-4.2.0/{subfold}/{file}")
	config.add_route("img", "/img/{file}")
	config.add_route("riotroute", "/riot/{file}")


	config.add_view(imgReturn, route_name="img")
	config.add_view(fontRouteReturn, route_name="fontroute")
	config.add_view(bootstrapRouteReturn, route_name="bootstrap")
	config.add_view(riotRouteReturn, route_name="riotroute")


	config.add_view(testHomePage)
	config.add_view(serveRiotApp, name="whendidchrislastdie")
	config.add_view(serveRiotApp, name="chrispls")
	config.add_view(serveRiotApp, name="riot")
	config.add_view(deathApp, name='player_data.json')

	config.add_notfound_view(notfound)
	app = config.make_wsgi_app()
	championMapUpdater = timers.BackgroundUpdater(86400.0, updater.setChampIdMap).start()
	gameUpdater = timers.BackgroundUpdater(60.0, updater.getMatchData).start()
	serve(app, host='0.0.0.0', port="8080")
    