#!/usr/bin/env python

from optparse import OptionParser
import map_models.separate as separate
import map_models.unified as unified
from unicodedata2 import script_cat # helper script from local directory
import operator

"""
Read geoname.org data that has been placed into a SQLite database and create
a new database consisting of full name records structured for efficient autocomplete
and geolookup.
"""

def lookup_extranames_from_info(session, a2, a1, country):
    """
    
    """
    admin2rec = session.query(separate.PlaceInfo).filter(separate.PlaceInfo.id == a2).first()
    admin1rec = session.query(separate.PlaceInfo).filter(separate.PlaceInfo.id == a1).first()
    countryrec = session.query(separate.PlaceInfo).filter(separate.PlaceInfo.id == country).first()

    nameset = (admin2rec.name, admin1rec.name, countryrec.name)
    ascii_nameset = (admin2rec.ascii_name, admin1rec.ascii_name, countryrec.ascii_name)
    print nameset, ascii_nameset
    return (nameset, ascii_nameset)

def add(lookup, key, value):
    """
    Helper function for creating/adding values to a dict of lists
    :param lookup: dictionary
    :param key: dict key
    :param value: new value to add to list in dict
    """
    if key in lookup:
        lookup[key].append(value)
    else:
        lookup[key] = [value]

def get_namesets(session, geoid, geo2id, geo1id, countryid):
    """
    Return a dictionary of all the names that will be used to construct the fully expanded place name
    :param session: database session for querying the allCountries and alternatenames content
    :param geoid: The place geographic id code
    :param geo2id: the admin2code for geoid
    :param geo1id: the admin1code for geoid
    :param countryid: the country level place id for geoid
    """
    idlist = (geoid, geo2id, geo1id, countryid)
    lookup = {}
    links = []  # links (just for geoid)
    for v in session.query(separate.PlaceNames).filter(separate.PlaceNames.geonameid.in_(idlist)).yield_per(1):
        value_tup = v
        if v.isolanguage == u'link':
            links.append(v.alternate)
            continue

        # key tuples selected to make fallback matches easy
        add(lookup, v.geonameid, value_tup)   # key:int
        add(lookup, (v.geonameid, v.isolanguage), value_tup) # key:int,str
        add(lookup, (v.geonameid, v.isPreferredName), value_tup) # key:int,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isPreferredName, v.isShortName, v.isColloquial, v.isHistoric), value_tup) # key:int,str,bool,bool,bool,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isPreferredName, v.isHistoric), value_tup) # key:int,str,bool,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isHistoric), value_tup) # key:int,str,bool

    for v in session.query(separate.PlaceInfo).filter(separate.PlaceInfo.id.in_(idlist)).yield_per(1):
        add(lookup, (v.id, "__infoname__"), v)

    return (lookup, links)

def append_if_not_empty(namelist, name):
    """Helper function for building full expanded name"""
    if name is not None:
        namelist.append(name)

def build_script_tally(name):
    scripts = {}
    for c in name:
        scriptname = script_cat(c)
        if scriptname in scripts:
            scripts[scriptname] += 1
        else:
            scripts[scriptname] = 1
    return scripts

def match_script(refname, candidatematches):
    # look through each charaacter in the name and build a frequency table of unicode script types.
    refscripts = build_script_tally(refname)
    # now do the same thing for each candidate name
    candidatescripts = {} # key: script name, value: list of geographic names
    for name in candidatematches:
        tally = build_script_tally(name.alternate)
        ordered_tally = sorted(tally.iteritems(), key=operator.itemgetter(1), reverse=True)
        # only list the name under its most prevelant script type -- not currently checking for ties
        (script_type, _) = ordered_tally[0]
        add(candidatescripts, script_type, name)

    ordered_reftally = sorted(refscripts.iteritems(), key=operator.itemgetter(1), reverse=True)
    best_match = True
    for (script_type, _) in ordered_reftally:
        if script_type in candidatescripts:
            number_of_matches = len(candidatescripts[script_type])
            perfect_match = True
            return (candidatescripts[script_type][0], number_of_matches, perfect_match, best_match)
        best_match = False

    number_of_matches = 1
    perfect_match = False
    best_match = False
    return (candidatematches[0], number_of_matches, perfect_match, best_match) 

def get_closest_match(records, rec, gid):
    """
    Return a geographic container name for gid that has similar language and type flags as the rec name
    :param records: dictionary of namesets obtained from get_nameset
    :param rec: specific PlaceNames record whose containing place name we are searching for
    :param gid: the place id of the containing geography whose name we seek
    :return: unicode string of best match found
    """
    prioritized_keys = [
        (gid, rec.isolanguage, rec.isPreferredName, rec.isShortName, rec.isColloquial, rec.isHistoric),
        (gid, rec.isolanguage, rec.isPreferredName, rec.isHistoric),
        (gid, rec.isolanguage, rec.isHistoric),
        (gid, rec.isolanguage),
        (gid, 1),  # just pick a preferred name from any language -- best we can do really?
        (gid, "__infoname__") # okay no alternate name match -- fallback to PlaceTable names
        ]

    for key in prioritized_keys:
        for key in records:
            # try to pic a record that uses the same unicode script
            (index, number_of_matches, perfectmatch, best_match) = match_script(rec.alternate, records[key])
            if number_of_matches != 1:
                print key, ": warning multiple matches", number_of_matches
            if not best_match:
                print key, ": chose a partially matching script"
            if not perfectmatch:
                print key, ": unable to find the same script"

            if key[1] == '__infoname__':
                print "matching infotable"
                return records[key][0].name
            else:
                return records[key][0].alternate


