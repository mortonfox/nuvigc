#!/usr/bin/env python

"""
nuvigc.py - This program converts a SQLite database from GSAK to a GPX file
suitable for processing by Garmin POILoader.

This is based on the original GSAK macro at
http://geocaching.totaltechworld.com/ but rewritten in Python and updated
to support new geocaching GPX features.

Version: 0.0.5
Author: Po Shan Cheah (morton@mortonfox.com)
Source code: https://github.com/mortonfox/nuvigc
Created: December 12, 2010
Last updated: August 11, 2016
"""

import sys
import sqlite3
import re
import string
from HTMLParser import HTMLParser, HTMLParseError
from optparse import OptionParser
import os
import os.path
import nuvifiles
import base64
from lookup import CacheTypes, Attributes

LogConv = {
	'found it':'F',
	'webcam photo taken':'F',
	'attended':'F',
	"didn't find it":'N',
}

TextLimit = 16500


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

class LogsTable:
    """
    Prefetch logs table.
    """
    def __init__(self):
	self.table = {}

    def queryData(self):
	curs = conn.cursor()
	curs.execute('select * from logs')
	for row in curs:
	    self.table[row['lParent']] = self.table.get(row['lParent'], []) + [row]
	for lpar, row in self.table.iteritems():
	    row.sort(key=lambda r: r['lDate'], reverse=True)

    def getRows(self, parent):
	if not self.table:
	    self.queryData()
	return self.table.get(parent, [])


def last4(code):
    """
    Summarize last 4 cache logs.
    """
#     curs = conn.cursor()
#     curs.execute('select lType from logs where lParent=? order by lDate desc', (code, ))
#     rows = curs.fetchall()
#     curs.close()
    rows = logsTable.getRows(code)
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

class CacheMemo:
    """
    Prefetch cachememo table.
    """
    def __init__(self):
	self.table = {}

    def queryData(self):
	curs = conn.cursor()
	curs.execute('select * from cachememo')
	for row in curs:
	    self.table[row['Code']] = row

    def getRow(self, code):
	if not self.table:
	    self.queryData()
	return self.table[code]


def travelBugs(code):
    """
    Get list of travel bugs.
    """
    return cacheMemo.getRow(code)['TravelBugs']
#     curs = conn.cursor()
#     curs.execute('select TravelBugs from cachememo where code=? limit 1', (code, ))
#     row = curs.fetchone()
#     curs.close()
#     return row['TravelBugs']

def getText(code):
    """
    Get textual info for cache.
    """
#     curs = conn.cursor()
#     curs.execute('select LongDescription,ShortDescription,Hints from cachememo where code=? limit 1', (code, ))
#     row = curs.fetchone()
#     curs.close()
    row = cacheMemo.getRow(code)
    return (
	    row['LongDescription'],
	    row['ShortDescription'],
	    row['Hints'],
	    )

class AttrTable:
    """
    Prefetch attributes table.
    """
    def __init__(self):
	self.table = {}

    def queryData(self):
	curs = conn.cursor()
	curs.execute('select * from attributes')
	for row in curs:
	    self.table[row['aCode']] = self.table.get(row['aCode'], []) + [row]

    def getRows(self, code):
	if not self.table:
	    self.queryData()
	return self.table.get(code, [])


def attribFmt(row):
    return '%s=%s' % (
	    Attributes.get(row['aId'], 'Unknown attr'),
	    'Y' if row['aInc'] else 'N'
	    )

def attribs(code):
    """
    Get cache attributes.
    """
    rows = attrTable.getRows(code)
    return ', '.join([attribFmt(r) for r in rows])
#     curs = conn.cursor()
#     curs.execute('select * from attributes where aCode=?', (code, ))
#     return ', '.join([attribFmt(r) for r in curs])

class LogMemo:
    """
    Prefetch logmemo table.
    """
    def __init__(self):
	self.table = {}

    def queryData(self):
	curs = conn.cursor()
	curs.execute('select * from logmemo')
	for row in curs:
	    self.table[row['lLogId']] = row['lText']

    def getLogText(self, logid):
	if not self.table:
	    self.queryData()
	return self.table[logid]


def logText(logid):
    return logMemo.getLogText(logid)
#     curs = conn.cursor()
#     curs.execute('select lText from logmemo where lLogId=? limit 1', (logid, ))
#     row = curs.fetchone()
#     curs.close()
#     return row['lText']

