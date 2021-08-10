from struct import pack, unpack

from .gns import GNS
from .resource import Resources
from .texture import Texture as Texture_File


class PointXYZ(object):
    def __init__(self):
        self.X = None
        self.Y = None
        self.Z = None
        self.coords = (self.X, self.Y, self.Z)

    def from_data(self, data):
        self.coords = (self.X, self.Y, self.Z) = unpack('<3h', data)

    def set_coords(self, x, y, z):
        self.coords = (self.X, self.Y, self.Z) = x, y, z


class PointUV(object):
    def __init__(self):
        self.U = None
        self.V = None
        self.coords = (self.U, self.V)

    def from_data(self, data):
        self.coords = (self.U, self.V) = unpack('<2B', data)

    def set_coords(self, u, v):
        self.coords = (self.U, self.V) = u, v


class VectorXYZ(object):
    def __init__(self):
        self.X = None
        self.Y = None
        self.Z = None
        self.coords = (self.X, self.Y, self.Z)

    def from_data(self, data):
        self.coords = (self.X, self.Y, self.Z) = [x / 4096.0 for x in unpack('<3h', data)]

    def set_coords(self, x, y, z):
        self.coords = (self.X, self.Y, self.Z) = x, y, z


class Vertex(object):
    def __init__(self):
        self.point = PointXYZ()
        self.normal = None
        self.texcoord = None

    def from_data(self, point_data, normal_data=None, texcoord_data=None):
        self.point.from_data(point_data)
        if normal_data:
            self.normal = VectorXYZ()
            self.normal.from_data(normal_data)
            self.texcoord = PointUV()
            self.texcoord.from_data(texcoord_data)


class Triangle(object):
    def __init__(self):
        self.A = Vertex()
        self.B = Vertex()
        self.C = Vertex()
        self.texture_palette = None
        self.texture_page = None
        self.visible_angles = None
        self.terrain_coords = None
        self.unknown1 = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None

    def from_data(self, point, visangle, normal=None, texcoord=None, unknown5=None, terrain_coords=None):
        if normal:
            self.A.from_data(point[0:6], normal[0:6], texcoord[0:2])
            self.unknown1 = (unpack('B', texcoord[2:3])[0] >> 4) & 0xf
            self.texture_palette = unpack('B', texcoord[2:3])[0] & 0xf
            self.unknown2 = unpack('B', texcoord[3:4])[0]
            self.B.from_data(point[6:12], normal[6:12], texcoord[4:6])
            self.unknown3 = (unpack('B', texcoord[6:7])[0] >> 2) & 0x3f
            self.texture_page = unpack('B', texcoord[6:7])[0] & 0x3
            self.unknown4 = unpack('B', texcoord[7:8])[0]
            self.C.from_data(point[12:18], normal[12:18], texcoord[8:10])
            (val1, tx) = unpack('BB', terrain_coords)
            tz = val1 >> 1
            tlvl = val1 & 0x01
            self.terrain_coords = (tx, tz, tlvl)
        else:
            self.A.from_data(point[0:6])
            self.B.from_data(point[6:12])
            self.C.from_data(point[12:18])
            self.unknown5 = unknown5
        vis = unpack('H', visangle)[0]
        self.visible_angles = [ (vis & 2**(15-x)) >> (15-x) for x in range(16) ]

    def vertices(self):
        for point in 'ABC':
            yield getattr(self, point)


