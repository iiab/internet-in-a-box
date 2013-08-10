#!/usr/bin/env python

from optparse import OptionParser
import map_models.geoname_org_model as gndata
import map_models.iiab_model as ibdata
from unicodedata2 import script_cat # helper script from local directory

"""
Read geoname.org data that has been placed into a SQLite database and create
a new database consisting of full name records structured for efficient autocomplete
and geolookup.
"""

def lookup_extranames_from_info(session, a2, a1, country):
    """
    
    """
    admin2rec = session.query(gndata.PlaceInfo).filter(gndata.PlaceInfo.id == a2).first()
    admin1rec = session.query(gndata.PlaceInfo).filter(gndata.PlaceInfo.id == a1).first()
    countryrec = session.query(gndata.PlaceInfo).filter(gndata.PlaceInfo.id == country).first()

    nameset = (admin2rec.name, admin1rec.name, countryrec.name)
    ascii_nameset = (admin2rec.ascii_name, admin1rec.ascii_name, countryrec.ascii_name)
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
    for v in session.query(gndata.PlaceNames).filter(gndata.PlaceNames.geonameid.in_(idlist)).yield_per(1):
        if v.isolanguage == u'link':
            if v.geonameid == geoid:
                links.append(v.alternate)
            continue

        value_tup = v
        # key tuples selected to make fallback matches easy
        add(lookup, v.geonameid, value_tup)   # key:int
        add(lookup, (v.geonameid, v.isolanguage), value_tup) # key:int,str
        add(lookup, (v.geonameid, v.isPreferredName), value_tup) # key:int,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isPreferredName, v.isShortName, v.isColloquial, v.isHistoric), value_tup) # key:int,str,bool,bool,bool,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isPreferredName, v.isHistoric), value_tup) # key:int,str,bool,bool
        add(lookup, (v.geonameid, v.isolanguage, v.isPreferredName), value_tup) # key:int,str,bool

    # TODO:PENDING DB REBUILD
    #for v in session.query(gndata.PlaceInfo).filter(gndata.PlaceInfo.id.in_(idlist)).yield_per(1):
    #    add(lookup, (v.id, "__infoname__"), v)

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
    """
    Return tuple consisting of (single name record with best match, int number of records that matched, bool true if some script in common, bool true if matched predominant script)
    :param refname: name record we are matching
    :param candidatematches: list of name records to search
    """
    # look through each charaacter in the name and build a frequency table of unicode script types.
    refscripts = build_script_tally(refname)
    # now do the same thing for each candidate name
    candidatescripts = {} # key: script name, value: list of geographic names
    for namerec in candidatematches:
        try: # Might be best to profile compared to test for attribute. Primary case is a name record.
            name = namerec.alternate
        except AttributeError:
            name = namerec.name
        tally = build_script_tally(name)
        ordered_tally = sorted(tally.iteritems(), key=lambda t: t[1], reverse=True)
        # only list the name under its most prevelant script type -- not currently checking for ties
        (script_type, _) = ordered_tally[0]
        add(candidatescripts, script_type, namerec)

    ordered_reftally = sorted(refscripts.iteritems(), key=lambda t: t[1], reverse=True)
    best_match = True
    for (script_type, _) in ordered_reftally:
        if script_type in candidatescripts:
            number_of_matches = len(candidatescripts[script_type])
            perfect_match = True
            namerec = candidatescripts[script_type][0] # arbitrarily select first name record in list
            return (namerec, number_of_matches, perfect_match, best_match)
        best_match = False

    number_of_matches = 1
    perfect_match = False
    best_match = False
    name = candidatematches[0] # just take first entry
    return (name, number_of_matches, perfect_match, best_match) 

def get_closest_match(records, rec, gid):
    """
    Return a geographic container name for gid that has similar language and type flags as the rec name
    :param records: dictionary of namesets obtained from get_nameset
    :param rec: specific PlaceNames record whose containing place name we are searching for
    :param gid: the place id of the containing geography whose name we seek
    :return: unicode string of best match found
    """
    # key tuples must match tuple keys in lookup table
    # order in priority rank
    prioritized_keys = [
        (gid, rec.isolanguage, rec.isPreferredName, rec.isShortName, rec.isColloquial, rec.isHistoric),
        (gid, rec.isolanguage, rec.isPreferredName, rec.isHistoric),
        (gid, rec.isolanguage, rec.isPreferredName),
        (gid, rec.isolanguage, 1),
        (gid, rec.isolanguage),
        (gid, 1),  # just pick a preferred name from any language -- best we can do really?
        (gid, "__infoname__") # okay no alternate name match -- fallback to PlaceTable names
        ]

    for key in prioritized_keys:
        if key in records:
            # try to pic a record that uses the same unicode script
            (matched, number_of_matches, perfectmatch, best_match) = match_script(rec.alternate, records[key])
            if number_of_matches != 1:
                print key, ": warning multiple matches", number_of_matches
            if not best_match:
                print key, ": chose a partially matching script"
            if not perfectmatch:
                print key, ": unable to find the same script"

            if key[1] == '__infoname__':
                print "matching infotable"
                return matched.name
            else:
                #print "matched record", key
                return matched.alternate


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
    #print name
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
    # for each place, inspect all of the different names.
    for count, v in enumerate(insession.query(gndata.PlaceInfo).yield_per(1)):
        #nameset, ascii_nameset = lookup_extranames_from_info(session, v.admin2_id, v.admin1_id, v.country_id)
        (name_records, links) = get_namesets(insession, v.id, v.admin2_id, v.admin1_id, v.country_id)

        info = ibdata.GeoInfo(id=v.id, latitude=v.latitude, longitude=v.longitude, population=v.population,
                feature_code=v.feature_code, feature_name=v.feature_name)
        outsession.add(info)

        # insert into geolinks
        for l in links:
            outsession.add(ibdata.GeoLinks(geonameid=v.id, link=l))

        # Not all places have alternate name records -- use them if we do, otherwise fallback to name in the placeinfo table
        if v.id in name_records:
            for record in name_records[v.id]:
                expanded_name = get_expanded_name(name_records, record, v.admin2_id, v.admin1_id, v.country_id)

                place = ibdata.GeoNames(geonameid=v.id, isolanguage=record.isolanguage, name=expanded_name, importance=v.population)
                outsession.add(place)

                print v.id, record.isolanguage, expanded_name, v.feature_name, v.population

        ### TODO: PENDING DB REBUILD
        # now expand name found in the placeinfo table.
#        expanded_name = get_expanded_info_name(name_records, v.id, v.admin2_id, v.admin1_id, v.country_id)
#        print expanded_name

        ### TODO: PENDING DB REBUILD
        # now expand asciiname found in the placeinfo table.
#        expanded_name = get_expanded_info_asciiname(name_records, v.id, v.admin2_id, v.admin1_id, v.country_id)
#        print expanded_name

        if count & 0xffff == 0:
            outsession.commit()

        if count > 1000:
            break

    outsession.commit()
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

    sepDb = gndata.Database(options.db_filename)

    uniDb = ibdata.Database("maptest.db")
    uniDb.clear_table(ibdata.GeoNames)
    uniDb.clear_table(ibdata.GeoInfo)
    uniDb.clear_table(ibdata.GeoLinks)

    uniDb.create()

    work(sepDb.get_session(), uniDb.get_session())

    
if __name__ == '__main__':
    main()


