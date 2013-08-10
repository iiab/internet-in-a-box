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
    admin2_id = Column(Integer)
    admin1_id = Column(Integer)
    country_id = Column(Integer)
    latitude = Column(String)
    longitude = Column(String)
    population = Column(String)
    feature_code = Column(String)
    feature_name = Column(String)

class PlaceNames(Base):
    __tablename__ = "placenames"
    id = Column(Integer, primary_key=True) # generated row id's
    geonameid = Column(Integer)
    isolanguage = Column(String)
    alternate = Column(String)
    isPreferredName = Column(String)
    isShortName = Column(String)
    isColloquial = Column(String)
    isHistoric = Column(String)


def record_iterator(filename, field_names):
    with codecs.open(filename, encoding='utf-8') as f:
        for line in f:
            if line.lstrip().startswith('#'):
                continue
            yield dict(zip(field_names, map(unicode.strip, line.split('\t'))))


def build_dictionary(filename, fields, key):
    """Return a dictionary of records keyed on the id"""
    assert key in fields

    results = {}
    for r in record_iterator(filename, fields):
        if r[key] != '':
            results[r[key]] = r
        else:
            print "Skipping record with missing " + key + ": " + r

    return results

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

def place_admin1_id(aux_data, rec):
    if rec['admin1_code'] == '':
        return '';
    admin1code = "%s.%s" % (rec['country_code'], rec['admin1_code'])
    try:
        return aux_data['admin1'][admin1code]['id']
    except KeyError:
        print u''.join((u"Failed to find admin1 code for ", admin1code, u" on ", rec['id'])).encode('utf-8')
        return ''

def place_admin2_id(aux_data, rec):
    if rec['admin1_code'] == '' or rec['admin2_code'] == '':
        return '';
    admin2code = "%s.%s.%s" % (rec['country_code'], rec['admin1_code'], rec['admin2_code'])
    try:
        return aux_data['admin2'][admin2code]['id']
    except KeyError:
        print u''.join((u"Failed to find admin2 code for ", admin2code, u" on ", rec['id'])).encode('utf-8')
        return ''

def place_country_id(aux_data, rec):
    countrycode = rec['country_code']
    try:
        return aux_data['countries'][countrycode]['id']
    except KeyError:
        print u''.join((u"Failed to find country code for ", countrycode, u" on ", rec['id'])).encode('utf-8')
        return ''

def place_feature_name(aux_data, rec):
    feature = "%s.%s" % (rec['feature_class'], rec['feature_code'])
    try:
        return aux_data['features'][feature]['name']
    except KeyError:
        print u''.join((u"Failed to find feature code for ", feature, u" on ", rec['id'])).encode('utf-8')
        return ''

def try_for_improved_population_estimate(aux_data, data):
    if data['id'] in aux_data['cities']:
        citypop = aux_data['cities'][data['id']]['population']
        if data['population'] != citypop:
            if data['population'] != 0:
                print "city population mismatch on %d: %d %d" % (
                        data['id'], data['population'], citypop)
            data['population'] = citypop
    elif data['id'] in aux_data['countries']:
        countrypop = aux_data['countries']['population']
        if data['population'] != countrypop:
            if data['population'] != 0:
                print "country population mismatch on %d: %d %d" % (
                        data['id'], data['population'], countrypop)
            data['population'] = citypop

def make_place_info(aux_data, rec):
    data = {}

    direct_copy_fields = ('id', 'latitude', 'longitude', 'population', 'feature_code', 'name', 'asciiname')
    for f in direct_copy_fields:
        data[f] = rec[f]

    data['admin2_id'] = place_admin2_id(aux_data, rec)
    data['admin1_id'] = place_admin1_id(aux_data, rec)
    data['country_id'] = place_country_id(aux_data, rec)
    data['feature_name'] = place_feature_name(aux_data, rec)
    try_for_improved_population_estimate(aux_data, data)
    return PlaceInfo(**data)

def augment_record(aux_data, record):
    return record

def parse_alt_names_to_db(dbSession):
    # create names data
    for count, record in enumerate(record_iterator('alternateNames.txt', altname_fields)):
        pn = PlaceNames(**record)
        dbSession.add(pn)
        if (count % 500000) == 0:
            dbSession.commit()
            print '.',
    dbSession.commit()

def parse_place_info_to_db(dbSession):
    dbSession.query(PlaceInfo).delete()

    # create names data
    for count, record in enumerate(record_iterator('allCountries.txt', place_fields)):
        #augment record
        record = augment_record(aux_data, record)
        pi = make_place_info(aux_data, record)
        dbSession.add(pi)
        if (count % 500000) == 0:
            dbSession.commit()
            print '.',
    dbSession.commit()


def load_lookup_tables():
    aux_data = {}
    aux_data['admin1'] = build_dictionary('admin1CodesASCII.txt', admin1_fields, 'code');
    aux_data['admin2'] = build_dictionary('admin2Codes.txt', admin2_fields, 'code');
    aux_data['features'] = build_dictionary('featureCodes_en.txt', feature_fields, 'code');
    aux_data['countries'] = build_dictionary('countryInfo.txt', country_fields, 'iso');
    aux_data['cities'] = build_dictionary('cities1000.txt', place_fields, 'id');
    return aux_data

def main():
    parser = OptionParser(description="Parse geonames.org geo data into a SQLite DB.")
    parser.add_option("--dbname", dest="db_filename", action="store",
                      default="geodata2.db",
                      help="The geodata.db SQLite database")
    parser.add_option("--srcdir", dest="data_dir", action="store",
                      default="",
                      help="Specify directory in which data files can be found")
    parser.add_option("--disable-info", action="store_false", dest="build_info", default=True)
    parser.add_option("--disable-names", action="store_false", dest="build_names", default=True)

    (options, args) = parser.parse_args()

    aux_data = load_lookup_tables()

    engine = create_engine('sqlite:///' + options.db_filename)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    dbSession = Session()

    if parser.build_names:
        print 'parse names...'
        parse_alt_names_to_db(dbSession)

    if parser.build_info:
        print 'parse places...'
        parse_place_info_to_db(dbSession)

    
if __name__ == '__main__':
    main()