class Quad(object):
    def __init__(self):
        self.A = Vertex()
        self.B = Vertex()
        self.C = Vertex()
        self.D = Vertex()
        self.texture_palette = None
        self.texture_page = None
        self.visible_angles = None
        self.terrain_coords = None
        self.unknown1 = None
        self.unknown2 = None
        self.unknown3 = None
        self.unknown4 = None
        self.unknown5 = None

    def from_data(self, point, visangle, normal=None, texcoord=None, unknown5=None, terrain_coords=None):
        if normal:
            self.A.from_data(point[0:6], normal[0:6], texcoord[0:2])
            self.unknown1 = (unpack('B', texcoord[2:3])[0] >> 4) & 0xf
            self.texture_palette = unpack('B', texcoord[2:3])[0] & 0xf
            self.unknown2 = unpack('B', texcoord[3:4])[0]
            self.B.from_data(point[6:12], normal[6:12], texcoord[4:6])
            self.unknown3 = (unpack('B', texcoord[6:7])[0] >> 2) & 0x3f
            self.texture_page = unpack('B', texcoord[6:7])[0] & 0x3
            self.unknown4 = unpack('B', texcoord[7:8])[0]
            self.C.from_data(point[12:18], normal[12:18], texcoord[8:10])
            self.D.from_data(point[18:24], normal[18:24], texcoord[10:12])
            (val1, tx) = unpack('BB', terrain_coords)
            tz = val1 >> 1
            tlvl = val1 & 0x01
            self.terrain_coords = (tx, tz, tlvl)
        else:
            self.A.from_data(point[0:6])
            self.B.from_data(point[6:12])
            self.C.from_data(point[12:18])
            self.D.from_data(point[18:24])
            self.unknown5 = unknown5
        vis = unpack('H', visangle)[0]
        self.visible_angles = [ (vis & 2**(15-x)) >> (15-x) for x in range(16) ]

    def vertices(self):
        for point in 'ABCD':
            yield getattr(self, point)


class Palette(object):
    def __init__(self, ):
        self.colors = None

    def from_data(self, data):
        colors = []
        for c in range(16):
            unpacked = unpack('H', data[c*2:c*2+2])[0]
            a = (unpacked >> 15) & 0x01
            b = (unpacked >> 10) & 0x1f
            g = (unpacked >> 5) & 0x1f
            r = (unpacked >> 0) & 0x1f
            colors.append((r, g, b, a))
        self.colors = colors


class Ambient_Light(object):
    def __init__(self, ):
        self.color = None

    def from_data(self, data):
        self.color = unpack('3B', data)

    def to_data(self, amb_light):
        color = amb_light.color
        return pack('3B', *color)


class Directional_Light(object):
    def __init__(self, ):
        self.color = None
        self.direction = VectorXYZ()

    def from_data(self, color_data, direction_data):
        self.color = unpack('3h', color_data)
        self.direction.from_data(direction_data)


class Background(object):
    def __init__(self):
        self.color1 = None
        self.color2 = None

    def from_data(self, color_data):
        self.color1 = unpack('3B', color_data[0:3])
        self.color2 = unpack('3B', color_data[3:6])

    def to_data(self, background):
        return pack('6B', *(background.color1 + background.color2))


class Tile(object):
    def __init__(self):
        self.unknown1 = None
        self.surface_type = None
        self.unknown2 = None
        self.height = None
        self.depth = None
        self.slope_height = None
        self.slope_type = None
        self.unknown3 = None
        self.unknown4 = None
        self.cant_walk = None
        self.cant_cursor = None
        self.unknown5 = None

    def from_data(self, tile_data):
        val1 = unpack('B', tile_data[0:1])[0]
        self.unknown1 = (val1 >> 6) & 0x3
        self.surface_type = (val1 >> 0) & 0x3f
        self.unknown2 = unpack('B', tile_data[1:2])[0]
        self.height = unpack('B', tile_data[2:3])[0]
        val4 = unpack('B', tile_data[3:4])[0]
        self.depth = (val4 >> 5) & 0x7
        self.slope_height = (val4 >> 0) & 0x1f
        self.slope_type = unpack('B', tile_data[4:5])[0]
        self.unknown3 = unpack('B', tile_data[5:6])[0]
        val7 = unpack('B', tile_data[6:7])[0]
        self.unknown4 = (val7 >> 2) & 0x3f
        self.cant_walk = (val7 >> 1) & 0x1
        self.cant_cursor = (val7 >> 0) & 0x1
        self.unknown5 = unpack('B', tile_data[7:8])[0]

    def to_data(self, tile):
        tile_data = ''
        val1 = (tile.unknown1 << 6) + (tile.surface_type << 0)
        tile_data += pack('B', val1)
        tile_data += pack('B', tile.unknown2)
        tile_data += pack('B', tile.height)
        val4 = (tile.depth << 5) + (tile.slope_height << 0)
        tile_data += pack('B', val4)
        tile_data += pack('B', tile.slope_type)
        tile_data += pack('B', tile.unknown3)
        val7 = (tile.unknown4 << 2) + (tile.cant_walk << 1) + (tile.cant_cursor << 0)
        tile_data += pack('B', val7)
        tile_data += pack('B', tile.unknown5)
        return tile_data


