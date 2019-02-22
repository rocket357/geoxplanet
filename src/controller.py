#!/usr/bin/env python

## src/controller.py
## Author: rocket357
## sisson.j@gmail.com
##
## This script contains the main body of logic for GeoXPlanet.
## 
## BSD 2-clause license

import sys, os, time, csv, codecs
import requests
import zipfile
import sqlite3
from netaddr import IPNetwork, IPAddress
from trace import trace

class GeoXPlanet:

	db = None
	dbc = None
	cfg = None
	DB_SQL = None
	GXPDIR = None
	platform = None
	desktop = None
	netstat = 'netstat -na'
	flowsrc = None
	locationCache = {}
	tracedIPs = {}
	# https://www.cisco.com/assets/sol/sb/Switches_Emulators_v2_2_015/help/nk_configuring_device_security26.html
	# with RFC1918 ranges added in
	martians = [ 
		"0.0.0.0/8",		# Source hosts on this network 
		"10.0.0.0/8",		# RFC1918 private range
		"127.0.0.0/8", 		# Internet host loopback address range
		"172.16.0.0/12",	# RFC1918 private range
		"192.0.2.0/24",		# TEST-NET example
		"192.168.0.0/16",	# RFC1918 private range
		"224.0.0.0/4",		# IPv4 multicast
		"240.0.0.0/4" 		# Reserved Address Range
	]

	def __init__(self, config):
		self.cfg = config
		self.GXPDIR = config.get("Static", "GXPDIR")
		self.platform = sys.platform
		print "Starting up on %s" % self.platform
		self.setupDB()

	def setupDB(self):
		DB_URL = "https://geolite.maxmind.com/download/geoip/database/GeoLite2-City-CSV.zip"
		DB_CSV = os.path.join(self.GXPDIR,"GeoLite2-City-CSV.zip")
		self.DB_SQL = os.path.join(self.GXPDIR,"locations.db")
		r = requests.head(DB_URL)
		pattern = '%a, %d %b %Y %H:%M:%S GMT'
		lastModified = int(time.mktime(time.strptime(r.headers["Last-Modified"],pattern)))
		size = int(r.headers["Content-Length"])
		size_mb = float(size) / (1024*1024)
		if not os.path.isfile(self.DB_SQL):
			print "We need to build out the locations database."
			print "This only needs to be done once per update."
		else:
			try:
				self.db = sqlite3.connect(self.DB_SQL)
				sqltest = """SELECT COUNT(*) FROM IpBlocks;"""
				self.dbc = self.db.cursor()
				self.dbc.execute(sqltest)
				print "Rows in database:  %s" % self.dbc.fetchone()
				return
			except Exception, e:
				print "%s failed sanity checks due to: %s" % (self.DB_SQL, e)
				sys.exit()
			
		if not os.path.isfile(DB_CSV):
			print "I need to download and unzip a copy of MaxMind's free GeoLite2 City database."
			print "File location:  %s" % DB_URL
			print "This file is approximately %s MB in size" % round(size_mb, 2)
			print "Do you want me to do that now?"
			resp = raw_input("yes or no? ")
			if resp.lower() == 'yes':
				print "Downloading GeoLocation Database...",
				sys.stdout.flush()
				c = requests.get(DB_URL, allow_redirects=True)
				f = open(DB_CSV, 'w')
				f.write(c.content)
				f.close()
				print "Done!"
				zipfp = zipfile.ZipFile(DB_CSV, 'r')
				zipdir = os.path.join(self.GXPDIR, "GeoLite2")
				if not os.path.isdir(zipdir):
					os.mkdir(zipdir)
				print "Unzipping the Geolocation database to %s..." % zipdir,
				sys.stdout.flush()
				zipfp.extractall(zipdir)
				zipfp.close()
				print "Done!"
		else:
			d = os.path.getmtime(DB_CSV)
			if lastModified > os.path.getmtime(DB_CSV): # the URL is newer than the local file
				print "I need to download an updated copy of MaxMind's free GeoLite2 City database."
				print "Do you want to do that now?"
				resp = raw_input("yes or no? ")
				if resp.lower() == 'yes':
					print "Downloading update for GeoLocation Database...",
					c = requests.get(DB_URL, allow_redirects=True)
					f = open(DB_CSV, 'wb').write(c.content)
					f.close()
					print "Done!"
					zipfp = zipfile.ZipFile(DB_CSV, 'r')
					zipdir = os.path.join(self.GXPDIR, "GeoLite2")
					if not os.path.isdir(zipdir):
						os.mkdir(zipdir)
					print "Unzipping the Geolocation files...",
					sys.stdout.flush()
					zipfp.extractall(zipdir)
					zipfp.close()
					print "Done!"
				else:
					print "Skipping the update for now."
		# and now the fun begins...
		locdir = os.listdir(os.path.join(self.GXPDIR,"GeoLite2"))
		ipv4_loc = os.path.join(self.GXPDIR,"GeoLite2",locdir[0],"GeoLite2-City-Blocks-IPv4.csv")
		ipv6_loc = os.path.join(self.GXPDIR,"GeoLite2",locdir[0],"GeoLite2-City-Blocks-IPv6.csv")
		try:
			self.db = sqlite3.connect(self.DB_SQL)
		except Exception, e:
			print e
		print "Creating the sqlite3 tables...",
		sys.stdout.flush()
		create_table = """CREATE TABLE IF NOT EXISTS IpBlocks (
	ipstart int,
	ipend int,
	lat float,
	lon float
);"""
		self.dbc = self.db.cursor()
		self.dbc.execute(create_table)
		ips_lat_lon = []
		count = 0
		print "Done!"
		print "Reading network/latitude/longitude information and inserting into sqlite3 db...",
		sys.stdout.flush()
		with open(ipv4_loc,'rb') as data:
			for line in data.readlines():
				if 'network' in line:  continue
				cols = line.split(',')
				#print cols[0]
				sys.stdout.flush()
				net = IPNetwork(cols[0]).network
				brd = IPNetwork(cols[0]).broadcast
				if net is None or brd is None:
					continue
				ips_lat_lon.append((int(IPAddress(net)),int(IPAddress(brd)),cols[7],cols[8]))
				count = count + 1
				if count % 1000 == 0:  # running in batches to reduce memory overhead
					try:
						#print "Rows processed:  %s" % count
						self.dbc.executemany("INSERT INTO IpBlocks (ipstart, ipend, lat, lon) VALUES (?, ?, ?, ?);", ips_lat_lon)
						ips_lat_lon = []
					except Exception, e:
						print "FUCKED:  %s %s %s %s" % (net, brd, cols[7], cols[8])
						print e
					finally:
						ips_lat_lon = []
			self.dbc.executemany("INSERT INTO IpBlocks (ipstart, ipend, lat, lon) VALUES (?, ?, ?, ?);", ips_lat_lon)
		self.db.commit()
		print "Done!"
		print "Rows processed:  %s" % count
		print "Creating indexes...",
		sys.stdout.flush()
		create_index = """CREATE INDEX net_idx ON IpBlocks(ipstart,ipend,lat,lon);"""
		self.dbc.execute(create_index)
		self.db.commit()
		print "Done!"

	def lookupIP(self, IP):
		#start_time = time.time()
		found = False
		if IP in self.locationCache.keys():
			#print "IP Found in locationCache"
			return self.locationCache[IP]
		else:
			print "Pulling %s from db..." % IP
			IPE = int(IPAddress(IP))
			query = "SELECT * FROM IpBlocks WHERE ipstart <= %s and ipend >= %s;" % (IPE, IPE)
			#query_begin = time.time()
			res = self.dbc.execute(query)
			#print "dbc.execute took %s seconds" % (time.time() - query_begin)
			row = res.fetchone()
			self.locationCache[IP] = row
			#print "%s in %s" % (IP, row)
			#print "lookupIP took %s seconds" % (time.time() - start_time)
			sys.stdout.flush()	

	def _isMartian(self, ipAddr):
		for cidr in self.martians:
			if self._ipInCIDR(ipAddr, cidr):
				return True
		return False	

	def _ipInCIDR(self, ipAddr, CIDR):
		return IPAddress(ipAddr) in IPNetwork(CIDR)

	def getLocalActiveConnections(self):
		localActiveConnections = []
		traceDict = {}
		connectionList = os.popen(self.netstat).readlines()
		for conn in connectionList:
			if 'ESTABLISHED' in conn:
				#print conn
				sys.stdout.flush()
				if self.platform == 'win32':
					ipport = conn.split()[2]
				else:
					ipport = conn.split()[4]
				if 'openbsd' in sys.platform:
					ipAddr = '.'.join(ipport.split('.')[:-1])
					ipPort = ipport.split('.')[-1]
					#print "%s -> %s" % (ipAddr, ipPort)
				else:
					ipAddr = ipport.split(':')[0]
					ipPort = ipport.split(':')[1]
				if not self._isMartian(ipAddr):
					#print ipAddr
					self.lookupIP(ipAddr)
					localActiveConnections.append("%s,%s" % (ipAddr, ipPort))
					# TODO - causes random hangs?
					if self.cfg.get("General","Trace") == 'True':
						if ipAddr not in self.tracedIPs.keys():
							self.traceroute(ipAddr)

	def traceroute(self, ipAddr):
		# start a separate thread (trace class) so we can continue
		# without having to wait around for the traceroute to complete
		curtrace = trace(ipAddr)
		curtrace.start()
		self.tracedIPs[ipAddr] = curtrace

	def processList(self, ipList):
		for ip in ipList:
			pass	

	def run(self):
		while True:
			time.sleep(float(self.cfg.get("General","DELAY")))
			self.getLocalActiveConnections()
			