def logFmt(row):
    return """
<font color=#0000FF>%s by %s %s</font> - %s%s%s<br><br>
""" % (
	row['lType'],
	enc(escAmp(row['lBy'])),
	row['lDate'],
	convlat(float(row['lLat'])) + ' ' if row['lLat'] != '' else '',
	convlon(float(row['lLon'])) + ' ' if row['lLon'] != '' else '',
	cleanHTML(enc(escAmp(logText(row['lLogId'])))),
	)

def logs(code):
    """
    Get cache logs.
    """
#     curs = conn.cursor()
#     curs.execute('select lType,lBy,lDate,lLat,lLon,lLogId from logs where lParent=? order by lDate desc', (code, ))
#     return ''.join([logFmt(r) for r in curs])
    rows = logsTable.getRows(code)
    return ''.join([logFmt(r) for r in rows])

def cleanStr(s):
    """
    HTML-escape some special characters and compress whitespace.
    Convert some entity refs.
    """
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'"', '&quot;', s)
    s = re.sub(r'<', '&lt;', s)
    s = re.sub(r'>', '&gt;', s)

    s = re.sub(r'&ndash;', '-', s)
    s = re.sub(r'&mdash;', '-', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'&ldquo;', '&quot;', s)
    s = re.sub(r'&rdquo;', '&quot;', s)
    s = re.sub(r'&lsquo;', "'", s)
    s = re.sub(r'&rsquo;', "'", s)
    s = re.sub(r'&trade;', '(TM)', s)

    s = re.sub(r'&(\w+);', entity_repl, s)

    s = re.sub(r'&#8216;', "'", s)
    s = re.sub(r'&#8217;', "'", s)
    s = re.sub(r'&#8220;', '&quot;', s)
    s = re.sub(r'&#8221;', '&quot;', s)
    s = re.sub(r'&#8211;', '-', s)
    s = re.sub(r'&#8212;', '-', s)

    s = re.sub(r'\x00', '', s)

    s = re.sub(r'&#(\d+);', entity_num_repl, s)

    return s

def entity_repl(matchobj):
    name = matchobj.group(1)
    if name == 'quot' or name == 'lt' or name == 'gt' or name == 'amp':
	return '&%s;' % name
    else:
	return '(%s)' % name

def entity_num_repl(matchobj):
    name = matchobj.group(1)
    # Mac version of POI Loader doesn't handle numeric entities very well.
    return ('(#%s)' if sys.platform == 'darwin' else '&#%s;') % name

class StripHTML(HTMLParser):
    """
    Strip out HTML tags except for <p> and <br>.
    Convert some HTML entities and remove the rest.
    This is for POILoader and the Nuvi, which can't handle anything
    too complicated.
    """
    def __init__(self):
	self.reset()
	self.text = ''

    def handle_data(self, d):
	d = re.sub(r'\r', r'', d)
	d = re.sub(r'\n', r'<br>', d)
	self.text += d

    def handle_starttag(self, tag, attrs):
	if tag == 'p' or tag == 'br':
	    self.text += '<%s>' % tag

    def handle_startendtag(self, tag, attrs):
	if tag == 'br':
	    self.text += '<%s>' % tag

    def handle_endtag(self, tag):
	if tag == 'p':
	    self.text += '</%s>' % tag

    def handle_entityref(self, name):
	if name == 'ndash' or name == 'mdash':
	    self.text += '-'
	elif name == 'nbsp':
	    self.text += ' '
	elif name == 'ldquo' or name == 'rdquo':
	    self.text += '&quot;'
	elif name == 'lsquo' or name == 'rsquo':
	    self.text += "'"
	elif name == 'trade':
	    self.text += '(TM)'
	elif name == 'quot' or name == 'lt' or name == 'gt' or name == 'amp':
	    self.text += '&%s;' % name
	else:
	    self.text += '(%s)' % name

    def handle_charref(self, name):
	if name == '8216' or name == '8217':
	    self.text += "'"
	elif name == '8220' or name == '8221':
	    self.text += '&quot;'
	elif name == '8211' or name == '8212':
	    self.text += '-'
	else:
	    # Mac version of POI Loader doesn't handle numeric entities very well.
	    self.text += ('(#%s)' if sys.platform == 'darwin' else '&#%s;') % name

    def unknown_decl(self, decl):
	pass

    def get_data(self):
	return self.text

