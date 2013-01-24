#!/usr/bin/env python

from math import radians, degrees, log, tan, atan, exp, pi, floor
import math
import csv
import sys
from time import time


def project(lat, lng):
    """Spherical Mercator projection
    returns (x, y) in radians"""
    max_lat = 85.0511287798
    lat = max(min(max_lat, lat), -max_lat)
    x = radians(lng)
    y = radians(lat)
    y = log(tan((pi / 4.0) + (y / 2.0)))
    return (x, y)


def unproject(x, y):
    """Unproject from spherical mercator coordinates in radians
    returns latitude, longitude in degrees"""
    lng = degrees(x)
    lat = degrees(2.0 * atan(exp(y)) - (pi / 2.0))
    return (lat, lng)


def radians_to_point(x, y, zoom):
    scale = 256 * math.pow(2.0, zoom)
    a = 0.5 / pi
    b = 0.5
    c = -0.5 / pi
    d = 0.5
    x = scale * (a * x + b)
    y = scale * (c * y + d)
    return (x, y)


def point_to_radians(x, y, zoom):
    scale = 256 * math.pow(2.0, zoom)
    a = 0.5 / pi
    b = 0.5
    c = -0.5 / pi
    d = 0.5
    x = ((x / scale) - b) / a
    y = ((y / scale) - d) / c
    return (x, y)


def latlng_to_point(lat, lng, zoom):
    (x, y) = project(lat, lng)
    (x, y) = radians_to_point(x, y, zoom)
    return (x, y)


def point_to_latlng(x, y, zoom):
    (x, y) = point_to_radians(x, y, zoom)
    (lat, lng) = unproject(x, y)
    return (lat, lng)


def latlng_to_tile(lat, lng, zoom):
    (x, y) = latlng_to_point(lat, lng, zoom)
    tx = int(floor(x / 256.0))
    ty = int(floor(y / 256.0))
    return (tx, ty, zoom)


def tile_to_latlng(tx, ty, zoom):
    x = 256.0 * tx
    y = 256.0 * ty
    (lat, lng) = point_to_latlng(x, y, zoom)
    return (lat, lng)


def get_local_tiles(lat, lng, zoom, r):
    (cx, cy, z) = latlng_to_tile(lat, lng, zoom)
    swx = max(cx - r, 0)
    swy = max(cy - r, 0)
    nex = min(cx + r, math.pow(2.0, zoom))
    ney = min(cy + r, math.pow(2.0, zoom))
    tiles = []
    for x in range(swx, nex):
        for y in range(swy, ney):
            tiles.append((x, y, zoom))
    return tiles


def load_cities(filename="data/cities5000.txt"):
    f = open(filename, "r")
    reader = csv.reader(f, delimiter="\t")
    cities = list(reader)
    f.close()
    return cities


def cities_to_latlng(cities):
    latlngs = [(float(x[4]), float(x[5])) for x in cities]
    return latlngs


def tile_key(tile):
    """Key which sorts tiles into blocks"""
    v = 2 ** 16 * int(tile[0] / 8) + int(tile[1] / 8)
    return v


def xyz_to_meta(x, y, z):
    METATILE=8
    mask = METATILE - 1
    x &= ~mask
    y &= ~mask
    return (x, y, z)


def cities_to_tiles(cities, zoom, tile_range=8):
    latlngs = cities_to_latlng(cities)
    tiles = set()
    cnt = 0
    t0 = time()
    for latlng in latlngs:
        if cnt % 1000 == 0:
            sys.stderr.write("%i at %i seconds\n" % (cnt, time() - t0))
        cnt += 1
        tile_list = get_local_tiles(latlng[0], latlng[1], zoom, tile_range)
        for tile in tile_list:
            meta = xyz_to_meta(tile[0], tile[1], tile[2])
            if hash(meta) not in tiles:
                print "%i %i %i" % meta
                tiles.add(hash(meta))
    return


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "USAGE: render_cities.py <zoom> <range>"
        sys.exit(-1)
    zoom = int(sys.argv[1])
    tile_range = int(sys.argv[2])
    cities = load_cities()
    cities_to_tiles(cities, zoom, tile_range)
