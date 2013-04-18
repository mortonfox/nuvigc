# nuvigc

The nuvigc script reads a [GSAK](http://gsak.net/) database and generates a GPX file suitable for passing to [Garmin POI Loader](http://www8.garmin.com/products/poiloader/) to load onto a Garmin nüvi GPS.

We can visualize the flow of geocaching data like so:

    geocaching.com pocket query -> GSAK -> nuvigc -> POI Loader -> nüvi GPS 

nuvigc is based on an older GSAK macro at [Garmin Nuvi - True Paperless Geocaching](http://geocaching.totaltechworld.com) but instead of running as a macro within GSAK, it runs as a standalone Python script and can thus be called easily from a batch file.

