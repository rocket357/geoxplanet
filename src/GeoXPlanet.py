#!/usr/bin/env python

## src/GeoXPlanet.py
## Author: rocket357
## sisson.j@gmail.com
##
## This script performs startup checks and launches GeoXPlanet.
## 
## BSD 2-clause license

import sys, os, time, shutil, ConfigParser
from controller import GeoXPlanet

GXPVERSION = '0.99'
HOME=os.path.expanduser('~')
CONFDIR = os.path.join(HOME,".config")
GXPDIR = os.path.join(CONFDIR,"GeoXPlanet")
defaultConfig = os.path.join(GXPDIR,"GeoXPlanet.conf")
configfp = None

try:
	configfp = open(defaultConfig, 'r')
except IOError:
	print "I wasn't able to locate your GeoXPlanet config file."
	print "Would you like for me to create the geoxplanet directory and default files for you now?"
	print "The geoxplanet directory will be: %s" % GXPDIR
	print "and all files will be created within the above directory"
	resp = raw_input("yes or no? ")
	if resp.lower() == 'yes':
		print "Creating default geoxplanet directory and files"
		print "Creating directory: %s" % GXPDIR
		if not os.path.isdir(CONFDIR):
			try:
				os.mkdir(CONFDIR)
			except OSError, err:
				print err
				sys.exit()
		try:
			os.mkdir(GXPDIR)
		except OSError, err:
			print err
			sys.exit()
		configfp = open(defaultConfig, 'w')
		configfp.write("""
[General]
; number of seconds between reading connection info
DELAY=15
; please set DEBUG=True if you run into issues
DEBUG=False

[Static]
VERSION=0.99
PLATFORM=%s
GXPDIR=%s
""" % (sys.platform, GXPDIR))
		configfp.close()
		configfp = None
	else:
		sys.exit()
else:
	print "Using %s" % (defaultConfig)
finally:
	if configfp is None:
		configfp = open(defaultConfig, 'r')
	config = ConfigParser.ConfigParser()
	config.readfp(configfp)
	if config.get("Static","VERSION") == GXPVERSION:
		print "Launching GeoXPlanet-%s" % GXPVERSION
	else:
		pass  # TODO handle mis-matched config/script versions?
	configfp.close()

if __name__ == '__main__':
	program = GeoXPlanet(config)
	program.run()
