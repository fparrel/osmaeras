import xml.etree.ElementTree as ET
from math import sin, cos, atan2, sqrt, pi, radians
from shapely.geometry import Polygon, LineString
from shapely.ops import cascaded_union
import shapely.ops
import pyproj
from functools import partial
import geopandas
import json

def GeodeticDistGreatCircle(lat1,lon1,lat2,lon2):
  """Compute distance between two points of the earth geoid (approximated to a sphere)"""
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

#def lenOfPathWithin(path,bounds):
#  l = LineString(reproject(path))
#  bounds = Polygon(reproject(bounds))
#  l.intersection(bounds)
#  return l.length

def lenOfPathWithinPolygon(path,boundsshapely):
  l = LineString(reproject(path))
  l.intersection(boundsshapely)
  return l.length

def reproject(p):
  """Returns the x & y coordinates in meters using a sinusoidal projection"""
  out = [pyproj.transform(proj_latlon,proj4area,pt[1],pt[0]) for pt in p]
  return out

def areaOfPolygon(p1):
  """Calculates the area of an arbitrary polygon given its verticies"""
  p = reproject(p1)
  area = 0.0
  if len(p)==1:
    return 0.0
  for i in range(-1, len(p)-1):
    area += p[i][0] * (p[i+1][1] - p[i-1][1])
  return abs(area) / 2.0

def boundingBox(bounds):
  return min(lat for lat,lon in bounds),max(lat for lat,lon in bounds),min(lon for lat,lon in bounds),max(lon for lat,lon in bounds)

def deprojGeom(geom):
  deproj = partial(pyproj.transform, proj4area, proj_latlon)
  return shapely.ops.transform(deproj,geom)

def togeojson():
  urb = geopandas.GeoSeries(map(deprojGeom,urbanisation)).__geo_interface__['features']
  for feature in urb:
    feature['properties'] = {'color':'grey'}
    del feature['id']
  art = geopandas.GeoSeries(map(deprojGeom,artificial_green)).__geo_interface__['features']
  for feature in art:
    feature['properties'] = {'color':'yellow'}
    del feature['id']
  nat = geopandas.GeoSeries(map(deprojGeom,natural)).__geo_interface__['features']
  for feature in nat:
    feature['properties'] = {'color':'green'}
    del feature['id']
  bbox = boundingBox(bounds)
  bds = {'type': 'Feature','properties': {'color':'red','fill':'transparent'},'geometry':{'type':'Polygon','coordinates':[map(lambda xy:(xy[1],xy[0]),bounds+[bounds[0]])]},'bbox':[bbox[2],bbox[0],bbox[3],bbox[1]]}
  doc = {'type': 'FeatureCollection', 'features':urb+art+nat+[bds]}
  f = open('zonessophia.geojson','w')
  json.dump(doc,f)
  f.close()

proj_latlon = pyproj.Proj(proj='latlong',datum='WGS84')
proj4area = pyproj.Proj("+proj=sinu +R=6371009")

print 'Lecture du fichier et mise en cache...'
data = ET.parse('sophia.osm')

nodes = {}
for e in data.getroot():
  if e.tag=='node':
    nodes[e.attrib['id']] = float(e.attrib['lat']),float(e.attrib['lon'])

ways = {}
for e in data.getroot():
  if e.tag=='way':
    ways[e.attrib['id']] = map(lambda sube:nodes[sube.get('ref')], filter(lambda sube:sube.tag=='nd',e))

print 'Analyse...'

