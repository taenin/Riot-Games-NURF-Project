import timers
import time
import sys
import updater
def main(args):
	startTime = int(args[1])
	mainWorker = updater.Worker(startTime)
	comThread = timers.BackgroundUpdater(3, mainWorker.updateInformation).start()
	try:
		while True:
			time.sleep(1)
	except:
		print "Exiting ..."
if __name__ == '__main__':
	main(sys.argv)
	

