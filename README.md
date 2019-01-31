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

### Get a subset within borders
`osmosis/bin/osmosis --read-pbf provence-alpes-cote-d-azur-latest.osm.pbf --bounding-polygon file="sophia.poly" completeWays=yes --write-xml file="sophia.osm"`

### Compute aeras and length
`python comp.py`

## Last results

Correction des erreurs (a ignorer si moins d'un kilometre)
  Chemins hors frontieres = 159 m
  Routes hors urbanisation= -80 m

Lineaire:

  chemins et pistes = 249.3 km
  rivieres et canaux = 41.4 km
  routes = 212.3 km

Superficies:

  Urbanisation: 596 ha
    dont batiments = 106 ha
    dont parkings = 36 ha
    dont routes = 103 ha

  Espaces verts artificiels: 105 ha
    dont golfs = 84.3 ha
    dont agricole = 5.6 ha
    dont espaces verts = 2.3 ha
    dont reservoirs et piscines = 0.7 ha
    dont terrains de sport (hors golf) = 12.5 ha

  Espaces naturels = 1499 ha
    dont foret, garrigue, prairie = 1533 ha
    dont eau (lacs, etangs), hors rivieres etroites = 2 ha

superficie totale = 2400 ha
superficie totale identifiee = 2189 ha