#paths_len = 0.0
#roads_aera = 0.0
#roads_len = 0.0
paths = []
roads = []
roadssh = []
buildings = []
built_zones = []
forests = []
golfs = []
stades = []
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
        paths.append(path)
        #paths_len += lenOfPath(path)
      else:
        roads.append(path)
        road = LineString(reproject(path))
        if tags.has_key('lanes'):
          # Lanes present => compute width
          width = int(tags['lanes'])*3.0
        elif tags.has_key('oneway'):
          width = 3.0
        else:
          width = 6.0
        roadssh.append(road.buffer(width/2))
        #l = lenOfPath(path)
        #roads_aera += l * width
        #roads_len += l
    if tags.has_key('building'):
      buildings.append(Polygon(reproject(path)))
    if tags.has_key('natural'):
      if tags['natural'] in ('forest','wood','scrub'):
        forests.append(Polygon(reproject(path)))
      elif tags['natural']=='water':
        lakes.append(Polygon(reproject(path)))
      else:
        print tags['natural']
    if tags.has_key('landuse'):
      if tags['landuse'] in ('forest', 'meadow', 'grass'):
        forests.append(Polygon(reproject(path)))
      elif tags['landuse'] in ('farmyard', 'farmland', 'orchard'):
        farming.append(Polygon(reproject(path)))
      elif tags['landuse'] in ('village_green', 'recreation_ground'):
        fake_green.append(Polygon(reproject(path)))
      elif tags['landuse']=='basin':
        reservoirs.append(Polygon(reproject(path)))
      elif tags['landuse'] in ('residential','commercial','industrial','construction','retail','quarry'):
        built_zones.append(Polygon(reproject(path)))
      else:
        print tags['landuse']
    if tags.get('leisure')=='golf_course':
      golfs.append(Polygon(reproject(path)))
    if tags.get('leisure')=='pitch':
      stades.append(Polygon(reproject(path)))
    if tags.get('leisure')=='swimming_pool':
      reservoirs.append(Polygon(reproject(path)))
    if tags.has_key('waterway'):
      rivers.append(path)
    if tags.get('amenity')=='parking' or tags.get('landuse')=='garages':
      parkings.append(Polygon(reproject(path)))
    if tags.get('name')=="Technopole de Sophia-Antipolis":
      bounds = path
  elif e.tag=='relation':
    tags = {}
    outers = []
    inners = []
    for i in e:
      if i.tag=='member' and i.get('role')=='outer':
        outers.append(i.get('ref'))
      elif i.tag=='member' and i.get('role')=='inner':
        inners.append(i.get('ref'))
      elif i.tag=='tag':
        tags[i.attrib['k']] = i.attrib['v']
    if tags.get('landuse') in ('forest', 'meadow', 'grass'):
      #print 'here',outers,inners
      #TODO: some ref not found
      outers = filter(lambda x:x!=None,[ways.get(ref) for ref in outers])
      inners = filter(lambda x:x!=None,[ways.get(ref) for ref in inners])
      forest = cascaded_union(map(lambda outer:Polygon(reproject(outer)),outers)).difference(cascaded_union(map(lambda outer:Polygon(reproject(outer)),inners)))
      forests.append(forest)

if len(nd_not_found)>0:
  print 'WARNING: somes nodes were not found'

print 'Recoupement et regroupements...'

boundsshapely = Polygon(reproject(bounds))

roadssh = cascaded_union(roadssh).intersection(boundsshapely)

built_zones = cascaded_union(built_zones).intersection(boundsshapely)
buildings = cascaded_union(buildings).intersection(boundsshapely)
parkings = cascaded_union(parkings).intersection(boundsshapely)
urbanisation = cascaded_union([built_zones,buildings,parkings,roadssh])

fake_green = cascaded_union(fake_green).intersection(boundsshapely)
golfs = cascaded_union(golfs).intersection(boundsshapely)
farming = cascaded_union(farming).intersection(boundsshapely)
reservoirs = cascaded_union(reservoirs).intersection(boundsshapely)
stades = cascaded_union(stades).intersection(boundsshapely)
artificial_green = cascaded_union([fake_green,golfs,farming,reservoirs,stades])

forests = cascaded_union(forests).intersection(boundsshapely)
lakes = cascaded_union(lakes).intersection(boundsshapely)
natural = cascaded_union([forests,lakes])

natural = natural.difference(urbanisation) # Mainly for removing roads in forests

print 'Sauvegarde...'

togeojson()

paths_len2 = 0.0
for path in paths:
  paths_len2 += lenOfPathWithinPolygon(path,boundsshapely)

roads_len2 = 0.0
for road in roads:
  roads_len2 += lenOfPathWithinPolygon(road,boundsshapely)

print
print 'Lineaire:'
print
print '  chemins et pistes = %.1f km'%(paths_len2/1000.0)
print '  rivieres et canaux = %.1f km'%(sum(map(lenOfPath,rivers))/1000.0)
print '  routes = %.1f km'%(roads_len2/1000.0)
print
print 'Superficies:'
print
print '  Urbanisation = %.0f ha' % (urbanisation.area/10000.0)
print '    dont batiments = %.0f ha (%.1f%%)'%(buildings.area/10000.0,buildings.area*100.0/boundsshapely.area)
print '    dont parkings = %.0f ha'%(parkings.area/10000.0)
print '    dont routes = %.0f ha'%(roadssh.area/10000.0)
print
print '  Espaces verts artificiels = %.0f ha' % (artificial_green.area/10000.0)
print '    dont golfs = %.1f ha'%(golfs.area/10000.0)
print '    dont agricole = %.1f ha'%(farming.area/10000.0)
print '    dont espaces verts = %.1f ha'%(fake_green.area/10000.0)
print '    dont reservoirs et piscines = %.1f ha'%(reservoirs.area/10000.0)
print '    dont terrains de sport (hors golf) = %.1f ha'%(stades.area/10000.0)
print
print '  Espaces naturels = %.0f ha'%(natural.area/10000.0)
print '    dont foret, garrigue, prairie = %.0f ha'%(forests.area/10000.0)
print '    dont eau (lacs, etangs), hors rivieres etroites = %.0f ha'%(lakes.area/10000.0)
print
print '  Non identifiee = %.0f ha'%((boundsshapely.area-cascaded_union([urbanisation,artificial_green,natural]).area)/10000.0)
print
print 'superficie totale = %.0f ha'%(boundsshapely.area/10000.0)

#TODO: donner une largeur aux rivieres?
