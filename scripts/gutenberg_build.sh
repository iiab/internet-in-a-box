#!/bin/bash

# abort script on error
set -e

PYTHON_DIR=${PYTHON_DIR:-""} # permit override from environment
PYTHON_EXE="${PYTHON_DIR}python"
echo Using python path $PYTHON_DIR
echo Using python exec $PYTHON_EXE

# BASE_DIR is typically one directory above Heritage project dirctory
BASE_DIR=/knowledge
usage() {
cat << EOF
usage: $0 base_directory
  base_directory is the absolute path to the directory containing
                 the processed and data directories.
                 Default $BASE_DIR

This script processes the Project Gutenberg RDF index file
to produce the database, index files and website support files.

Links will be created in the project directories to files in the processed
directory.

If running with sudo it may be necessary to override the python directory
with the virtualenv python by setting the PYTHON_DIR env variable.

EOF
}

if [[ $# > 1 || $1 = "-h" || $1 = "--help" ]]; then
    usage
    exit 1
fi

if [[ $# = 1 ]]; then
    BASE_DIR=$1
fi

# assumes script run from scripts directory off of heritage root
HERITAGE_DIR=..
PROCESSED_DIR=$BASE_DIR/processed
DBNAME=gutenberg.db
MODEL=gutenberg_models.py
WORDLIST_JSON=gutenberg_wordlist.json
GUTENBERG_DATA=$BASE_DIR/data/gutenberg/gutenberg

CATALOG=$GUTENBERG_DATA/../catalog.rdf.bz2
DBNAME_TARGET=$PROCESSED_DIR/$DBNAME
WHOOSH_DIR=$PROCESSED_DIR/whoosh/gutenberg_index
WHOOSH_DIR_LNK_SRC=$PROCESSED_DIR/whoosh
WHOOSH_DIR_LNK_DST=$HERITAGE_DIR/whoosh
MODEL_TARGET=$PROCESSED_DIR/$MODEL
WORDLIST_JSON_TARGET=$PROCESSED_DIR/$WORDLIST_JSON

function assert_dir_exists {
    if [[ ! -d "$1" ]]; then
        echo Cannot find directory: $1
        exit 1
    fi
}

function mk_lnk {
    # do sanity check making sure linked file is a normal file or directory
    if [[ ! -f "$1" && ! -d "$1" || -h "$1" ]]; then
        echo "$1 does not exist or is a symbolic link (which means params may be reversed)"
        exit 1
    fi
    if [[ ! -e "$2" ]]; then
        echo Creating "$2"
        # symlinks to non existing file will fail -e but not -h
        if [[ -h $2 ]]; then
            ln -s -f "$1" "$2"
        else
            ln -s "$1" "$2"
        fi
    else
        echo "$2 exists (no action)"
    fi
}

assert_dir_exists $PROCESSED_DIR
assert_dir_exists $WHOOSH_DIR

ACTION_LIST=${ACTION_LIST:-"db whoosh model wordlist symlinks"}
for val in $ACTION_LIST
do
    case $val in
        db)
            echo Building database from gutenberg RDF XML index
            $PYTHON_EXE ./gutenberg_db_build.py --rdfindex $CATALOG --dbname $DBNAME_TARGET
            ;;

        whoosh)
            echo Building whoosh index
            $PYTHON_EXE gutenberg_whoosh_build.py --db $DBNAME_TARGET --indexdir $WHOOSH_DIR
            ;;

        model)
            echo Creating SQL object model
            # if sqlautocode is not found, you may need to pip install sqlautocode
            # Option -d means use declarative object model format.
            # sed script post processes to produce result for use with flask-sqlalchemy
            ${PYTHON_DIR}sqlautocode -d sqlite:///${DBNAME_TARGET} | sed -f model_fixup.sed > $MODEL_TARGET

            ;;

        wordlist)
            echo Dumping titles and creators to json wordlist
            { sqlite3 -csv $DBNAME_TARGET "select book.title from gutenberg_books as book order by downloads desc;" ; sqlite3 -csv $DBNAME_TARGET "select c.creator from gutenberg_creators as c;" ; sqlite3 -csv $DBNAME_TARGET "select c.contributor from gutenberg_contributors as c;" ; } | $PYTHON_EXE csv_to_json.py -y --json $WORDLIST_JSON_TARGET
            ;;

        symlinks)
            echo Creating symlinks
            mk_lnk $DBNAME_TARGET $HERITAGE_DIR/$DBNAME
            mk_lnk $WHOOSH_DIR_LNK_SRC $WHOOSH_DIR_LNK_DST
            mk_lnk $MODEL_TARGET $HERITAGE_DIR/iiab/$MODEL
            mk_lnk $WORDLIST_JSON_TARGET $HERITAGE_DIR/iiab/static/$WORDLIST_JSON
            mk_lnk $GUTENBERG_DATA $HERITAGE_DIR/iiab/static/data
            ;;

        *)
            usage
            exit 1
            ;;
    esac
done

