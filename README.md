# osmaeras

Compute aeras and lenghts from OpenStreetMap data

## Step-by-step

### Get osm data
`wget http://download.geofabrik.de/europe/france/provence-alpes-cote-d-azur-latest.osm.pbf`

### Install Rust + cargo
```
curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env
```

### Install osmosis
```
wget https://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz
mkdir osmosis
mv osmosis-latest.tgz osmosis
cd osmosis
tar xvfz osmosis-latest.tgz
rm osmosis-latest.tgz
chmod a+x bin/osmosis
```

### Install python dependencies
`sudo pip install shapely pyproj geopandas`

### Build way/aera extractor
```
cd osmextract
cargo build --release
cd ..
```

### Get border of the zone you want
`./osmextract/target/release/osmextractfromname provence-alpes-cote-d-azur-latest.osm.pbf "Technopole de Sophia-Antipolis" > sophia.poly`
(2-3 minutes)

### Get a subset within borders
`osmosis/bin/osmosis --read-pbf provence-alpes-cote-d-azur-latest.osm.pbf --bounding-polygon file="sophia.poly" completeRelations=yes --write-xml file="sophia.osm"`

### Compute aeras and length
`python comp.py`

## Last results

OSM Data timestamp from geofabrik: 2019-01-30T21:14:05Z

Lineaire:

  chemins et pistes = 246.8 km
  rivieres et canaux = 29.5 km
  routes = 197.6 km

Superficies:

  Urbanisation = 653 ha (27.2%)
    dont mineral = 260 ha (10.8%)
      dont batiments = 110 ha (4.6%)
      dont parkings = 36 ha (1.5%)
      dont routes = 110 ha (4.6%)
      dont mines = 11 ha (0.5%)
      dont terrains de sport sans pelouse = 8 ha (0.3%)
    dont zones autour des batiments = 392 ha (16.3%)

  Espaces verts artificiels = 103 ha (4.3%)
    dont golfs = 84.3 ha (3.5%)
    dont agricole = 5.6 ha (0.2%)
    dont espaces verts = 26.1 ha (1.1%)
    dont reservoirs et piscines = 0.7 ha (0.0%)
    dont terrains de sport avec pelouse (hors golf) = 5.1 ha (0.2%)

  Espaces naturels = 1498 ha (62.4%)
    dont foret, garrigue, prairie = 1536 ha (64.0%)
    dont eau (lacs, etangs), hors rivieres etroites = 2 ha (0.1%)

  Non identifiee = 147 ha (6.1%)

superficie totale = 2400 ha

