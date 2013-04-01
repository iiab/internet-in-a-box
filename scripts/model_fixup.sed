3,10d
2a\
from .extensions import db
s/DeclarativeBase/db.Model/g
s/Table/db.Table/g
s/Column/db.Column/g
s/relation(/db.relation(/g
s/metadata,//g
s/INTEGER/db.INTEGER/g
s/TEXT/db.TEXT/g
s/VARCHAR/db.VARCHAR/g
s/ForeignKey/db.ForeignKey/g
/gutenberg_subjects =/a\
    gutenberg_files = db.relation('GutenbergFile')

