#!/usr/bin/env python

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, create_engine, inspect, ForeignKey
from sqlalchemy.orm import sessionmaker

__all__ = ["Database"]

class Database:
    def __init__(self, alchemyBase, filename):
        self.alchemy_base = alchemyBase
        self.engine = create_engine('sqlite:///' + filename)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create(self):
        self.alchemy_base.metadata.create_all(self.engine)

    def clear_table(self, table):
        if self.engine.has_table(table.__tablename__):
            self.session.query(table).delete()

    def get_session(self):
        return self.session


