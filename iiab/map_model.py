from extensions import db_map as db

class GeoInfo(db.Model):
    __bind_key__ = 'maps'
    __tablename__ = 'geoinfo'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Integer)
    longitude = db.Column(db.Integer)
    population = db.Column(db.Integer)
    feature_code = db.Column(db.String)
    feature_name = db.Column(db.String)

class GeoNames(db.Model):
    __bind_key__ = 'maps'
    __tablename__ = 'geonames'
    id = db.Column(db.Integer, primary_key=True)
    geonameid = db.Column(db.Integer)
    name = db.Column(db.String)
    fullname = db.Column(db.String)
    isolanguage = db.Column(db.String)

class GeoLinks(db.Model):
    __bind_key__ = 'maps'
    __tablename__ = 'geolinks'
    id = db.Column(db.Integer, primary_key=True)
    geonameid = db.Column(db.Integer)
    link = db.Column(db.String)
