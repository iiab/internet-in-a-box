#!/usr/bin/env python
import struct
import os
import thread


META_MAGIC = "META"
MAX_ZOOM = 18


class TileSet(object):
    def __init__(self, tile_path, xmlname, METATILE=8):
        self.tile_path = tile_path
        self.xmlname = xmlname
        self.METATILE = METATILE

    def xyz_to_meta(self, x, y, z):
        mask = self.METATILE - 1
        x &= ~mask
        y &= ~mask
        hashes = {}

        for i in range(0, 5):
            hashes[i] = ((x & 0x0f) << 4) | (y & 0x0f)
            x >>= 4
            y >>= 4

        meta = "%s/%s/%d/%u/%u/%u/%u/%u.meta" % (self.tile_path, self.xmlname, z, hashes[4], hashes[3], hashes[2], hashes[1], hashes[0])
        return meta

    def xyz_to_meta_offset(self, x, y, z):
        mask = self.METATILE - 1
        offset = (x & mask) * self.METATILE + (y & mask)
        return offset


def meta_save(tileset, x, y, z, size, tiles):
    #print "Saving %d tiles" % (size * size)
    METATILE = tileset.METATILE
    meta_path = tileset.xyz_to_meta(x, y, z)
    d = os.path.dirname(meta_path)
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            # Multiple threads can race when creating directories,
            # ignore exception if the directory now exists
            if not os.path.exists(d):
                raise

    tmp = "%s.tmp.%d" % (meta_path, thread.get_ident())
    f = open(tmp, "w")

    f.write(struct.pack("4s4i", META_MAGIC, METATILE * METATILE, x, y, z))
    offset = len(META_MAGIC) + 4 * 4
    # Need to pre-compensate the offsets for the size of the offset/size table we are about to write
    offset += (2 * 4) * (METATILE * METATILE)
    # Collect all the tile sizes
    sizes = {}
    offsets = {}
    for xx in range(0, size):
        for yy in range(0, size):
            mt = tileset.xyz_to_meta_offset(x + xx, y + yy, z)
            sizes[mt] = len(tiles[(xx, yy)])
            offsets[mt] = offset
            offset += sizes[mt]
    # Write out the offset/size table
    for mt in range(0, METATILE * METATILE):
        if mt in sizes:
            f.write(struct.pack("2i", offsets[mt], sizes[mt]))
        else:
            f.write(struct.pack("2i", 0, 0))
    # Write out the tiles
    for xx in range(0, size):
        for yy in range(0, size):
            f.write(tiles[(xx, yy)])

    f.close()
    os.rename(tmp, meta_path)
    #print "Wrote: %s" % meta_path


def meta_load_index(tileset, x, y, z):
    """Opens a meta tile file and reads the index.
    returns (file_descriptor, offsets, sizes)"""
    global META_MAGIC
    METATILE = tileset.METATILE
    meta_path = tileset.xyz_to_meta(x, y, z)
    if not os.path.exists(meta_path):
        raise Exception("Tile file not found at " + meta_path)
    f = open(meta_path, 'r')
    offset = len(META_MAGIC) + 4 * 4
    offset += (2 * 4) * (METATILE * METATILE)
    fmt = "4s4i"
    (META_MAGIC, n, x, y, z) = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    offsets = []
    sizes = []
    for mt in range(0, METATILE * METATILE):
        (offset, size) = struct.unpack('2i', f.read(2 * 4))
        offsets.append(offset)
        sizes.append(size)
    return (f, offsets, sizes)


def meta_load_all(tileset, x, y, z):
    """Read all tiles out of a meta tile"""
    METATILE = tileset.METATILE
    f, offsets, sizes = meta_load_index(tileset, x, y, z)
    tiles = {}
    for xx in range(0, METATILE):
        for yy in range(0, METATILE):
            offset = offsets[xx * METATILE + yy]
            size = sizes[xx * METATILE + yy]
            if offset != 0:
                f.seek(offset)
                tile = f.read(size)
                tiles[(xx, yy)] = tile
    return tiles


def meta_load_one(tileset, x, y, z):
    """Read a single tile out of the appropriate meta tile file"""
    f, offsets, sizes = meta_load_index(tileset, x, y, z)
    index = tileset.xyz_to_meta_offset(x, y, z)
    offset = offsets[index]
    size = sizes[index]
    f.seek(offset)
    tile = f.read(size)
    return tile
