# osmaeras

Compute aeras and lenghts from OpenStreetMap data

## Step-by-step

### Get osm data
```sh
wget http://download.geofabrik.de/europe/france/provence-alpes-cote-d-azur-latest.osm.pbf
```

### Install Rust + cargo
```sh
curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env
```

### Install osmosis
```sh
mkdir -p osmosis
pushd osmosis
wget https://github.com/openstreetmap/osmosis/releases/download/0.48.3/osmosis-0.48.3.tgz  
tar xvfz osmosis-*.tgz
rm osmosis-*.tgz
chmod a+x bin/osmosis
popd
```

### Install python dependencies
```sh
pip install shapely pyproj geopandas pytz
```
PS: you may need to `sudo`. In this case check that modules are imported for your user.

### Build way/aera extractor
```sh
pushd osmextract
cargo build --release
popd
```

### Get border of the zone you want
```sh
./osmextract/target/release/osmextractfromname provence-alpes-cote-d-azur-latest.osm.pbf "Technopole de Sophia-Antipolis" > sophia.poly
```
(lasts 2-3 minutes)

### Get a subset within borders
```sh
osmosis/bin/osmosis --read-pbf provence-alpes-cote-d-azur-latest.osm.pbf --bounding-polygon file="sophia.poly" completeRelations=yes --write-xml file="sophia.osm"
```

### Compute aeras and length
```sh
python comp.py
```

### Convert geojson to kml
```sh
./geojson2kml.py zonessophia.geojson
```

## Last results

```
OSM Data timestamp from geofabrik: 2021-05-11

Lineaire:

  chemins et pistes = 263.9 km
  rivieres et canaux = 30.4 km
  routes = 212.7 km

Superficies:

  Urbanisation = 669 ha (27.9%)
    dont mineral = 273 ha (11.4%)
      dont batiments = 112 ha (4.6%)
      dont parkings = 39 ha (1.6%)
      dont routes = 119 ha (5.0%)
      dont mines = 11 ha (0.5%)
      dont terrains de sport sans pelouse = 9 ha (0.4%)
    dont zones autour des batiments = 396 ha (16.5%)

  Espaces verts artificiels = 96 ha (4.0%)
    dont golfs = 83.9 ha (3.5%)
    dont agricole = 5.6 ha (0.2%)
    dont espaces verts = 26.2 ha (1.1%)
    dont reservoirs et piscines = 0.6 ha (0.0%)
    dont terrains de sport avec pelouse (hors golf) = 3.6 ha (0.1%)

  Espaces naturels = 1508 ha (62.8%)
    dont foret, garrigue, prairie = 1554 ha (64.7%)
    dont eau (lacs, etangs), hors rivieres etroites = 2 ha (0.1%)

  Non identifiee = 127 ha (5.3%)

superficie totale = 2400 ha
```

## Démarche suivie

Etapes en format latitude, longitude décimale (précision: nanodregrés):

Le fichier correspondant à la Zone PACA est récupéré sur le serveur http://geofabrik.de Ce fichier fige les données OpenStreetMap (http://openstreetmaps.org) à un instant donné (habituellement la veilla au soir). Un programme codé en Rust permet d'extraire le polygone représentant les limites de la Technopole Sophia-Antipolis de ce fichier. J'ai choisi d'utiliser un code compilé choisi pour la vitesse d'exécution. Ensuite l'outil osmosis permet d'extraire tous les points inclus dans ce polygone ainsi que leurs dépendances (donc on obtient également des points extérieurs à la technopole via ce système de dépendences).

Etapes en coordonnés metriques (x, y en mètres):

Le fichier représentant les données OSM relatives à Sophia-Antipolis est ensuite analysé. Une projection sinusoïdale (https://fr.wikipedia.org/wiki/Projection_sinuso%C3%AFdale) permet de convertir les latitudes longitudes en mètres, afin de pouvoir calculer les superficies et distances par méthode euclidienne. La projection sinusoïdale a la propriété de conserver les superficies (en revanche on perd de la précision sur les distances qui nous importent moins). Nous choisissons un rayon terrestre de 6371009m, rayon moyen donc assez précis autour des latitudes voisines de 45 degrés. Cette projection est faite via la librarie pyproj/PROJ4 (https://proj4.org/).
Chaque polygone (`way` fermé chez OSM) et multipolygone (`relation[type=multipolygon]` contenant deux listes de polygones: les exterieurs et les intérieurs ("trous")), est converti en objet géométrique de la librairie Shapely (https://github.com/Toblerity/Shapely), puis placé dans la sous-catégorie correspondante. Pour les routes on utilise la librarie Shapely pour leur donner une épaisseur. On utilise le tag `width` lorsqu'il est renseigné sur OSM, sinon on compte 3m par voie lorsque le nombre de voies est renseigné, et 6m par defaut lorsque rien n'est renseigné.
Les objets de la même sous-catégorie sont ensuite unis (pour éviter les doubles comptages par exemple un maison sur une zone résidentielle), et intersectés avec les limites de Sophia-Antipolis (car du fait du système de dépendances on peut obtenir des points en dehors de ces limites).
Les sous-catégories sont regroupées en catégories (par union également toujours pour éviter les doubles comptages).
Les zones urbaines sont enlevées des zones naturelles et des espaces verts (exemple: pour les routes dans les parcs et forêts), et les zones naturelles sont enlevées des espaces verts (pour les bois encalvés dans le parcs).
La librairies Shapely calcule les surfaces et distances totales.

Etapes de nouveau en format latitude, longitude décimale:

Ensuite chaque objet géométrique Shapely de type polygone ou multipolygone est reconverti en latitude longitude, puis exporté au format geojson (http://geojson.org/) avec les zones colorées en gris, jaune ou vert, afin de pouvoir vérifier visuellement la pertinence des résultats. On converti également au format .kml pour une intégration dans google maps.
