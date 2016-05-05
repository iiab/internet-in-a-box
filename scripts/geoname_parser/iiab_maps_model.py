#!/usr/bin/env python

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, inspect, ForeignKey
from sqlalchemy.orm import sessionmaker

__all__ = ["GeoInfo", "GeoNames", "GeoLinks", "GeoLanguage"]

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
    geoid = Column(Integer, ForeignKey('geoinfo.id'))
    lang = Column(String, index=True)
    name = Column(String)
    fullname = Column(String)
    importance = Column(Integer, index=True)

class GeoLinks(Base):
    __tablename__ = 'geolinks'
    id = Column(Integer, primary_key=True)
    geoid = Column(Integer, ForeignKey('geoinfo.id'))
    link = Column(String)

