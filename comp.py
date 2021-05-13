import xml.etree.ElementTree as ET
from math import sin, cos, atan2, sqrt, pi, radians
from shapely.geometry import Polygon, LineString
from shapely.ops import cascaded_union
import shapely.ops
import pyproj
from functools import partial
import geopandas
import json
from sys import stdout

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
  return map(lambda pt: pyproj.transform(proj_latlon,proj4area,pt[1],pt[0]), p)

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

def geojsondump(geom,fname):
  f = open('%s.geojson'%fname.strip('.geojson'),'w')
  f.write(geopandas.GeoSeries(map(deprojGeom,geom)).to_json())
  f.close()

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
  bds = geopandas.GeoSeries(deprojGeom(bounds)).__geo_interface__['features']
  bds[0]['properties'] = {'color':'red','fill':'transparent'}
  del bds[0]['id']
  #bds = {'type': 'Feature','properties': {'color':'red','fill':'transparent'},'geometry':{'type':'Polygon','coordinates':[map(lambda xy:(xy[1],xy[0]),bounds+[bounds[0]])]},'bbox':[minlon,minlat,maxlon,maxlat]}
  doc = {'type': 'FeatureCollection', 'features':urb+art+nat+bds}
  f = open('zonessophia.geojson','w')
  json.dump(doc,f)
  f.close()

proj_latlon = pyproj.Proj(proj='latlong',datum='WGS84')
proj4area = pyproj.Proj("+proj=sinu +R=6371009")

print('Lecture du fichier et mise en cache...')
data = ET.parse('sophia.osm')

nodes = {}
for e in data.getroot():
  if e.tag=='node':
    nodes[e.attrib['id']] = float(e.attrib['lat']),float(e.attrib['lon'])

ways = {}
for e in data.getroot():
  if e.tag=='way':
    ways[e.attrib['id']] = map(lambda sube:nodes[sube.get('ref')], filter(lambda sube:sube.tag=='nd',e))

print('Analyse...')

