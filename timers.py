from threading import Thread
import time, gc

class BackgroundUpdater(Thread):
	"""Creates a thread that calls the method "fnct" every "delay" seconds
		self._delay: Float. Represents the time in seconds between function calls
		self._fnct: Function that takes no arguments. To be called every "delay" seconds
	"""
	def __init__(self, delay, fnct):
		Thread.__init__(self)
		self._delay = delay
		self._fnct = fnct
		self._stopped = False
		

	def run(self):
		while not self._stopped:
			self._fnct()
			gc.collect()
			time.sleep(self._delay)
			


	def temporaryStop(self):
		self._stopped = True