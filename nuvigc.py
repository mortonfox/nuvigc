#!/usr/bin/env python

"""
nuvigc.py - This program converts a SQLite database from GSAK to a GPX file
suitable for processing by Garmin POILoader.

This is based on the original GSAK macro at
http://geocaching.totaltechworld.com/ but rewritten in Python and updated
to support new geocaching GPX features.

Version: 0.0.1
Author: Po Shan Cheah (morton@mortonfox.com)
Source code: http://code.google.com/p/nuvigc/
Created: December 12, 2010
Last updated: December 12, 2010
"""

import sys
import sqlite3
import re

CacheTypes = {
    'A':'Pro', 'B':'Let', 'C':'CIT', 'E':'Eve', 'G':'Ben', 'I':'Whe',
    'L':'Loc', 'M':'Mul', 'O':'Oth', 'R':'Ear', 'T':'Tra', 'U':'Mys',
    'V':'Vir', 'W':'Web', 'X':'Maz', 'Y':'Way', 'Z':'Meg',
}

def escAmp(s):
    return re.sub(r'&(?!\w+;)', r'&amp;', s)

def last4(code):
    global conn

    curs = conn.cursor()
    curs.execute('select lType from logs where lParent=?', (code, ))
    rows = curs.fetchall()
    rowcount = len(rows)

    l4 = ''

    for i in range(4):
	if i >= rowcount:
	    l4 += '0'
	else:
	    s = rows[i]['lType']
	    if s == 'Found it' or s == 'Webcam Photo Taken' or s == 'Attended':
		l4 += 'F'
	    elif s == "Didn't find it":
		l4 += 'N'
	    else:
		l4 += 'X'

    return l4

def convcoord(coord):
    deg = int(coord)
    decim = (coord - deg) * 60.0
    return '%d %06.3f' % (deg, decim)

def convlat(coord):
    if coord < 0:
	return 'S' + convcoord(-coord)
    else:
	return 'N' + convcoord(coord)

def convlon(coord):
    if coord < 0:
	return 'W' + convcoord(-coord)
    else:
	return 'E' + convcoord(coord)

def processCache(row):
    wptname = '%s/%s/%s' % (row['SmartName'], CacheTypes[row['CacheType']], row['Code'])

    status = ''
    statusplain = ''

    if row['TempDisabled']:
	status = '<font color=red>*** Temp Unavailable ***</font><br><br>'
	statusplain = '*** Temp Unavailable ***'

    if row['Archived']:
	status = '<font color=red>*** Archived ***</font><br><br>'
	statusplain = '*** Archived ***'

    name = escAmp(row['Name'])
    ownername = escAmp(row['OwnerName'])

    infoline = '%s/%s/%s/Tb:%s, (D:%.1f/T:%.1f)' % (
	    CacheTypes[row['CacheType']],
	    row['Container'][:3],
	    last4(row['Code']),
	    'Y' if row['HasTravelBug'] else 'N',
	    row['Difficulty'], row['Terrain'])

    dates = 'Pl:%s, LF:%s' % (row['PlacedDate'], row['LastFoundDate'])

    coords = '%s %s' % (convlat(float(row['Latitude'])), convlon(float(row['Longitude'])))

    print wptname, name.encode('utf-8'), ownername.encode('utf-8')
    print infoline
    print dates
    print coords


conn = sqlite3.connect('sqlite.db3')

print """
<?xml version='1.0' encoding='Windows-1252' standalone='no' ?>
<gpx xmlns='http://www.topografix.com/GPX/1/1' xmlns:gpxx = 'http://www.garmin.com/xmlschemas/GpxExtensions/v3' creator='Pilotsnipes' version='1.1' xmlns:xsi = 'http://www.w3.org/2001/XMLSchema-instance' xsi:schemaLocation='http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensions/v3/GpxExtensionsv3.xsd'>
<metadata>
<desc>Pilotsnipes GPX output for Nuvi</desc>
<link href='http://pilotsnipes.googlepages.com'><text>Tourguide Compatible.</text></link>
<time>2008-05-01T00:00:00Z</time>
<bounds maxlat='53.000000' maxlon='-6.0000' minlat='53.000000' minlon='-6.000000'/>
</metadata>

"""

recordnum = 0

conn.row_factory = sqlite3.Row
curs = conn.cursor()
curs.execute('select * from caches')
rows = curs.fetchall()
rowcount = len(rows)
for row in rows:
    recordnum += 1
    if recordnum % 10 == 0:
	# print >> sys.stderr, "\rNow processing: %d of %d points" % (recordnum, rowcount),
	pass
    processCache(row)

# vim:set tw=0:
