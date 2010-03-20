#!/usr/bin/env python

def getGeo(address):
	# Geocode the cities
	# Source: http://code.google.com/apis/maps/documentation/geocoding/index.html
	import urllib, json

	url = "http://maps.google.com/maps/api/geocode/json?" + urllib.urlencode( {"address": address, "sensor": "false"} )
	obj = json.load(urllib.urlopen(url))
	if obj["status"] == 'OK':
		results = obj["results"]
		if len(results):
			latlong = results[0]["geometry"]["location"]
#			print latlong["lat"], latlong["lng"]
			return latlong
	else:
		raise Exception( obj["status"] )

# =============================================================================
if __name__ == '__main__':

	geo = getGeo("1600 Pensylvania Ave, Washington, DC")
	print geo
