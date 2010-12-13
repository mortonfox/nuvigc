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
import string

CacheTypes = {
	'A':'Pro', 'B':'Let', 'C':'CIT', 'E':'Eve', 'G':'Ben', 'I':'Whe',
	'L':'Loc', 'M':'Mul', 'O':'Oth', 'R':'Ear', 'T':'Tra', 'U':'Mys',
	'V':'Vir', 'W':'Web', 'X':'Maz', 'Y':'Way', 'Z':'Meg',
}

Attributes = {
	1:'Dogs allowed',
	10:'Difficult climbing',
	11:'May require wading',
	12:'May require swimming',
	13:'Available at all times',
	14:'Recommended at night',
	15:'Available during winter',
	17:'Poison plants',
	18:'Dangerous Animals',
	19:'Ticks',
	2:'Access or parking fee',
	20:'Abandoned mines',
	21:'Cliff / falling rocks',
	22:'Hunting',
	23:'Dangerous area',
	24:'Wheelchair accessible',
	25:'Parking available',
	26:'Public transportation',
	27:'Drinking water nearby',
	28:'Public restrooms nearby',
	29:'Telephone nearby',
	3:'Climbing gear',
	30:'Picnic tables nearby',
	31:'Camping available',
	32:'Bicycles',
	33:'Motorcycles',
	34:'Quads',
	35:'Off-road vehicles',
	36:'Snowmobiles',
	37:'Horses',
	38:'Campfires',
	39:'Thorns',
	4:'Boat',
	40:'Stealth required',
	41:'Stroller accessible',
	42:'Needs maintenance',
	43:'Watch for livestock',
	44:'Flashlight required',
	45:'Lost And Found Tour',
	46:'Truck Driver/RV',
	47:'Field Puzzle',
	48:'UV Light Required',
	49:'Snowshoes',
	5:'Scuba gear',
	50:'Cross Country Skis',
	51:'Special Tool Required',
	52:'Night Cache',
	53:'Park and Grab',
	54:'Abandoned Structure',
	55:'Short hike (less than 1km)',
	56:'Medium hike (1km-10km)',
	57:'Long Hike (+10km)',
	58:'Fuel Nearby',
	59:'Food Nearby',
	6:'Recommended for kids',
	7:'Takes less than an hour',
	8:'Scenic view',
	9:'Significant hike',
}

LogConv = {
	'found it':'F',
	'webcam photo taken':'F',
	'attended':'F',
	"didn't find it":'N',
}


def escAmp(s):
    """
    Convert stray ampersands to HTML entities but leave
    existing HTML entities alone.
    """
    return re.sub(r'&(?!#?\w+;)', r'&amp;', s)

def enc(s):
    """
    Encode Unicode characters in string.
    """
    return s.encode('ascii', 'xmlcharrefreplace')

def last4(code):
    """
    Summarize last 4 cache logs.
    """
    curs = conn.cursor()
    curs.execute('select lType from logs where lParent=?', (code, ))
    rows = curs.fetchall()
    rowcount = len(rows)

    l4 = ''

    for i in range(4):
	if i >= rowcount:
	    l4 += '0'
	else:
	    l4 += LogConv.get(string.lower(rows[i]['lType']), 'X')

    return l4

def convcoord(coord):
    deg = int(coord)
    decim = (coord - deg) * 60.0
    return '%d %06.3f' % (deg, decim)

def convlat(coord):
    """
    Convert latitude from decimal degrees to ddd mm.mmm
    """
    if coord < 0:
	return 'S' + convcoord(-coord)
    else:
	return 'N' + convcoord(coord)

def convlon(coord):
    """
    Convert longitude from decimal degrees to ddd mm.mmm
    """
    if coord < 0:
	return 'W' + convcoord(-coord)
    else:
	return 'E' + convcoord(coord)

def travelBugs(code):
    """
    Get list of travel bugs.
    """
    curs = conn.cursor()
    curs.execute('select TravelBugs from cachememo where code=? limit 1', (code, ))
    row = curs.fetchone()
    return row['TravelBugs']

def getText(code):
    """
    Get textual info for cache.
    """
    curs = conn.cursor()
    curs.execute('select LongDescription,ShortDescription,Hints from cachememo where code=? limit 1', (code, ))
    row = curs.fetchone()
    return (
	    row['LongDescription'],
	    row['ShortDescription'],
	    row['Hints'],
	    )

def attribFmt(row):
    return '%s=%s' % (
	    Attributes.get(row['aId'], 'Unknown attr'),
	    'Y' if row['aInc'] else 'N'
	    )

def attribs(code):
    """
    Get cache attributes.
    """
    curs = conn.cursor()
    curs.execute('select * from attributes where aCode=?', (code, ))
    attr = ''
    return ', '.join([attribFmt(r) for r in curs])


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

    cacheinfo = """
<font color=red>%s by %s</font><br>
<font color=#008000>%s</font><br>
<font color=blue>%s</font><br>
<font color=orange>%s</font><br><br>
""" % (
	enc(name), enc(ownername),
	infoline, dates, coords)

    if row['HasTravelBug']:
	tbstr = escAmp(travelBugs(row['Code']))
	cacheinfo += """
<font color=#FF00FF>**Travel Bugs**%s</font><br><br>
""" % enc(tbstr)

    attr = attribs(row['Code'])
    if attr != '':
	cacheinfo += """
**Attributes**<br>%s<br><br>
""" % attr

    plaincacheinfo = """
%s
%s
%s
%s by %s
%s
""" % (
	statusplain, 
	coords, 
	infoline, 
	enc(name), enc(ownername), 
	dates)

    ( longdesc, shortdesc, hints ) = getText(row['Code'])

    hints = """
<font color=#008000>****<br>Hint: %s<br>****</font><br><br>
""" % enc(escAmp(hints))

    alldesc = enc(shortdesc + longdesc)

    print wptname
    print cacheinfo
    print plaincacheinfo
    print alldesc
    print hints


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
