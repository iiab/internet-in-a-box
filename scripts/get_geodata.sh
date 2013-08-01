#!/bin/sh

echo Retrieving source data files from geonames.org
wget http://download.geonames.org/export/dump/admin1CodesASCII.txt
wget http://download.geonames.org/export/dump/admin2Codes.txt
wget http://download.geonames.org/export/dump/allCountries.zip
wget http://download.geonames.org/export/dump/alternateNames.zip
wget http://download.geonames.org/export/dump/cities1000.zip
wget http://download.geonames.org/export/dump/country_catagories.txt
wget http://download.geonames.org/export/dump/countryInfo.txt
wget http://download.geonames.org/export/dump/featureCodes_en.txt
wget http://download.geonames.org/export/dump/nocountry.txt
