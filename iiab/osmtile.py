"""Routines for retrieving and converting OpenStreetMap
mod_tile imagery tiles.  By Braddock Gaskill, March 2013"""
import struct
import os
import thread
from md5 import md5
try:
    import progressbar
except ImportError:
    pass


META_MAGIC = "META"
MAX_ZOOM = 18


class TileSet(object):
    def __init__(self, tile_path, xmlname, METATILE=8, flatter=False):
        """flatter=True will turn on the flatter directory paths"""
        self.tile_path = tile_path
        self.xmlname = xmlname
        self.METATILE = METATILE
        self.flatter = flatter

    def xyz_to_meta_deep(self, x, y, z):
        """Deep, sparse directory structure normally used by mod_tile"""
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

    def xyz_to_meta_flatter(self, x, y, z):
        """New flatter, denser directory structure"""
        mask = self.METATILE - 1
        x &= ~mask
        y &= ~mask
        hashes = {}

        hashes[0] = ((x & 0xff) << 8) | (y & 0xff)
        x >>= 8
        y >>= 8

        for i in [1, 2, 3]:
            hashes[i] = ((x & 0x0f) << 4) | (y & 0x0f)
            x >>= 4
            y >>= 4

        meta = "%s/%s/%d/%u/%u/%u/%u.meta" % (self.tile_path, self.xmlname, z, hashes[3], hashes[2], hashes[1], hashes[0])
        return meta

    def xyz_to_meta(self, x, y, z):
        if self.flatter:
            return self.xyz_to_meta_flatter(x, y, z)
        return self.xyz_to_meta_deep(x, y, z)

    def xyz_to_meta_offset(self, x, y, z):
        mask = self.METATILE - 1
        offset = (x & mask) * self.METATILE + (y & mask)
        return offset


class TileNotFoundException(Exception):
    pass


class TileInvalidFormat(Exception):
    pass


def progress_bar(name, maxval):
    widgets = [name, progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=maxval)
    pbar.start()
    return pbar


def meta_write(tileset, x, y, z, indices, blobs):
    """Writes a meta tile file consisting of a series of blobs.  indicies is a
    list of blob indexes, or -1 if index entry has no blob"""
    METATILE = tileset.METATILE

    assert(len(indices) == METATILE * METATILE)

    # Get path and make parent dirs
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

    # Assert that every blob is referenced by an index
    blob_indices = set(range(len(blobs)))
    used_indices = set([x for x in indices if x != -1])
    assert(len(blob_indices - used_indices) == 0)

    # Header size
    offset = len(META_MAGIC) + 4 * 4
    # Need to pre-compensate the offsets for the size of the offset/size table we are about to write
    offset += (2 * 4) * (METATILE * METATILE)

    # Compute offsets for blobs
    bloboffsets = [0] * len(blobs)
    for i in range(len(blobs)):
        bloboffsets[i] = offset
        offset += len(blobs[i])

    # Calculate the offsets and sizes tables
    offsets = [0] * (METATILE * METATILE)
    sizes = [0] * (METATILE * METATILE)

    for i in range(len(indices)):
        bid = indices[i]
        if bid != -1:
            offsets[i] = bloboffsets[bid]
            sizes[i] = len(blobs[bid])

    # Create a temp file so our save is atomic
    tmp = "%s.tmp.%d" % (meta_path, thread.get_ident())
    f = open(tmp, "w")

    # Header
    f.write(struct.pack("4s4i", META_MAGIC, METATILE * METATILE, x, y, z))

    # Write out the offset/size table
    for mt in range(0, METATILE * METATILE):
        f.write(struct.pack("2i", offsets[mt], sizes[mt]))

    # Write out the blobs
    for i in range(len(blobs)):
        f.write(blobs[i])

    # Close and atomically rename file
    f.close()
    os.rename(tmp, meta_path)


