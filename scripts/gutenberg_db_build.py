#!/usr/bin/env python

import os
import sys
import sqlite3
from gutenberg_rdf_parser import parse_rdf_bz2
from optparse import OptionParser
from pluralize import pluralize # locally provided function
from gutenberg_filter import GutenbergIndexFilter

class GutenbergDbCreator:
    # schema dictionary format:
    #   { TABLE_NAME : [ (COL1, DEF1), (COL2, DEF2), ... ] }
    # column names selected to match record keys from rdf_parser
    # NOT NULL designation on PRIMARY KEY seems to help sqlite generate a key when inserting
    MAIN_TABLE_SCHEMA = { 'gutenberg_books' : [('textId', 'TEXT PRIMARY KEY NOT NULL'), ('title', 'TEXT'), ('friendlytitle', 'TEXT')] }
    AUX_COLUMN_NAMES = ['contributor', 'creator', 'subject', 'language', 'category']
    # each aux table one column which contains a unique value. The schema can be generated from the aux column list.
    AUX_TABLE_SCHEMA = { "gutenberg_%s" % pluralize(name) : [('id', 'INTEGER PRIMARY KEY NOT NULL'), (name, 'TEXT UNIQUE')] for name in AUX_COLUMN_NAMES}
    FILE_TABLE_SCHEMA = { "gutenberg_book_files" : [('id', 'INTEGER PRIMARY KEY NOT NULL'), ('file', 'TEXT UNIQUE'), ('format', 'TEXT'), 
        ('textId', 'TEXT REFERENCES gutenberg_books(textId) ON DELETE CASCADE')] }

    def __init__(self, filename, debug=False):
        """
        Create/recreate the schema

        :param filename: database filename
        :param debug: boolean whether to enable verbose output
        """
        self.db = sqlite3.connect(filename)
        self.debug = debug

        # create a look dict so we can find the mapping table given the auxiliary table name
        self.mapping_table_lookup = {}

        self._create_table_from_schema(self.MAIN_TABLE_SCHEMA)
        self._create_table_from_schema(self.AUX_TABLE_SCHEMA)
        self._create_table_from_schema(self.FILE_TABLE_SCHEMA)
        self._create_many2many_tables(self.MAIN_TABLE_SCHEMA, self.AUX_TABLE_SCHEMA)

    def _create_table_from_schema(self, schema_map):
        def collect_columns_from_schema(col_schema):
            """ Return comma separated columns and def for SQL create """
            return ','.join([' '.join(col_name_and_type) for col_name_and_type in col_schema])

        for table_name, schema in schema_map.items():
            print "creating table " + table_name
            self.db.execute("DROP TABLE IF EXISTS %s" % table_name)
            sql_create = "CREATE TABLE %s(%s)" % (table_name, 
                    collect_columns_from_schema(schema))
            if self.debug:
                print sql_create
            self.db.execute(sql_create)

    def _create_many2many_tables(self, main_schema, aux_schemas):
        """
        Create many-to-many tables based on supplied schema dicts.
        Many to many tables are created specially.  The main table has a many-to-many relationship with
        each auxiliary table.
        Also populates the mapping lookup table.
        :param main_schema: schema description dict as described above. Expected to have one table.
        :param aux_schemas: schema description dict as described above. Likely to have many tables.
        """
        # Autogeneration of mapping assumes there is only one main table again which all auxiliary table are mapped
        assert(len(main_schema) == 1)
        CREATE_TABLE_TEMPLATE = ("CREATE TABLE {table_name}({book_id_name} INT REFERENCES {main_table_name}(textId) ON DELETE CASCADE, "
                "{aux_id_name} INT REFERENCES {aux_table_name}(id) ON DELETE CASCADE, PRIMARY KEY({book_id_name},{aux_id_name}))")
        for main_table_name in main_schema:
            for aux_table_name, aux_cols in aux_schemas.items():
                # Assumed aux tables only contain two columns, the second of which describes the unique content
                column_name = self._get_aux_table_unique_column_name(aux_cols)
                table_name = "{0}_{1}_map".format(main_table_name, column_name)
                print "creating many-to-many mapping table " + table_name

                # column names
                book_id_name = "book_id"
                aux_id_name = "%s_id" % column_name

                self.db.execute("DROP TABLE IF EXISTS %s" % table_name)
                sql_create =  CREATE_TABLE_TEMPLATE.format(table_name=table_name, main_table_name=main_table_name, 
                        book_id_name=book_id_name, aux_table_name=aux_table_name, aux_id_name=aux_id_name)
                if self.debug:
                    print sql_create
                self.db.execute(sql_create)

                # record association between mapping table and auxiliary table
                self.mapping_table_lookup[aux_table_name] = {table_name : [book_id_name, aux_id_name]}

    def _get_aux_table_unique_column_name(self, aux_cols):
        """
        Return the unique value column name
        Auxiliary tables have typically have two columns, an id and a unique value column. Given
        an array of column definitions, this returns the column name of the unique column.
        :param aux_cols:   list of (colname, coldef) pairs
        :returns: colname of column with UNIQUE in column definition.
        """
        assert(len(aux_cols) == 2)
        for column_name, column_def in aux_cols:
            if column_def.find("UNIQUE") != -1:
                return column_name
        assert(False)  # The aux tables contain list of unique values -- one of the columns should be defined unique!

    def _create_insert_sql(self, table_name, col_schema):
        """
        Create an insert statement for use by main and auxiliary tables
        Omits id so it will be auto generated. (Note that books primary key changed
        so provided explicitly but column name is not 'id'.)
        """
        return "INSERT INTO %s (%s) VALUES (%s)" % (table_name, 
                ','.join([name for (name,_) in col_schema if name != 'id']), 
                ','.join([":" + name for (name,_) in col_schema if name != 'id']))

    def _insert_mapping_from_book_to_aux(self, cursor, aux_table_name, book_id, aux_id):
        """
        Inserts the many-to-many association between book_id and aux_id
        """
        assert(len(self.mapping_table_lookup[aux_table_name]) == 1) # expects one mapping table else must revise
        for map_table_name, map_col_names in self.mapping_table_lookup[aux_table_name].items():
            (book_id_name, aux_id_name) = map_col_names
            insertSql = "INSERT INTO {0} ({1},{2}) VALUES (:{1}, :{2})".format(map_table_name, book_id_name, aux_id_name)
            values = { book_id_name : book_id, aux_id_name : aux_id }
            if self.debug:
                print insertSql, values
            cursor.execute(insertSql, values)

    def _select_id_or_insert(self, cursor, selectSql, insertSql, col_name, value):
        """
        Auxiliary tables contain unique values so return the id for the value if it already has been inserted
        If it hasn't been inserted, do so and return the new id.
        :param cursor:      working database cursor
        :param selectSql:   sql select statement ready for execution with supplied value. table name already embedded.
        :param insertSql:   sql insert statement ready for execution with supplied value. table name already embedded.
        :param col_name:    column name associated with the value
        :param value:       unicode string to be put in the database
        :returns:           id of value in the table
        """
        # check if value already in table
        aux_id = cursor.execute(selectSql, (value,)).fetchone()
        if isinstance(aux_id, tuple): 
            (aux_id,) = aux_id
        if aux_id is None:
            cursor.execute(insertSql, { 'id' : None, col_name : value })
            aux_id = cursor.lastrowid
        return aux_id

    def is_book_description(self, record):
        assert record['record_type'] in ['DESCRIPTION', 'FILE']
        return record['record_type'] == 'DESCRIPTION'

    def add_record(self, record, cursor):
        """
        :param record:      rdf parser record format
        :param cursor:      If pending transaction, database cursor to use.  May be None
        """
        cursor_owner = cursor is None
        if cursor is None:
            cursor = self.db.cursor()

        assert(len(self.MAIN_TABLE_SCHEMA) == 1)  # expect only one main table, else book_id is not unique

        # id should be null so that it will be autogenerated
        assert('id' not in record)
        #record['id'] = None

        if self.is_book_description(record):
            # insert main book entry
            for table_name, col_schema in self.MAIN_TABLE_SCHEMA.items():
                insertSql = self._create_insert_sql(table_name, col_schema)

                # some titles include multiple entries (perhaps because of translations)
                # let's combine them into one title separated by slashes
                for cname in ['title', 'friendlytitle']:
                    v = record[cname]
                    if isinstance(v, (list, tuple)):
                        record[cname] = u' / '.join(v)
                
                if self.debug:
                    print insertSql, record
                cursor.execute(insertSql, record)
                book_id = record['textId']  # used below when inserting fields into aux tables

            # insert aux entries.  more than one data value may exist for each column in a record
            for table_name, col_schema in self.AUX_TABLE_SCHEMA.items():
                insertSql = self._create_insert_sql(table_name, col_schema)
                if self.debug:
                    print insertSql
                col_name = self._get_aux_table_unique_column_name(col_schema)
                selectSql = "SELECT id FROM %s WHERE %s=?" % (table_name, col_name)
                values = record[col_name]
                # if list of values insert each in turn
                if not isinstance(values, basestring):
                    for value in values:
                        aux_id = self._select_id_or_insert(cursor, selectSql, insertSql, col_name, value)
                        self._insert_mapping_from_book_to_aux(cursor, table_name, book_id, aux_id)
                # otherwise insert the single value
                else:
                    if self.debug:
                        print selectSql, values
                    aux_id = self._select_id_or_insert(cursor, selectSql, insertSql, col_name, values)
                    self._insert_mapping_from_book_to_aux(cursor, table_name, book_id, aux_id)
        else: # record_type is FILE type
            for table_name, col_schema in self.FILE_TABLE_SCHEMA.items():
                # if format is list, merge to newline delimited field
                if not isinstance(record['format'], basestring):
                    record['format'] = u"\n".join(record['format'])
                insertSql = self._create_insert_sql(table_name, col_schema)
                cursor.execute(insertSql, record)

        if cursor_owner:
            self.db.commit()

    def add_many_records(self, record_list):
        """
        Creates transaction and iterates through record list inserting values
        """
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)   # don't buffer stdout

        cursor = self.db.cursor()
        print "Bulk adding records"
        try:
            for count, record in enumerate(record_list):
                self.add_record(record, cursor)
                if (count % 10000) == 0:
                    print count,
            print "\n%d records added." % (count + 1)
            print "Removing books which have all files filtered out..."

            # Now remove books for which we don't have any files records. TODO: Verify that a lack of
            # file entries is always a result of our filtering.  If we need to discover files through
            # some means other than a file record in the gutenberg index this may need to change.
            # TODO: Remove aux and mapping table entries associated with removed books.
            (number_of_books_without_files,) = cursor.execute('select count(BOOKS.textId) from gutenberg_books as BOOKS where (select count(*) from gutenberg_book_files as FILES where FILES.textId=BOOKS.textId) == 0;').fetchone()
            print "Number of books without files %d." % number_of_books_without_files
            removed_count = cursor.execute('delete from gutenberg_books where(select count(*) from gutenberg_book_files as FILES where FILES.textId=gutenberg_books.textId)==0').rowcount
            print "Removed %d records." % removed_count
            if number_of_books_without_files != removed_count:
                print "WARNING: NUMBER OF RECORDS REMOVED DOES NOT MATCH NUMBER OF BOOKS WITHOUT FILES"
            print "Committing..."
        finally:
            # always commit rather than rollback if sqlite3.DatabaseError because easier to debug
            self.db.commit()

def main():
    parser = OptionParser()
    parser.add_option("--dbname", dest="db_filename", action="store",
                      default="gutenberg.db",
                      help="The gutenberg.db SQLite database")
    parser.add_option("--rdfindex", dest="bz2_rdf_filename", action="store",
                      default="catalog.rdf.bz2",
                      help="The filename for the bzip2 compressed XML RDF index for Project Gutenberg")
    (options, args) = parser.parse_args()

    make_db = GutenbergDbCreator(options.db_filename)
    make_db.add_many_records(parse_rdf_bz2(options.bz2_rdf_filename, GutenbergIndexFilter().filter))

if __name__ == '__main__':
    main()

