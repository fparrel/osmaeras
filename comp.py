import xml.etree.ElementTree as ET
from math import sin, cos, atan2, sqrt, pi, radians

data = ET.parse('sophia.osm')

nodes = {}
for e in data.getroot():
	if e.tag=='node':
		nodes[e.attrib['id']] = float(e.attrib['lat']),float(e.attrib['lon'])

def GeodeticDistGreatCircle(lat1,lon1,lat2,lon2):
	"Compute distance between two points of the earth geoid (approximated to a sphere)"
	# convert inputs in degrees to radians
	lat1 = lat1 * 0.0174532925199433
	lon1 = lon1 * 0.0174532925199433
	lat2 = lat2 * 0.0174532925199433
	lon2 = lon2 * 0.0174532925199433
	# just draw a schema of two points on a sphere and two radius and you'll understand
	a = sin((lat2 - lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1)/2)**2
	c = 2 * atan2(sqrt(a), sqrt(1-a))
	# earth mean radius is 6371 km
	return 6372795.0 * c

def lenOfPath(path):
	l = 0.0
	for i in range(1,len(path)):
		l += GeodeticDistGreatCircle(path[i-1][0],path[i-1][1],path[i][0],path[i][1])
	return l

def reproject(p):
	"""Returns the x & y coordinates in meters using a sinusoidal projection"""
	earth_radius = 6371009 # in meters
	lat_dist = pi * earth_radius / 180.0
	y = [pt[0] * lat_dist for pt in p]
	x = [pt[1] * lat_dist * cos(radians(pt[0])) for pt in p]
	return zip(x, y)

def areaOfPolygon(p1):
    """Calculates the area of an arbitrary polygon given its verticies"""
    p = reproject(p1)
    area = 0.0
    if len(p)==1:
        return 0.0
    for i in range(-1, len(p)-1):
        area += p[i][0] * (p[i+1][1] - p[i-1][1])
    return abs(area) / 2.0

paths = []
roads = []
buildings = []
vegetal = []
water = []
nd_not_found = 0
for e in data.getroot():
	if e.tag=='way':
		path = []
		tags = {}
		for i in e:
			if i.tag=='nd':
				if nodes.has_key(i.attrib['ref']):
					path.append(nodes[i.attrib['ref']])
				else:
					nd_not_found += 1
			if i.tag=='tag':
				tags[i.attrib['k']] = i.attrib['v']
		if tags.has_key('highway'):
			if tags['highway'] in ('path','track','steps','bridleway','footway','cycleway'):
				paths.append(path)
			else:
				roads.append(path)
		if tags.has_key('building'):
			buildings.append(path)
		if tags.has_key('natural'):
			if tags['natural'] in ('forest','wood','scrub'):
				vegetal.append(path)
			elif tags['natural']=='water':
				water.append(path)
			else:
				print tags['natural']
		if tags.has_key('landuse'):
			if tags['landuse'] in ('forest', 'meadow', 'farmyard', 'farmland', 'grass', 'orchard', 'village_green', 'recreation_ground'):
				vegetal.append(path)
			elif tags['landuse']=='basin':
				water.append(path)
			elif tags['landuse'] in ('residential','commercial','industrial','construction','retail','quarry'):
				buildings.append(path)
			else:
				print tags['landuse']
		if tags.get('name')=="Technopole de Sophia-Antipolis":
			bounds = path

print 'chemins et pistes = %d km'%(sum(map(lenOfPath,paths))/1000.0)
print 'routes = %d km'%(sum(map(lenOfPath,roads))/1000.0)
print 'zones commerciales, industrielles, residentielles, batiments... = %d ha'%(sum(map(areaOfPolygon,buildings))/10000.0)
print 'foret, garrigue, golfs, espaces verts... = %d ha'%(sum(map(areaOfPolygon,vegetal))/10000.0)
print 'eau et reservoirs = %d ha'%(sum(map(areaOfPolygon,water))/10000.0)
print 'superficie totale = %d ha'%(areaOfPolygon(bounds)/10000.0)