def meta_save(tileset, x, y, z, tiles):
    """tiles is a list of (x, y, bytes).
    All tiles must be within a single meta file specified
    by tileset/x/y/z.  tiles are stored on disk in the order in which they are
    listed"""
    METATILE = tileset.METATILE
    meta_filename = tileset.xyz_to_meta(x, y, z)

    # Check that all tiles are in the same meta file
    tile_xy = set()
    for (tile_x, tile_y, tile) in tiles:
        tile_meta = tileset.xyz_to_meta(tile_x, tile_y, z)
        if tile_meta != meta_filename:
            raise Exception("Tile not within meta file")
        if (tile_x, tile_y) in tile_xy:
            raise Exception("Multiple tiles with same x,y coordinates")
        tile_xy.add((tile_x, tile_y))

    # Calculate md5sums for all tiles
    hashes = [0] * len(tiles)
    for i, (tile_x, tile_y, tile) in enumerate(tiles):
        hashes[i] = md5(tile).digest()

    # Calculate indices for each tile
    indices = [-1] * (METATILE * METATILE)
    for i, (tile_x, tile_y, tile) in enumerate(tiles):
        index = tileset.xyz_to_meta_offset(tile_x, tile_y, z)
        indices[index] = hashes[i]

    unique_hashes = {}
    blob_index = 0
    for i, entry in enumerate(tiles):
        if hashes[i] not in unique_hashes:  # First tile of this md5
            unique_hashes[hashes[i]] = blob_index
            blob_index += 1

    # map indices unique hashes to blob index
    for i, entry in enumerate(indices):
        if indices[i] != -1:
            indices[i] = unique_hashes[indices[i]]

    # Create blobs
    blobs = []
    blob_index = 0
    for i, (tile_x, tile_y, tile) in enumerate(tiles):
        tile_hash = hashes[i]
        if unique_hashes[tile_hash] == blob_index:  # First unique tile
            blobs.append(tile)
            blob_index += 1

    assert(blob_index == len(blobs))

    #print "compressed %i to %i for %i indices" % (len(tiles), len(blobs), len([x for x in indices if x != -1]))
    # Save the file
    meta_write(tileset, x, y, z, indices, blobs)


def meta_load_index(tileset, x, y, z):
    """Opens a meta tile file and reads the index.
    returns (file_descriptor, offsets, sizes)"""
    global META_MAGIC
    METATILE = tileset.METATILE
    meta_path = tileset.xyz_to_meta(x, y, z)
    if not os.path.exists(meta_path):
        raise TileNotFoundException("Tile file not found at " + meta_path)
    f = open(meta_path, 'r')
    offset = len(META_MAGIC) + 4 * 4
    offset += (2 * 4) * (METATILE * METATILE)
    magic = f.read(4)
    if magic != META_MAGIC:
        raise TileInvalidFormat("Tile " + meta_path + " is not a valid tile.  Magic " + META_MAGIC + " is not present")
    fmt = "4i"
    (n, x, y, z) = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
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
    tiles = []
    for xx in range(0, METATILE):
        for yy in range(0, METATILE):
            offset = offsets[xx * METATILE + yy]
            size = sizes[xx * METATILE + yy]
            if offset != 0:
                f.seek(offset)
                tile = f.read(size)
                tiles.append((x + xx, y + yy, tile))
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


def convert(src, dst, z):
    """Convert a source mod_tile tree of one METATILE setting
    to a new tree of a larger (multiple) METATILE setting.
    Example usage:
        import osmtile
        src=osmtile.TileSet('/knowledge/processed/mod_tile', 'default', METATILE=8, flatter=False)
        dst=osmtile.TileSet('/knowledge/modules/openstreetmap/mod_tile64', 'default', METATILE=64, flatter=True)
        for z in range(0, 16):
            osmtile.convert(src, dst, z)
    """
    assert(dst.METATILE > src.METATILE)
    assert(dst.METATILE % src.METATILE == 0)
    size = 2 ** z
    progress = progress_bar("Level " + str(z) + " Tiles ", size)
    for y in xrange(0, size, dst.METATILE):
        progress.update(y)
        for x in xrange(0, size, dst.METATILE):
            tiles = []
            for src_y in xrange(y, y + dst.METATILE, src.METATILE):
                for src_x in xrange(x, x + dst.METATILE, src.METATILE):
                    try:
                        tiles.extend(meta_load_all(src, src_x, src_y, z))
                    except TileNotFoundException:
                        pass
                    except TileInvalidFormat as e:
                        print "ERROR reading tile: " + e.message
            if len(tiles) > 0:
                meta_save(dst, x, y, z, tiles)
    progress.update(size)
