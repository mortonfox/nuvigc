#!/usr/bin/env python

"""
getattr.py - This script extracts attribute and cache types from the GSAK
static db and converts those into Python lookup tables.

Run this after every GSAK update in case those tables have changed.
"""

import sqlite3
import os

def progfilePath():
    """
    Try to get the Program Files path.
    """
    s = os.environ.get('ProgramFiles')
    if s is not None:
	return s

    homedrive = os.environ.get('HOMEDRIVE')
    if homedrive is None:
	homedrive = 'C:'

    return '%s/Program Files' % homedrive

def cacheType(row):
    return "'%s':'%s'" % (row['vfrom'], row['vto'][0:3])

def attribute(row):
    return "%s:'%s'" % (row['vfrom'], row['vto'])

def main():
    global conn

    dbfile = '%s/GSAK/static.db3' % progfilePath()

    try:
	conn = sqlite3.connect(dbfile)
    except sqlite3.OperationalError, e:
	print >> sys.stderr, 'Error opening database %s: %s' % (dbfile, e.message)
	sys.exit(2)

    conn.row_factory = sqlite3.Row
    curs = conn.cursor()

    outfname = 'lookup.py'
    outf = open(outfname, 'w')

    curs.execute("select * from lookup where type = 'CacheTypes'")
    rows = curs.fetchall()
    
    print >>outf, """
CacheTypes = {
%s
}
""" % ", \n".join(['    ' + cacheType(row) for row in rows]) 

    curs.execute("select * from lookup where type = 'attributes'")
    rows = curs.fetchall()

    print >>outf, """
Attributes = {
%s
}
""" % ", \n".join(['    ' + attribute(row) for row in rows]) 


if __name__ == '__main__':
    main()

# vim:set tw=0:
