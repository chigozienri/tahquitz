default:
	./gps.rb

photo:
	python photo_surveying.py

# The following target produces a file tahquitz.aig containing elevation data for the 1 km UTM square that contains Tahquitz Rock.
# The .aig file (Arc/Info ASCII Grid) is a plain text file in a pretty self-explanatory format: https://gdal.org/drivers/raster/aaigrid.html
# Cells are lat-lon squares with an edge size of 0.000277777778 degrees.
# The projection is described in the associated .prj file, which we throw away.
# To make the following target work, need:
#   apt-get install libgdal-dev gdal-bin python-gdal
#   pip install elevation
# lower left of UTM square, zone 11S, is
#   x=529 km, y=3735 km
# In NAD83 coords, this converts (using http://www.synnatschke.de/geo-tools/coordinate-converter.php ) to:
#   lat = 33.75468 N , lon = 116.68687 W
# Upper right is
#   lat = 33.76367 N , lon = 116.67604 W
# These data tell me that the ratios of meters to degrees are:
#   dx/dlon = 0.923361034164481e5       dy/dlat = 1.11234705228066e5
# Therefore the sizes of the cells are:
#   dx = 25.649 m       dy = 30.899 m
# output in UTM coords:
#   https://gis.stackexchange.com/a/8319/10112
#   https://epsg.io/32611
tahquitz.aig:
	eio clip -o tahquitz.tif --bounds -116.68687 33.75468 -116.67604 33.76367
	gdal_translate -a_srs EPSG:32611 -of AAIGrid -ot Int32 tahquitz.tif tahquitz.aig
	rm -f tahquitz.tif tahquitz.prj tahquitz.aig.aux.xml