def cleanHTML(s):
    """
    Wrapper function for HTML stripper class.
    """
    stripper = StripHTML()
    try:
	stripper.feed(s)
    except HTMLParseError:
	# If the HTML parser fails, we fall back to a simple cleanup.
	s = re.sub(r'&', r'&amp;', s)
	s = re.sub(r'<', r'[', s)
	s = re.sub(r'>', r']', s)
	return s
    return stripper.get_data()


def truncate(s, length):
    """
    Truncate a string to the specified length but clean up HTML entities
    at the end of the string that may have gotten chopped up.
    """
    if len(s) <= length:
	return s
    s = s[:length]
    # Clean up the end of the string so we don't leave a piece of a
    # HTML entity behind when we truncate the string.
    return s[:-7] + re.sub(r'&', r'', s[-7:])

def processCache(row):
    """
    Process a record from the caches table. Generate GPX output for that
    geocache.
    """
    wptname = '%s/%s/%s' % (row['SmartName'], CacheTypes[row['CacheType']], row['Code'])

    status = ''
    statusplain = ''

    if row['TempDisabled']:
	status = '<font color=#FF0000>*** Temp Unavailable ***</font><br><br>'
	statusplain = '*** Temp Unavailable ***'

    if row['Archived']:
	status = '<font color=#FF0000>*** Archived ***</font><br><br>'
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
<font color=#FF0000>%s by %s</font><br>
<font color=#008000>%s</font><br>
<font color=#0000FF>%s</font><br>
<font color=#FFA500>%s</font><br><br>
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
<font color=#00BFFF>**Attributes** %s</font><br><br>
""" % attr

    # This is some cache information in plain text that the Nuvi will display
    # before you touch the "More" button.
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

    hints = "<font color=#008000>Hint: %s</font><br>" % enc(escAmp(hints))

    alldesc = escAmp(enc(shortdesc + '<br>' + longdesc))

    logstr = cleanStr(logs(row['Code']))
    hints = cleanStr(hints)

    alldesc = cleanHTML(alldesc)

    combdesc = cleanStr(status + escAmp(cacheinfo) + "Description: " + alldesc + '<br>')

    if len(combdesc) + len(hints) > TextLimit:
	finalstr = truncate(combdesc, TextLimit - len(hints) - 10) + cleanStr('<br>**DESCRIPTION CUT**<br>') + hints
    else:
	finalstr = truncate(combdesc + hints + logstr, TextLimit)


    return """
<wpt lat='%s' lon='%s'><ele>0.00</ele><time>2008-05-01T00:00:00Z</time>
<name>%s</name><cmt></cmt><desc>%s</desc>
<link href="futurefeature.jpg"/><sym>Information</sym>
<extensions><gpxx:WaypointExtension>
<gpxx:DisplayMode>SymbolAndName</gpxx:DisplayMode>
<gpxx:Address><gpxx:PostalCode>%s</gpxx:PostalCode></gpxx:Address>
</gpxx:WaypointExtension></extensions></wpt>
""" % (
	row['Latitude'], row['Longitude'],
	wptname, finalstr, cleanStr(escAmp(plaincacheinfo)),
	)

def childComment(code):
    curs = conn.cursor()
    curs.execute('select cComment from waymemo where cCode=? limit 1', (code, ))
    row = curs.fetchone()
    curs.close()
    return row['cComment']

def parentSmart(code):
    curs = conn.cursor()
    curs.execute('select smartName from caches where code=? limit 1', (code, ))
    row = curs.fetchone()
    curs.close()
    return row['smartName']

def processWaypoint(row):
    """
    Generate GPX for an additional waypoint.
    """
    wptname = '%s - %s' % (row['cCode'], row['cType'])

    ccomment = cleanHTML(escAmp(childComment(row['cCode'])))

    parentinfo = '%s - (%s)' % (
	    row['cParent'],
	    parentSmart(row['cParent']),
	    )

    childdesc = """
This is a child waypoint for Cache <font color=#0000FF>%s</font><br><br>Type: %s<br>Comment: %s
""" % (
	parentinfo,
	enc(row['cType']),
	enc(ccomment),
	)

    childdesc = cleanStr(childdesc)

    return """
