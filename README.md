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
wget https://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz
mkdir osmosis
mv osmosis-latest.tgz osmosis
cd osmosis
tar xvfz osmosis-latest.tgz
rm osmosis-latest.tgz
chmod a+x bin/osmosis
```

### Install python dependencies
```sh
sudo pip install shapely pyproj geopandas
```

### Build way/aera extractor
```sh
cd osmextract
cargo build --release
cd ..
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
