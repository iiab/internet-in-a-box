#!/bin/bash

# abort script on error
set -e

CATALOG=../catalog.rdf.bz2
DBNAME=../gutenberg.db
WHOOSH_DIR=../whoosh/gutenberg_index
MODEL=../iiab/gutenberg_models.py

echo Building database from gutenberg RDF XML index
./gutenberg_db_build.py --rdfindex $CATALOG --dbname $DBNAME

echo Building whoosh index
./gutenberg_whoosh_build.py --db $DBNAME --indexdir $WHOOSH_DIR

echo Creating SQL object model
# if sqlautocode is not found, you may need to pip install sqlautocode
# Option -d means use declarative object model format.
# sed script post processes to produce result for use with flask-sqlalchemy
sqlautocode -d sqlite:///${DBNAME} | sed -f model_fixup.sed > $MODEL



