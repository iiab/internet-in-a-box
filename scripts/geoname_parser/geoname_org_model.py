#!/usr/bin/env python

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, inspect
from sqlalchemy.orm import sessionmaker

__all__ = ["country_fields", "place_fields", "altname_fields",
        "admin1_fields", "admin2_fields", "feature_fields",
        "PlaceInfo", "PlaceNames", "create_indices", "drop_indices"]

Base = declarative_base()

# geonameid is used as primary key id
country_fields = ('iso', 'iso3', 'iso_numeric', 'fips', 'country', 'capital', 
                  'area_km', 'population', 'continent', 'tld', 'currencycode', 
                  'currencyname', 'phone', 'postal_code_format', 'postal_code_regex', 
                  'languages', 'id', 'neighbours', 'fips_equiv')
place_fields = ('id', 'name', 'asciiname', 'altnames',
                'latitude', 'longitude', 'feature_class', 'feature_code',
                'country_code', 'cc2', 'admin1_code', 'admin2_code',
                'admin3_code', 'admin4_code', 'population', 'elevation',
                'gtopo30', 'timezone', 'modification_date')
# alternateNameId is used as primary key id
altname_fields = ('id', 'geonameid', 'isolanguage', 'alternate', 'isPreferredName', 
                  'isShortName', 'isColloquial', 'isHistoric')
admin1_fields = ('code', 'name', 'ascii_name', 'id')
admin2_fields = ('code', 'name', 'ascii_name', 'id')
feature_fields = ('code', 'name', 'description')

class PlaceInfo(Base):
    __tablename__ = "placeinfo"

    id = Column(Integer, primary_key=True) # geoid
    name = Column(String)
    asciiname = Column(String)
    admin4_id = Column(Integer)
    admin3_id = Column(Integer)
    admin2_id = Column(Integer)
    admin1_id = Column(Integer)
    country_id = Column(Integer)
    latitude = Column(String)
    longitude = Column(String)
    population = Column(String, index=True)
    feature_code = Column(String)
    feature_name = Column(String)

class PlaceNames(Base):
    __tablename__ = "placenames"
    id = Column(Integer, primary_key=True) # generated row id's
    geonameid = Column(Integer, index=True)
    isolanguage = Column(String)
    alternate = Column(String)
    isPreferredName = Column(String)
    isShortName = Column(String)
    isColloquial = Column(String)
    isHistoric = Column(String)

def drop_indices(session):
    session.execute('DROP INDEX IF EXISTS ix_placeinfo_population')
    session.execute('DROP INDEX IF EXISTS ix_placenames_geonameid')

def create_indices(session):
    session.execute('CREATE INDEX ix_placenames_geonameid ON placenames (geonameid)')
    session.execute('CREATE INDEX ix_placeinfo_population ON placeinfo (population)')
