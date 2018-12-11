# osmaeras
Compute aeras and enghts from OpenStreetMap data

# Step-by-step

## Get osm data
`wget http://download.geofabrik.de/europe/france/provence-alpes-cote-d-azur-latest.osm.pbf`

## Convert borders
```
wget https://svn.openstreetmap.org/applications/utils/osm-extract/polygons/ogr2poly.py
chmod +x ogr2poly.py
./ogr2poly.py -v parc_sophia_antipolis/parc_sophia_antipolis.shp # < gives error but creates file
```

## Get a subset within borders
`osmosis/bin/osmosis --read-pbf file="provence-alpes-cote-d-azur-latest.osm.pbf" --bounding-polygon file="parc_sophia_antipolis_0.poly" --write-xml file="sophia.osm"`

## Compute aeras and length
`python comp.py`

