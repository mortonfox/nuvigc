# nuvigc - GSAK geocaching data preprocessor for Garmin POI Loader

## Introduction

The nuvigc script reads a [GSAK](http://gsak.net/) database and generates a
GPX file suitable for passing to
[Garmin POI Loader](http://www8.garmin.com/products/poiloader/) to load
onto a Garmin n&uuml;vi GPS.

We can visualize the flow of geocaching data like so:

    geocaching.com pocket query -> GSAK -> nuvigc -> POI Loader -> nüvi GPS

nuvigc is based on an older GSAK macro at
[Garmin Nuvi - True Paperless Geocaching](http://geocaching.williamsonnetwork.com)
but instead of running as a macro within GSAK, it runs as a standalone
Python script and can thus be called easily from a batch file.

## Setup

In order to work, nuvigc needs some attribute information from GSAK in
lookup.py. Run getattr.py to generate that file.

    python getattr.py

On Windows, that command should be sufficient. If you're running GSAK in
Wine on OS X or Linux, you'll need to set the ProgramFiles environment
variable. For example:

    export ProgramFiles=/Applications/GSAK.app/drive_c/Program\ Files
    python getattr.py

## Usage

To use nuvigc, just run nuvigc.py with the GSAK database names as parameters.

    python nuvigc.py home delaware maryland

That command will produce one GPX file, one JPG, and one BMP for each database. The two image files are simple icons (X in a yellow box) that will indicate geocaches on the n&uuml;vi map screen. At this time, there is no support yet for changing the geocache icon.

You can also change the name of the output file. For example,

    python nuvigc.py maryland=amaryland

will write to output
files ```amaryland GSAK.gpx```, ```amaryland GSAK.jpg```
and ```amaryland GSAK.bmp``` instead. You can use
this feature to affect the order in which POI files show up on the GPS.

On Windows, that command should be sufficient. On OS X or Linux, you'll
need to set the APPDATA environment variable. For example:

    export APPDATA=/Applications/GSAK.app/drive_c/users/username/Application\ Data
    python nuvigc.py home delaware maryland

Once you have done that, simply run Garmin POI Loader and tell it to read
GPX files from this folder.

## Caution

Avoid using numbers in database/output names. POI Loader will convert those
waypoints to speed alerts instead of regular POIs and you will not be able to
route to them.