<wpt lat='%s' lon='%s'><ele>0.00</ele><time>2008-05-01T00:00:00Z</time>
<name>%s</name><cmt></cmt><desc>%s</desc><link href="futurefeature.jpg"/>
<sym>Information</sym>
<extensions><gpxx:WaypointExtension>
<gpxx:DisplayMode>SymbolAndName</gpxx:DisplayMode>
<gpxx:Address><gpxx:PostalCode>Child of %s</gpxx:PostalCode></gpxx:Address>
</gpxx:WaypointExtension></extensions></wpt>
""" % (
	row['cLat'], row['cLon'],
	wptname, childdesc, parentinfo,
	)


def appDataPath():
    """
    Try to get the Windows application data path by various means.
    """
    s = os.environ.get('APPDATA')
    if s is not None:
	return s

    userprof = os.environ.get('USERPROFILE')
    if userprof is not None:
	return userprof + '/Application Data'
    
    homedrive = os.environ.get('HOMEDRIVE')
    homepath = os.environ.get('HOMEPATH')

    if homedrive is not None and homepath is not None:
	return '%s%s/Application Data' % (homedrive, homepath)

    if homedrive is None:
	homedrive = 'C:'

    username = os.environ.get('USERNAME')
    if username is not None:
	return '%s/Documents and Settings/%s/Application Data'

    return ''

def writeicon(fname, data):
    """
    Write out an icon file. Don't do anything if it already exists.
    """
    if os.path.exists(fname):
	return
    f = open(fname, 'wb')
    f.write(base64.b64decode(data))
    f.close()

def init_prefetch():
    global logsTable, cacheMemo, attrTable, logMemo
    logsTable = LogsTable()
    cacheMemo = CacheMemo()
    attrTable = AttrTable()
    logMemo = LogMemo()


def process_db(dbname, outname, outdir, gsakdir):
    global conn

    init_prefetch()

    if outname == dbname:
        print 'Processing database %s...' % dbname
    else:
        print 'Processing database %s to %s...' % (dbname, outname)

    dbfile = '%s/%s/data/%s/sqlite.db3' % (appDataPath(), gsakdir, dbname)

    try:
	conn = sqlite3.connect(dbfile)
    except sqlite3.OperationalError, e:
	print >> sys.stderr, 'Error opening database %s: %s' % (dbfile, e.message)
	sys.exit(2)

    outfname = '%s/%s GSAK.gpx' % (outdir, outname)

    outf = open(outfname, 'w')

    print >>outf, """<?xml version='1.0' encoding='Windows-1252' standalone='no' ?>
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

    # Custom text factory ignores Unicode characters that cannot be decoded from utf-8.
    conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")

    curs = conn.cursor()
    curs.execute('PRAGMA cache_size=20000')
    curs.execute('select * from caches')
    rows = curs.fetchall()
    rowcount = len(rows)
    for row in rows:
	recordnum += 1
	if recordnum % 10 == 0:
	    print "\rNow processing: %d of %d points" % (recordnum, rowcount),
	print >>outf, processCache(row)

    print "\rNow processing: %d of %d points" % (recordnum, rowcount),
    print "\nDone"

    recordnum = 0

    curs.execute('select * from waypoints')
    rows = curs.fetchall()
    rowcount = len(rows)
    for row in rows:
	recordnum += 1
	if recordnum % 10 == 0:
	    print "\rNow processing: %d of %d additional points" % (recordnum, rowcount),
	print >>outf, processWaypoint(row)

    print "\rNow processing: %d of %d additional points" % (recordnum, rowcount),
    print "\nDone"

    print >>outf, "</gpx>"
    outf.close()

    writeicon('%s/%s GSAK.bmp' % (outdir, outname), nuvifiles.cacheBMP)
    writeicon('%s/%s GSAK.jpg' % (outdir, outname), nuvifiles.cacheJPG)


def main():
    parser = OptionParser(usage = """Usage: %prog [options] dbname[=outname] [dbname[=outname] ...]
        dbname: Name of database to process.
        dbname=outname: Process database dbname but output to file outname.""")
    parser.add_option('-d', '--output-dir', dest='outdir', default='.',
	    help='Output directory.')
    parser.add_option('-g', '--gsak-folder', dest='gsakfolder', default='gsak',
	    help='GSAK folder name.')

    (options, args) = parser.parse_args()

    if len(args) < 1:
	parser.print_help()
	sys.exit(1)

    for arg in args:
        # name=name2 means read DB name but output as name2.
        dbname = arg
        outname = arg
        if '=' in arg:
            dbname, outname = arg.split('=', 2)
	process_db(dbname, outname, options.outdir, options.gsakfolder)


if __name__ == '__main__':
    main()

# vim:set tw=0:
