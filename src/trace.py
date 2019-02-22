from threading import Thread
import os, re, sys, socket

class trace(Thread):
	running = False
	ipRegex = None
	ipStr = None
	traceCommand = None
	results = None

	def __init__(self, ipStr):
		Thread.__init__(self)
		self.ipRegex = re.compile("([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*)")
		self.ipStr = ipStr
		if sys.platform == 'win32':
			self.traceCommand = 'tracert'
		else:
			self.traceCommand = 'traceroute'

	def run(self):
		self.running = True
		traceproc = os.popen("%s %s" % (self.traceCommand, self.ipStr))
		result = traceproc.readlines()
		for line in result:
			#print line
			ipMatch = self.ipRegex.search(line)
			if ipMatch is not None:
				addr = ipMatch.group(1)
			self.results = "%s %s" % (self.results, self.ipStr)
		self.results = "%s %s" % (self.results, self.ipStr)
		self.running = False
	
	def getList(self):
		return self.results.split(' ')

	def isRunning(self):
		return self.running
