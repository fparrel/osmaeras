# osmaeras
Compute aeras and enghts from OpenStreetMap data

# Step-by-step

## Get osm data
`wget http://download.geofabrik.de/europe/france/provence-alpes-cote-d-azur-latest.osm.pbf`

## Install Rust + cargo
```
curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env
```

## Install osmosis
TODO

## Build way/aera extractor
```
cd osmextract
cargo build --release
cd ..
```

## Get border of the zone you want
`./osmextract/target/release/osmextractfromname provence-alpes-cote-d-azur-latest.osm.pbf "Technopole de Sophia-Antipolis" > sophia.poly`

## Get a subset within borders
`osmosis/bin/osmosis --read-pbf provence-alpes-cote-d-azur-latest.osm.pbf --bounding-polygon file="sophia.poly" completeWays=yes --write-xml file="sophia.osm"`

## Compute aeras and length
`python comp.py`