class Terrain(object):
    def __init__(self):
        self.tiles = []

    def from_data(self, terrain_data):
        (x_count, z_count) = unpack('2B', terrain_data[0:2])
        offset = 2
        for y in range(2):
            level = []
            for z in range(z_count):
                row = []
                for x in range(x_count):
                    tile_data = terrain_data[offset:offset+8]
                    tile = Tile()
                    tile.from_data(tile_data)
                    row.append(tile)
                    offset += 8
                level.append(row)
            self.tiles.append(level)
            # Skip to second level of terrain data
            offset = 2 + 8 * 256

    def to_data(self, terrain):
        max_x = len(terrain.tiles[0][0])
        max_z = len(terrain.tiles[0])
        terrain_data = pack('BB', max_x, max_z)
        for level in terrain.tiles:
            for row in level:
                for tile in row:
                    tile_obj = Tile()
                    tile_data = tile_obj.to_data(tile)
                    terrain_data += tile_data
            # Skip to second level of terrain data
            terrain_data += '\x00' * (8 * 256 - 8 * max_x * max_z)
        return terrain_data


class Texture(object):
    def __init__(self):
        self.image = []

    def from_data(self, data):
        for y in range(1024):
            row = []
            for x in range(128):
                i = y * 128 + x
                pair = unpack('B', data[i:i+1])[0]
                pix1 = (pair >> 0) & 0xf
                pix2 = (pair >> 4) & 0xf
                row.append(pix1)
                row.append(pix2)
            self.image.append(row)

    def to_data(self, texture):
        texture_data = ''
        for y in range(1024):
            for x in range(128):
                pix1 = texture[y][x*2]
                pix2 = texture[y][x*2 + 1]
                pair = pack('B', (pix1 << 0) + (pix2 << 4))
                texture_data += pair
        return texture_data