pathlines = []
roads = []
roadlines = []
buildings = []
built_zones = []
forests = []
golfs = []
pitches_green = [] # Soccer, rubgy...
pitches_mineral = [] # Tennis, basketball...
lakes = []
reservoirs = []
farming = []
fake_green = []
riverlines = []
parkings = []
quarries = []
nd_not_found = []
nbnodes = 0
nbnodestotal = len(data.getroot())
for e in data.getroot():
  nbnodes += 1
  stdout.write('\r%d / %d nodes' % (nbnodes,nbnodestotal))
  tags = {}
  geom = None
  if e.tag=='way':
    way = []
    for i in e:
      if i.tag=='nd':
        if nodes.has_key(i.attrib['ref']):
          way.append(nodes[i.attrib['ref']])
        else:
          nd_not_found.append(i.attrib['ref'])
      if i.tag=='tag':
        tags[i.attrib['k']] = i.attrib['v']
    reprojected = reproject(way)
    if way[-1]==way[0]:
      geom = Polygon(reprojected)
    else:
      geom = LineString(reprojected)
  elif e.tag=='relation':
    outers = []
    inners = []
    for i in e:
      if i.tag=='member' and i.get('role')=='outer':
        outers.append(i.get('ref'))
      elif i.tag=='member' and i.get('role')=='inner':
        inners.append(i.get('ref'))
      elif i.tag=='tag':
        tags[i.attrib['k']] = i.attrib['v']
    if tags.get('type')=='multipolygon':
      outers = [ways.get(ref) for ref in outers]
      inners = [ways.get(ref) for ref in inners]
      try:
        geom = cascaded_union(map(lambda way:Polygon(reproject(way)),outers)).difference(cascaded_union(map(lambda way:Polygon(reproject(way)),inners)))
      except Exception,exc:
        print('Warning: check %s.geojson against https://www.openstreetmap.org/relation/%s'%(e.attrib['id'],e.attrib['id']))
        # Some multipolygon relations are defined as multines instead of multipolygon. here is the workaroud
        # Merge LineStrings if needed
        prevlen = len(outers)
        while True:
          for i1 in range(0,len(outers)):
            for i2 in range(0,len(outers)):
              o1=outers[i1]
              o2=outers[i2]
              if len(o1)>0 and len(o2)>0 and o1!=o2 and o1[0]==o2[-1]:
                outers[i2].extend(o1)
                outers[i1] = []
          outers = filter(lambda o: len(o)>0,outers)
          if len(outers)==prevlen:
            break
          prevlen = len(outers)
        # And convert back to polygon(s)
        outs = map(lambda way:Polygon(reproject(way)),outers)
        inn = cascaded_union(map(lambda way:Polygon(reproject(way)),inners))
        geom = cascaded_union(outs).difference(inn)
        geojsondump([geom],e.attrib['id'])
  if geom!=None:
    if tags.has_key('highway'):
      if tags['highway'] in ('path','track','steps','bridleway','footway','cycleway'):
        pathlines.append(geom)
      else:
        if tags.has_key('lanes'):
          # Lanes present => compute width
          width = int(tags['lanes'])*3.0
        elif tags.has_key('oneway'):
          width = 3.0
        else:
          width = 6.0
        roadlines.append(geom)
        roads.append(geom.buffer(width/2))
    elif tags.has_key('area:highway'):
      roads.append(geom)
    if tags.has_key('building'):
      buildings.append(geom)
    if tags.get('power')=='plant':
      buildings.append(geom)
    if tags.has_key('natural'):
      if tags['natural'] in ('forest','wood','scrub','heath'):
        forests.append(geom)
      elif tags['natural']=='water':
        lakes.append(geom)
      elif tags['natural'] in ('coastline','ridge'):
        pass # ignore
      elif tags['natural']=='sand':
        quarries.append(geom) #TODO: quarries = quarries + natural mineral
      else:
        raise Exception('unknow value for tag natural: %s' % tags['natural'])
    if tags.has_key('landuse'):
      if tags['landuse'] in ('forest', 'meadow', 'grass', 'frass'):
        forests.append(geom)
      elif tags['landuse'] in ('farmyard', 'farmland', 'orchard'):
        farming.append(geom)
      elif tags['landuse'] in ('village_green', 'recreation_ground', 'flowerbed'):
        fake_green.append(geom)
      elif tags['landuse']=='basin':
        reservoirs.append(geom)
      elif tags['landuse']=='quarry':
        quarries.append(geom)
      elif tags['landuse'] in ('residential','commercial','industrial','construction','retail'):
        built_zones.append(geom)
      else:
        raise Exception('unknow value for tag landuse: %s' % tags['landuse'])
    if tags.get('leisure')=='park':
      fake_green.append(geom)
    if tags.get('leisure')=='golf_course':
      golfs.append(geom)
    if tags.get('leisure')=='pitch':
      if tags.get('sport') in ('soccer','football',None):
        pitches_green.append(geom)
      else:
        pitches_mineral.append(geom)
    if tags.get('leisure')=='swimming_pool':
      reservoirs.append(geom)
    if tags.has_key('waterway'):
      riverlines.append(geom)
    if tags.get('amenity')=='parking' or tags.get('landuse')=='garages':
      parkings.append(geom)
    if tags.get('name')=="Technopole de Sophia-Antipolis":
      bounds = geom

print('')

if len(nd_not_found)>0:
  print('WARNING: %d nodes were not found'%len(nd_not_found))

print('Recoupement et regroupements...')

roads = cascaded_union(roads).intersection(bounds)

quarries = cascaded_union(quarries).intersection(bounds)
built_zones = cascaded_union(built_zones).intersection(bounds)
buildings = cascaded_union(buildings).intersection(bounds)
parkings = cascaded_union(parkings).intersection(bounds)
pitches_mineral = cascaded_union(pitches_mineral).intersection(bounds)
mineral = cascaded_union([buildings,parkings,roads,quarries,pitches_mineral])
urbanisation = cascaded_union([built_zones,mineral])

fake_green = cascaded_union(fake_green).intersection(bounds)
golfs = cascaded_union(golfs).intersection(bounds)
farming = cascaded_union(farming).intersection(bounds)
reservoirs = cascaded_union(reservoirs).intersection(bounds)
pitches_green = cascaded_union(pitches_green).intersection(bounds)
artificial_green = cascaded_union([fake_green,golfs,farming,reservoirs,pitches_green])

