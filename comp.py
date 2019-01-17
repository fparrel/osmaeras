import xml.etree.ElementTree as ET
from math import sin, cos, atan2, sqrt, pi, radians
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

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

paths_len = 0.0
roads_aera = 0.0
roads_len = 0.0
buildings = []
built_zones = []
forests = []
golfs = []
lakes = []
reservoirs = []
farming = []
fake_green = []
rivers = []
parkings = []
nd_not_found = []
for e in data.getroot():
	if e.tag=='way':
		path = []
		tags = {}
		for i in e:
			if i.tag=='nd':
				if nodes.has_key(i.attrib['ref']):
					path.append(nodes[i.attrib['ref']])
				else:
					nd_not_found.append(i.attrib['ref'])
			if i.tag=='tag':
				tags[i.attrib['k']] = i.attrib['v']
		if tags.has_key('highway'):
			if tags['highway'] in ('path','track','steps','bridleway','footway','cycleway'):
				#paths.append(path)
                                paths_len += lenOfPath(path)
			else:
				#roads.append(path)
                                if tags.has_key('lanes'):
                                    # Lanes present => compute width
                                    width = int(tags['lanes'])*3.0
                                elif tags.has_key('oneway'):
                                    width = 3.0
                                else:
                                    width = 6.0
                                l = lenOfPath(path)
                                roads_aera += l * width
                                roads_len += l
		if tags.has_key('building'):
			buildings.append(path)
		if tags.has_key('natural'):
			if tags['natural'] in ('forest','wood','scrub'):
				forests.append(path)
			elif tags['natural']=='water':
				lakes.append(path)
			else:
				print tags['natural']
		if tags.has_key('landuse'):
			if tags['landuse'] in ('forest', 'meadow', 'grass'):
				forests.append(path)
                        elif tags['landuse'] in ('farmyard', 'farmland', 'orchard'):
                                farming.append(path)
                        elif tags['landuse'] in ('village_green', 'recreation_ground'):
                                fake_green.append(path)
			elif tags['landuse']=='basin':
				reservoirs.append(path)
			elif tags['landuse'] in ('residential','commercial','industrial','construction','retail','quarry'):
				built_zones.append(path)
			else:
				print tags['landuse']
                if tags.get('leisure')=='golf_course':
                        golfs.append(path)
                if tags.has_key('waterway'):
                        rivers.append(path)
                if tags.get('amenity')=='parking' or tags.get('landuse')=='garages':
                        parkings.append(path)
		if tags.get('name')=="Technopole de Sophia-Antipolis":
			bounds = path

def unions(polygons):
  return map(lambda x:list(x.exterior.coords),cascaded_union(map(lambda x:Polygon(x),polygons)).geoms)

def withinUnionAera(polygons,polygon):
  p = Polygon(reproject(polygon))
  o = cascaded_union(map(lambda x:Polygon(reproject(x)).intersection(p),polygons))
  return sum(map(lambda x:x.area,o))

def areaOfPolygons(ps,bounds):
  print sum(map(areaOfPolygon,ps))
  print sum(map(areaOfPolygon,within(ps,bounds)))
  return sum(map(areaOfPolygon,unions(ps)))

if len(nd_not_found)>0:
  print 'WARNING: somes nodes were not found'

print 'Lineaire:'
print
print '  chemins et pistes = %d km'%(paths_len/1000.0)
print '  rivieres et canaux = %d km'%(sum(map(lenOfPath,rivers))/1000.0)
print
print '  routes = %d km %d ha'%(roads_len/1000.0,roads_aera/10000.0)
print
print 'Superficies:'
print
print '  Urbanisation: %d ha' % (withinUnionAera(built_zones+buildings+parkings,bounds)/10000.0)
print '    dont batiments = %d ha'%(withinUnionAera(buildings,bounds)/10000.0)
print '    dont parkings = %d ha'%(withinUnionAera(parkings,bounds)/10000.0)
print
print '  Espaces verts artificiels: %d ha' % (withinUnionAera(fake_green+golfs+farming+reservoirs,bounds)/10000.0)
print '    dont golfs = %d ha'%(withinUnionAera(golfs,bounds)/10000.0)
print '    dont agricole = %d ha'%(withinUnionAera(farming,bounds)/10000.0)
print '    dont espaces verts = %d ha'%(withinUnionAera(fake_green,bounds)/10000.0)
print '    dont reservoirs = %d ha'%(withinUnionAera(reservoirs,bounds)/10000.0)
print
print '  Espaces naturels = %d ha'%(withinUnionAera(forests+lakes,bounds)/10000.0)
print '    dont foret, garrigue, prairie = %d ha'%(withinUnionAera(forests,bounds)/10000.0)
print '    dont eau (lacs, etangs), hors rivieres etroites = %d ha'%(withinUnionAera(lakes,bounds)/10000.0)
print
print 'superficie totale = %d ha'%(areaOfPolygon(bounds)/10000.0)
print 'superficie totale identifiee = %d ha'%(withinUnionAera(built_zones+buildings+parkings+fake_green+golfs+farming+reservoirs+forests+lakes,bounds)/10000.0)

#TODO: routes a compter dans urbanisation
#TODO: restreindre les donnees lineaiares a l'interieur de sophia
#TODO: donner une largeur aux rivieres?