class Map(object):
    def __init__(self):
        self.gns = GNS()
        self.situation = None
        self.texture_files = None
        self.resource_files = None
        self.texture = Texture_File()
        self.resources = Resources()
        self.extents = None
        self.hypotenuse = None

    def set_situation(self, situation):
        self.situation = situation % len(self.gns.situations)
        self.texture_files = self.gns.get_texture_files(self.situation)
        self.resource_files = self.gns.get_resource_files(self.situation)
        self.texture = Texture_File()
        self.resources = Resources()

    def read(self):
        self.texture.read(self.texture_files)
        self.resources.read(self.resource_files)

    def write(self):
        #self.texture.write()
        self.resources.write()

    def get_texture(self):
        texture = Texture()
        texture.from_data(self.texture.data)
        return texture

    def get_polygons(self):
        minx = 32767; miny = 32767; minz = 32767
        maxx = -32768; maxy = -32768; maxz = -32768
        polygons = (list(self.get_tex_3gon())
                + list(self.get_tex_4gon())
                + list(self.get_untex_3gon())
                + list(self.get_untex_4gon()))
        for polygon in polygons:
            for vertex in polygon.vertices():
                minx = min(minx, vertex.point.X)
                miny = min(miny, vertex.point.Y)
                minz = min(minz, vertex.point.Z)
                maxx = max(maxx, vertex.point.X)
                maxy = max(maxy, vertex.point.Y)
                maxz = max(maxz, vertex.point.Z)
            yield polygon
        self.extents = ((minx, miny, minz), (maxx, maxy, maxz))
        self.get_hypotenuse()

    def get_hypotenuse(self):
        from math import sqrt
        size_x = abs(self.extents[1][0] - self.extents[0][0])
        size_y = abs(self.extents[1][1] - self.extents[0][1])
        size_z = abs(self.extents[1][2] - self.extents[0][2])
        self.hypotenuse = sqrt(size_x**2 + size_z**2)

    def get_tex_3gon(self, toc_index=0x40):
        points = self.resources.get_tex_3gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_tex_3gon_vis()
        else:
            visangles = ['\x00\x00'] * 512
        normals = self.resources.get_tex_3gon_norm(toc_index)
        texcoords = self.resources.get_tex_3gon_uv(toc_index)
        terrain_coords = self.resources.get_tex_3gon_terrain_coords(toc_index)
        for point, visangle, normal, texcoord, terrain_coord in zip(points, visangles, normals, texcoords, terrain_coords):
            polygon = Triangle()
            polygon.from_data(point, visangle, normal, texcoord, terrain_coords=terrain_coord)
            yield polygon

    def get_tex_4gon(self, toc_index=0x40):
        points = self.resources.get_tex_4gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_tex_4gon_vis()
        else:
            visangles = ['\x00\x00'] * 768
        normals = self.resources.get_tex_4gon_norm(toc_index)
        texcoords = self.resources.get_tex_4gon_uv(toc_index)
        terrain_coords = self.resources.get_tex_4gon_terrain_coords(toc_index)
        for point, visangle, normal, texcoord, terrain_coord in zip(points, visangles, normals, texcoords, terrain_coords):
            polygon = Quad()
            polygon.from_data(point, visangle, normal, texcoord, terrain_coords=terrain_coord)
            yield polygon

    def get_untex_3gon(self, toc_index=0x40):
        points = self.resources.get_untex_3gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_untex_3gon_vis()
        else:
            visangles = ['\x00\x00'] * 64
        unknowns = self.resources.get_untex_3gon_unknown(toc_index)
        for point, visangle, unknown in zip(points, visangles, unknowns):
            polygon = Triangle()
            polygon.from_data(point, visangle, unknown5=unknown)
            yield polygon

    def get_untex_4gon(self, toc_index=0x40):
        points = self.resources.get_untex_4gon_xyz(toc_index)
        if toc_index == 0x40:
            visangles = self.resources.get_untex_4gon_vis()
        else:
            visangles = ['\x00\x00'] * 256
        unknowns = self.resources.get_untex_4gon_unknown(toc_index)
        for point, visangle, unknown in zip(points, visangles, unknowns):
            polygon = Quad()
            polygon.from_data(point, visangle, unknown5=unknown)
            yield polygon

    def get_color_palettes(self):
        palettes = self.resources.get_color_palettes()
        for palette_data in palettes:
            palette = Palette()
            palette.from_data(palette_data)
            yield palette

    def get_dir_lights(self):
        colors = self.resources.get_dir_light_rgb()
        normals = self.resources.get_dir_light_norm()
        for color, normal in zip(colors, normals):
            light = Directional_Light()
            light.from_data(color, normal)
            yield light

    def get_amb_light(self):
        color = self.resources.get_amb_light_rgb()
        light = Ambient_Light()
        light.from_data(color)
        return light

    def get_background(self):
        background_data = self.resources.get_background()
        background = Background()
        background.from_data(background_data)
        return background

    def get_terrain(self):
        terrain_data = self.resources.get_terrain()
        terrain = Terrain()
        terrain.from_data(terrain_data)
        return terrain

    def get_gray_palettes(self):
        palettes = self.resources.get_gray_palettes()
        for palette_data in palettes:
            palette = Palette()
            palette.from_data(palette_data)
            yield palette

    def put_texture(self, texture):
        tex = Texture()
        texture_data = tex.to_data(texture)
        self.texture.write(texture_data)

    def put_polygons(self, polygons):
        self.resources.put_polygons(polygons)

    def put_color_palettes(self, color_palettes):
        self.resources.put_palettes(color_palettes, 0x44)

    def put_dir_lights(self, dir_lights):
        self.resources.put_dir_lights(dir_lights)

    def put_amb_light(self, amb_light):
        light = Ambient_Light()
        light_data = light.to_data(amb_light)
        self.resources.put_amb_light_rgb(light_data)

    def put_background(self, background):
        bg = Background()
        bg_data = bg.to_data(background)
        self.resources.put_background(bg_data)

    def put_terrain(self, terrain):
        terr = Terrain()
        terrain_data = terr.to_data(terrain)
        self.resources.put_terrain(terrain_data)

    def put_visible_angles(self, polygons):
        self.resources.put_visible_angles(polygons)