def get_expanded_name(records, rec, admin2, admin1, country):
    """
    Return a unicode string with fully expanded name for place described by PlaceName record rec
    :param records: dictionary of namesets obtained from get_nameset
    :param rec: specific PlaceNames record whose containing place name we are searching for
    :param admin2: admin2code for rec
    :param admin1: admin1code for rec
    :param country: country geo id for rec
    """
    name = [rec.alternate]
    append_if_not_empty(name, get_closest_match(records, rec, admin2))
    append_if_not_empty(name, get_closest_match(records, rec, admin1))
    append_if_not_empty(name, get_closest_match(records, rec, country))
    print name
    return u', '.join(name)

def get_expanded_info_name(records, gid, admin2, admin1, country):
    """
    Return a unicode string with fully expanded name for place using PlaceInfo.name values
    :param records: dictionary of namesets obtained from get_nameset
    :param gid: specific geographic id for the place we are naming
    :param admin2: admin2code for gid
    :param admin1: admin1code for gid
    :param country: country geo id for gid
    """
    name = [records[(gid, "__infoname__")].name]
    append_if_not_empty(name, records[(admin2, "__infoname__")].name)
    append_if_not_empty(name, records[(admin1, "__infoname__")].name)
    append_if_not_empty(name, records[(country, "__infoname__")].name)
    print name
    return u', '.join(name)

def get_expanded_info_asciiname(records, gid, admin2, admin1, country):
    """
    Return a unicode string with fully expanded name for place using PlaceInfo.asciiname values
    :param records: dictionary of namesets obtained from get_nameset
    :param gid: specific geographic id for the place we are naming
    :param admin2: admin2code for gid
    :param admin1: admin1code for gid
    :param country: country geo id for gid
    """
    name = [records[(gid, "__infoname__")].asciiname]
    append_if_not_empty(name, records[(admin2, "__infoname__")].asciiname)
    append_if_not_empty(name, records[(admin1, "__infoname__")].asciiname)
    append_if_not_empty(name, records[(country, "__infoname__")].asciiname)
    print name
    return u', '.join(name)

def work(insession, outsession):
    count = 0
    # for each place, inspect all of the different names.
    for v in insession.query(separate.PlaceInfo).yield_per(1):
        #nameset, ascii_nameset = lookup_extranames_from_info(session, v.admin2_id, v.admin1_id, v.country_id)
        (name_records, links) = get_namesets(insession, v.id, v.admin2_id, v.admin1_id, v.country_id)
        # Not all places have alternate name records -- use them if we do, otherwise fallback to name in the placeinfo table
        if v.id in name_records:
            for record in name_records[v.id]:
                expanded_name = get_expanded_name(name_records, record, v.admin2_id, v.admin1_id, v.country_id)

                # insert into geoinfo
                print (v.id, v.latitude, v.longitude, v.population, v.feature_code, v.feature_name)

                # insert into geonames
                print (v.id, record.isolanguage, expanded_name, v.population)

        # insert into geolinks
        print (v.id, links)

        # now expand name found in the placeinfo table.
#        expanded_name = get_expanded_info_name(name_records, v.id, v.admin2_id, v.admin1_id, v.country_id)
#        print expanded_name

        # now expand asciiname found in the placeinfo table.
#        expanded_name = get_expanded_info_asciiname(name_records, v.id, v.admin2_id, v.admin1_id, v.country_id)
#        print expanded_name


        count += 1
        if count > 25:
            break;

def main():
    parser = OptionParser(description="Parse geonames.org geo data into a SQLite DB.")
    parser.add_option("--dbname", dest="db_filename", action="store",
                      default="geodata2.db",
                      help="The geodata.db SQLite database")
    parser.add_option("--srcdir", dest="data_dir", action="store",
                      default="",
                      help="Specify directory in which data files can be found")
    parser.add_option("--disable-info", action="store_false", dest="build_info", default=True)
    parser.add_option("--disable-names", action="store_false", dest="build_names", default=True)

    (options, args) = parser.parse_args()

    sepDb = separate.Database(options.db_filename)

    uniDb = unified.Database("maptest.db")
    #uniDb.clear_table(unified.GeoNames)
    #uniDb.clear_table(unified.GeoInfo)
    uniDb.create()

    work(sepDb.get_session(), uniDb.get_session())

    
if __name__ == '__main__':
    main()


