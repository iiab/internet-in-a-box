#!/usr/bin/env python

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, inspect
from sqlalchemy.orm import sessionmaker

__all__ = ["GeoInfo", "GeoNames", "Database"]

Base = declarative_base()

class GeoInfo(Base):
    __tablename__ = "geoinfo"

    id = Column(Integer, primary_key=True) # geoid
    latitude = Column(String)
    longitude = Column(String)
    population = Column(String)
    feature_code = Column(String)
    feature_name = Column(String)

class GeoNames(Base):
    __tablename__ = "geonames"
    id = Column(Integer, primary_key=True) # generated row id's
    geonameid = Column(Integer, index=True)
    isolanguage = Column(String)
    name = Column(String)
    fullname = Column(String)
    importance = Column(Integer, index=True)

class GeoLinks(Base):
    __tablename__ = 'geolinks'
    id = Column(Integer, primary_key=True)
    geonameid = Column(Integer, index=True)
    link = Column(String)

class Database:
    def __init__(self, filename):
        self.engine = create_engine('sqlite:///' + filename)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create(self):
        Base.metadata.create_all(self.engine)

    def clear_table(self, table):
        self.session.query(table).delete()

    def get_session(self):
        return self.session


