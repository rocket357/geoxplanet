from threading import Thread
import threading
import os, re, sys, socket, time, subprocess

class trace(Thread):
    DEBUG = None
    running = None
    ipRegex = None
    ipStr = None
    traceCommand = None
    results = ''
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
        self.running = 'running'
        if self.DEBUG:
            begin = time.time()
            print "Beginning trace on %s" % self.ipStr
        output = ''
        try:
            bit_bucket = open(os.devnull, 'w')
            output = subprocess.check_output([self.traceCommand, self.hops, '15', self.ipStr], stderr=bit_bucket)
            if self.DEBUG: print output
        except subprocess.CalledProcessError, e:
            if self.DEBUG:
                print e
        for line in output.split('\n'):
            ipMatch = self.ipRegex.search(line)
            if ipMatch is not None:
                addr = ipMatch.group(1)
                if len(self.results) > 0:
                    self.results = "%s %s" % (self.results, addr)
                else:
                    self.results = addr
        if len(self.results) > 1:
            self.results = "%s %s" % (self.results, self.ipStr)
        else:
            self.results = self.ipStr
        if self.DEBUG:
            print "Trace finished on %s in %s seconds" % (self.ipStr, time.time() - begin)
        self.running = 'complete'
    
    def getList(self):
        if self.DEBUG: print self.results
        return self.results.split(' ')

    def stopped(self):
        return self._stop_event.is_set()

    def stop(self):
        self.running = 'abort'
        self._stop_event.set()
