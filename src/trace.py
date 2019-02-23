from threading import Thread
import threading
import os, re, sys, socket, time, subprocess

class trace(Thread):
    DEBUG = None
    running = False
    ipRegex = None
    ipStr = None
    traceCommand = None
    results = None
    hops = None

    def __init__(self, ipStr, DEBUG):
        Thread.__init__(self)
        self._stop_event = threading.Event()
        self.DEBUG = DEBUG
        self.ipRegex = re.compile("([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*)")
        self.ipStr = ipStr
        if sys.platform == 'win32':
            self.traceCommand = 'tracert'
            self.hops = '-h'
        else:
            self.traceCommand = 'traceroute'
            self.hops = '-m'

    def run(self):
        if self.DEBUG:
            begin = time.time()
            print "Beginning trace on %s" % self.ipStr
        self.running = True
        output = []
        try:
            bit_bucket = open(os.devnull, 'w')
            output = subprocess.check_output([self.traceCommand, self.hops, '15', self.ipStr], stderr=bit_bucket)
        except subprocess.CalledProcessError, e:
            if self.DEBUG:
                print e
        for line in output:
            ipMatch = self.ipRegex.search(line)
            if ipMatch is not None:
                addr = ipMatch.group(1)
            self.results = "%s %s" % (self.results, self.ipStr)
        self.results = "%s %s" % (self.results, self.ipStr)
        if self.DEBUG:
            print "Trace finished on %s in %s seconds" % (self.ipStr, time.time() - begin)
        self.running = False
    
    def getList(self):
        return self.results.split(' ')

    def isRunning(self):
        return self.running

    def stopped(self):
        return self._stop_event.is_set()

    def stop(self):
        self.running = False
        self._stop_event.set()
