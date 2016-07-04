# Legacy Approach

geoname2whoosh.py created a whoosh index directly from allCountries.txt.  This is
limited to English names.

# Updated Approach

The geonames.org dataset comes decomposed into a variety of CSV files.  The
first step is to create a table indexing all of the alternate names, languages
and links into one table.  Then the various place records are created in a
different table denormalizing the smaller subtables and normalizing the records
into the fields of interest.

The next step is to create the specific denormalized records that will be indexed with each
name/language variation with the place information record.

Then the index is generated on the target iiab recordset.

This process is handled by ```scripts/geoname2iiab.py```.  It creates the two
intermediate SQLite databases to merge the geonames.org data (enable with
option ```--mkdb```) before creating the whoosh index (enable with ```--mkwhoosh```).

There are three steps in creating the merged data records in the two intermediate databases.

1. parse the geonames.org geoinfo into an intermediate database
   geoname_geonames.db. Skip this step with ```--skip_gn_info.```

2. parse the geonames.org geoname variations into a separate table in the an
   intermediate db geoname_geonames.db.  Skip this step with ```--skip_gn_names.```

3. merge records from the geoname_geonames.db and additional geonames.org files
   to create the iiab geo records in geoname_iiab.db.  Skip this step with
   ```--skip_iiab_db```

The whoosh index is built using the geoname_iiab.db merged record database.


# Issues

The geonames.org dataset originally contained a data file
country_categories.txt that is no longer part of the dataset.

Original url: http://download.geonames.org/export/dump/country_catagories.txt