forests = cascaded_union(forests).intersection(bounds)
lakes = cascaded_union(lakes).intersection(bounds)
natural = cascaded_union([forests,lakes])

natural = natural.difference(urbanisation) # Mainly for removing roads in forests
artificial_green = artificial_green.difference(urbanisation) # Remove buildings and roads in parks
artificial_green = artificial_green.difference(natural) # Remove forests inside parks

allidentified = cascaded_union([urbanisation,artificial_green,natural])

print('Sauvegarde...')

togeojson()

paths_len = sum([line.intersection(bounds).length for line in pathlines])
roads_len = sum([line.intersection(bounds).length for line in roadlines])
rivers_len = sum([line.intersection(bounds).length for line in riverlines])

print('** Resultats: **')
print
print('Lineaire:')
print
print('  chemins et pistes = %.1f km'%(paths_len/1000.0))
print('  rivieres et canaux = %.1f km'%(rivers_len/1000.0))
print('  routes = %.1f km'%(roads_len/1000.0))
print
print('Superficies:')
print
print('  Urbanisation = %.0f ha (%.1f%%)' % (urbanisation.area/10000.0,urbanisation.area*100.0/bounds.area))
print('    dont mineral = %.0f ha (%.1f%%)'%(mineral.area/10000.0,mineral.area*100.0/bounds.area))
print('      dont batiments = %.0f ha (%.1f%%)'%(buildings.area/10000.0,buildings.area*100.0/bounds.area))
print('      dont parkings = %.0f ha (%.1f%%)'%(parkings.area/10000.0,parkings.area*100.0/bounds.area))
print('      dont routes = %.0f ha (%.1f%%)'%(roads.area/10000.0,roads.area*100.0/bounds.area))
print('      dont mines = %.0f ha (%.1f%%)'%(quarries.area/10000.0,quarries.area*100.0/bounds.area))
print('      dont terrains de sport sans pelouse = %.0f ha (%.1f%%)'%(pitches_mineral.area/10000.0,pitches_mineral.area*100.0/bounds.area))
print('    dont zones autour des batiments = %.0f ha (%.1f%%)'%((urbanisation.area-mineral.area)/10000.0,(urbanisation.area-mineral.area)*100.0/bounds.area))
print
print('  Espaces verts artificiels = %.0f ha (%.1f%%)' % (artificial_green.area/10000.0,artificial_green.area*100.0/bounds.area))
print('    dont golfs = %.1f ha (%.1f%%)'%(golfs.area/10000.0,golfs.area*100.0/bounds.area))
print('    dont agricole = %.1f ha (%.1f%%)'%(farming.area/10000.0,farming.area*100.0/bounds.area))
print('    dont espaces verts = %.1f ha (%.1f%%)'%(fake_green.area/10000.0,fake_green.area*100.0/bounds.area))
print('    dont reservoirs et piscines = %.1f ha (%.1f%%)'%(reservoirs.area/10000.0,reservoirs.area*100.0/bounds.area))
print('    dont terrains de sport avec pelouse (hors golf) = %.1f ha (%.1f%%)'%(pitches_green.area/10000.0,pitches_green.area*100.0/bounds.area))
print
print('  Espaces naturels = %.0f ha (%.1f%%)'%(natural.area/10000.0,natural.area*100.0/bounds.area))
print('    dont foret, garrigue, prairie = %.0f ha (%.1f%%)'%(forests.area/10000.0,forests.area*100.0/bounds.area))
print('    dont eau (lacs, etangs), hors rivieres etroites = %.0f ha (%.1f%%)'%(lakes.area/10000.0,lakes.area*100.0/bounds.area))
print
print('  Non identifiee = %.0f ha (%.1f%%)'%((bounds.area-allidentified.area)/10000.0,100.0-allidentified.area*100.0/bounds.area))
print
print('superficie totale = %.0f ha'%(bounds.area/10000.0))

#TODO: donner une largeur aux rivieres?
