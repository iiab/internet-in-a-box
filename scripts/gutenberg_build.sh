#!/bin/bash

# abort script on error
set -e

echo Building database from gutenberg RDF XML index
CATALOG=../catalog.rdf.bz2
DBNAME=../gutenberg.db
./gutenberg_db_build.py --rdfindex $CATALOG --dbname $DBNAME

echo Building whoosh index
WHOOSH_DIR=../whoosh/gutenberg_index
./gutenberg_whoosh_build.py --db $DBNAME --indexdir $WHOOSH_DIR

echo Creating SQL object model
MODEL=../iiab/gutenberg_models.py
# if sqlautocode is not found, you may need to pip install sqlautocode
# Option -d means use declarative object model format.
# sed script post processes to produce result for use with flask-sqlalchemy
sqlautocode -d sqlite:///../gutenberg.db | sed -f model_fixup.sed > $MODEL



