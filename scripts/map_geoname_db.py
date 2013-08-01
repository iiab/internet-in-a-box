#!/usr/bin/env python

import os
import string
import sys
import sqlite3
from optparse import OptionParser
from pluralize import pluralize # locally provided function
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import codecs

Base = declarative_base()

# geonameid is used as primary key id
country_fields = ['iso', 'iso3', 'iso_numeric', 'fips', 'country', 'capital', 'area_km', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'id', 'neighbours', 'fips_equiv']

class Country(Base):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True)
    #iso = Column(String)
    #iso3 = Column(String)
    #iso_numeric = Column(String)
    #fips = Column(String)
    country = Column(String)
    capital = Column(String)
    area_km = Column(String)
    population = Column(Integer)
    continent = Column(String)
    #tld = Column(String)
    #currencycode = Column(String)
    currencyname = Column(String)
    #phone = Column(String)
    #postal_code_format = Column(String)
    #postal_code_regex = Column(String)
    languages = Column(String)   # comma delimited multivalue field - new table if useful
    #neighbours = Column(String)  # comma delimited multivalue field - new table if useful
    #fips_equiv = Column(String) 

place_fields = ('id', 'name', 'asciiname', 'altnames',
                'latitude', 'longitude', 'feature_class', 'feature_code',
                'country_code', 'cc2', 'admin1_code', 'admin2_code',
                'admin3_code', 'admin4_code', 'population', 'elevation',
                'gtopo30', 'timezone', 'modification_date')

class Place(Base):
    __tablename__ = 'place'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    asciiname = Column(String)
    #altnames = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    feature_class = Column(String)
    feature_code = Column(String)
    country_code = Column(String)
    cc2 = Column(String)
    admin1_code = Column(String)
    admin2_code = Column(String)
    admin3_code = Column(String)
    admin4_code = Column(String)
    population = Column(String)
    #elevation = Column(String)
    #gtopo30 = Column(String)
    #timezone = Column(String)
    #modification_date = Column(String)


# alternateNameId is used as primary key id
altname_fields = ('id', 'geonameid', 'isolanguage', 'alternate', 
                  'isPreferredName', 'isShortName', 'isColloquial', 'isHistoric')

class AltName(Base):
    __tablename__ = 'altnames'
    id = Column(Integer, primary_key=True)
    geonameid = Column(Integer)
    isolanguage = Column(String)
    alternate = Column(String)
    isPreferredName = Column(String)
    isShortName = Column(String)
    isColloquial = Column(String)
    isHistoric = Column(String)


admin1_fields = ('code', 'name', 'ascii_name', 'id')
admin2_fields = ('code', 'name', 'ascii_name', 'id')
class AdminDescriptor(Base):
    __tablename__ = 'admincodes'
    id = Column(Integer, primary_key=True)
    code = Column(String)
    name = Column(String)
    ascii_name = Column(String)

feature_fields = ('code', 'name', 'description')

def record_iterator(filename, field_names):
    with codecs.open(filename, encoding='utf-8') as f:
        for line in f:
            if line.lstrip().startswith('#'):
                continue
            yield dict(zip(field_names, line.split('\t')))


def builddb(db, insp, descriptor):
    filename, fields, cls = descriptor

    if cls is None:
        print "skipping " + filename
        return

    db_columns = [d['name'] for d in insp.get_columns(cls.__tablename__)]
    print db_columns

    print "Working on " + filename
    count = 0
    for r in record_iterator(filename, fields):
        filtered_data = {k : r[k] for k in r if k in db_columns}
        data = cls(**filtered_data)
        db.add(data)
        count += 1
        if (count % 100000) == 0:
            print count
            db.commit()
    db.commit()

def main():
    parser = OptionParser(description="Parse geonames.org geo data into a SQLite DB.")
    parser.add_option("--dbname", dest="db_filename", action="store",
                      default="geodata.db",
                      help="The geodata.db SQLite database")
    parser.add_option("--srcdir", dest="data_dir", action="store",
                      default="",
                      help="Specify directory in which data files can be found")
    (options, args) = parser.parse_args()

    recordsets = [
            ('allCountries.txt', place_fields, Place),
            ('countryInfo.txt', country_fields, Country),
            ('admin1CodesASCII.txt', admin1_fields, AdminDescriptor),
            ('admin2Codes.txt', admin2_fields, AdminDescriptor),
            ('alternateNames.txt', altname_fields, AltName),
            ('cities1000.txt', place_fields, None),
            ('featureCodes_en.txt', feature_fields, None),
            #('country_catagories.txt',)
            #('iso-languagecodes.txt',
            ]

    engine = create_engine('sqlite:///' + options.db_filename)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    dbSession = Session()
    insp = inspect(engine)

    for descriptor in recordsets:
        builddb(dbSession, insp, descriptor)

    
if __name__ == '__main__':
    main()


