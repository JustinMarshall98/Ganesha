from os.path import getsize
from struct import pack, unpack
from math import ceil
from datetime import datetime


class Resource(object):
    def __init__(self):
        super(Resource, self).__init__()
        self.file_path = None
        self.file = None
        self.chunks = [''] * 49
        self.size = None

    def read(self, file_path):
        self.file_path = file_path
        self.size = getsize(self.file_path)
        self.file = open(self.file_path, 'rb')
        toc = list(unpack('<49I', self.file.read(0xc4)))
        self.file.seek(0)
        data = self.file.read()
        self.file.close()
        toc.append(self.size)
        for i, entry in enumerate(toc[:-1]):
            begin = toc[i]
            if begin == 0:
                continue
            end = None
            for j in range(i + 1, len(toc)):
                if toc[j]:
                    end = toc[j]
                    break
            self.chunks[i] = data[begin:end]
            print i, self.file_path, begin, end
        self.toc = toc

    def write(self):
        offset = 0xc4
        toc = []
        for chunk in self.chunks:
            if chunk:
                toc.append(offset)
                offset += len(chunk)
            else:
                toc.append(0)
        data = pack('<49I', *toc)
        for chunk in self.chunks:
            data += chunk
        print 'Writing', self.file_path
        dateTime = datetime.now()
        print dateTime
        old_size = self.size
        self.size = len(data)
        old_sectors = int(ceil(old_size / 2048.0))
        new_sectors = int(ceil(self.size / 2048.0))
        if new_sectors > old_sectors:
            print 'WARNING: File has grown from %u sectors to %u sectors!' % (old_sectors, new_sectors)
        elif new_sectors < old_sectors:
            print 'Note: File has shrunk from %u sectors to %u sectors.' % (old_sectors, new_sectors)
        self.file = open(self.file_path, 'wb')
        self.file.write(data)
        self.file.close()


class Resources(object):
    def __init__(self):
        super(Resources, self).__init__()
        self.chunks = [None] * 49

    def read(self, files):
        for file_path in files:
            resource = Resource()
            resource.read(file_path)
            for i in range(49):
                if self.chunks[i] is not None:
                    continue
                if resource.chunks[i]:
                    self.chunks[i] = resource

    def write(self):
        written = []
        for chunk in self.chunks:
            if chunk and chunk.file_path not in written:
                chunk.write()
                written.append(chunk.file_path)

    def get_tex_3gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8
        for i in range(tri_count):
            polygon_data = data[offset:offset+18]
            yield polygon_data
            offset += 18

    def get_tex_4gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18
        for i in range(quad_count):
            polygon_data = data[offset:offset+24]
            yield polygon_data
            offset += 24

    def get_untex_3gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24
        for i in range(untri_count):
            polygon_data = data[offset:offset+18]
            yield polygon_data
            offset += 18

    def get_untex_4gon_xyz(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18
        for i in range(unquad_count):
            polygon_data = data[offset:offset+24]
            yield polygon_data
            offset += 24

    def get_tex_3gon_norm(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24
        for i in range(tri_count):
            normal_data = data[offset:offset+18]
            yield normal_data
            offset += 18

    def get_tex_4gon_norm(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18
        for i in range(quad_count):
            normal_data = data[offset:offset+24]
            yield normal_data
            offset += 24

    def get_tex_3gon_uv(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24
        for i in range(tri_count):
            texcoord_data = data[offset:offset+10]
            yield texcoord_data
            offset += 10

    def get_tex_4gon_uv(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24 + tri_count * 10
        for i in range(quad_count):
            texcoord_data = data[offset:offset+12]
            yield texcoord_data
            offset += 12

    def get_untex_3gon_unknown(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24 + tri_count * 10 + quad_count * 12
        for i in range(untri_count):
            unk_data = data[offset:offset+4]
            yield unk_data
            offset += 4

    def get_untex_4gon_unknown(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24 + tri_count * 10 + quad_count * 12 + untri_count * 4
        for i in range(unquad_count):
            unk_data = data[offset:offset+4]
            yield unk_data
            offset += 4

    def get_tex_3gon_terrain_coords(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24 + tri_count * 10 + quad_count * 12 + untri_count * 4 + unquad_count * 4
        for i in range(tri_count):
            terrain_coord_data = data[offset:offset+2]
            yield terrain_coord_data
            offset += 2

    def get_tex_4gon_terrain_coords(self, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        (tri_count, quad_count, untri_count, unquad_count) = unpack('<4H', data[0:8])
        offset = 8 + tri_count * 18 + quad_count * 24 + untri_count * 18 + unquad_count * 24 + tri_count * 18 + quad_count * 24 + tri_count * 10 + quad_count * 12 + untri_count * 4 + unquad_count * 4 + tri_count * 2
        for i in range(quad_count):
            terrain_coord_data = data[offset:offset+2]
            yield terrain_coord_data
            offset += 2

    def get_tex_3gon_vis(self, toc_offset=0xb0):
        try:
            resource = self.chunks[toc_offset / 4]
            data = resource.chunks[toc_offset / 4]
            offset = 0x380
            for i in range(512):
                vis_data = data[offset:offset+2]
                yield vis_data
                offset += 2
        except:
            print("Error in get_tex_3gon_vis")

    def get_tex_4gon_vis(self, toc_offset=0xb0):
        try:
            resource = self.chunks[toc_offset / 4]
            data = resource.chunks[toc_offset / 4]
            offset = 0x380 + 512 * 2
            for i in range(768):
                vis_data = data[offset:offset+2]
                yield vis_data
                offset += 2
        except:
            print("Error in get_tex_4gon_vis")

    def get_untex_3gon_vis(self, toc_offset=0xb0):
        try:
            resource = self.chunks[toc_offset / 4]
            data = resource.chunks[toc_offset / 4]
            offset = 0x380 + 512 * 2 + 768 * 2
            for i in range(64):
                vis_data = data[offset:offset+2]
                yield vis_data
                offset += 2
        except:
            print("Error in get_untex_3gon_vis")

    def get_untex_4gon_vis(self, toc_offset=0xb0):
        try:
            resource = self.chunks[toc_offset / 4]
            data = resource.chunks[toc_offset / 4]
            offset = 0x380 + 512 * 2 + 768 * 2 + 64 * 2
            for i in range(256):
                vis_data = data[offset:offset+2]
                yield vis_data
                offset += 2
        except:
            print("Error in get_untex_4gon_vis")

    def get_color_palettes(self, toc_offset=0x44):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        for i in range(16):
            yield data[offset:offset+32]
            offset += 32

    def get_dir_light_rgb(self, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        for i in range(3):
            yield data[offset:offset+2] + data[offset+6:offset+8] + data[offset+12:offset+14]
            offset += 2

    def get_dir_light_norm(self, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 18
        for i in range(3):
            yield data[offset:offset+6]
            offset += 6

    def get_amb_light_rgb(self, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 36
        return data[offset:offset+3]

    def get_background(self, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 39
        return data[offset:offset+6]

    def get_terrain(self, toc_offset=0x68):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        return data

    def get_gray_palettes(self, toc_offset=0x7c):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        for i in range(16):
            yield data[offset:offset+32]
            offset += 32

    def put_polygons(self, polygons, toc_offset=0x40):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        tex_tri = []
        tex_quad = []
        untex_tri = []
        untex_quad = []
        for polygon in polygons:
            if hasattr(polygon.source, 'D') and polygon.source.A.normal:
                tex_quad.append(polygon.source)
            elif hasattr(polygon.source, 'D') and not polygon.source.A.normal:
                untex_quad.append(polygon.source)
            elif polygon.source.A.normal:
                tex_tri.append(polygon.source)
            else:
                untex_tri.append(polygon.source)
        polygons_data = pack('<4H', *[len(x) for x in [tex_tri, tex_quad, untex_tri, untex_quad]])
        for polygon in tex_tri:
            for abc in ['A', 'B', 'C']:
                coords = getattr(polygon, abc).point.coords
                polygons_data += pack('<3h', *coords)
        for polygon in tex_quad:
            for abc in ['A', 'B', 'C', 'D']:
                coords = getattr(polygon, abc).point.coords
                polygons_data += pack('<3h', *coords)
        for polygon in untex_tri:
            for abc in ['A', 'B', 'C']:
                coords = getattr(polygon, abc).point.coords
                polygons_data += pack('<3h', *coords)
        for polygon in untex_quad:
            for abc in ['A', 'B', 'C', 'D']:
                coords = getattr(polygon, abc).point.coords
                polygons_data += pack('<3h', *coords)
        for polygon in tex_tri:
            for abc in ['A', 'B', 'C']:
                coords = getattr(polygon, abc).normal.coords
                polygons_data += pack('<3h', *[int(x * 4096) for x in coords])
        for polygon in tex_quad:
            for abc in ['A', 'B', 'C', 'D']:
                coords = getattr(polygon, abc).normal.coords
                polygons_data += pack('<3h', *[int(x * 4096) for x in coords])
        for polygon in tex_tri:
            polygon_data = ''
            if polygon.unknown2 == 0:
                polygon.unknown2 = 120
                polygon.unknown3 = 3
            polygon_data += pack('BB', *polygon.A.texcoord.coords)
            val3 = (polygon.unknown1 << 4) + polygon.texture_palette
            polygon_data += pack('BB', *[val3, polygon.unknown2])
            polygon_data += pack('BB', *polygon.B.texcoord.coords)
            val7 = (polygon.unknown3 << 2) + polygon.texture_page
            polygon_data += pack('BB', *[val7, polygon.unknown4])
            polygon_data += pack('BB', *polygon.C.texcoord.coords)
            polygons_data += polygon_data
        for polygon in tex_quad:
            polygon_data = ''
            if polygon.unknown2 == 0:
                polygon.unknown2 = 120
                polygon.unknown3 = 3
            polygon_data += pack('BB', *polygon.A.texcoord.coords)
            val3 = (polygon.unknown1 << 4) + polygon.texture_palette
            polygon_data += pack('BB', *[val3, polygon.unknown2])
            polygon_data += pack('BB', *polygon.B.texcoord.coords)
            val7 = (polygon.unknown3 << 2) + polygon.texture_page
            polygon_data += pack('BB', *[val7, polygon.unknown4])
            polygon_data += pack('BB', *polygon.C.texcoord.coords)
            polygon_data += pack('BB', *polygon.D.texcoord.coords)
            polygons_data += polygon_data
        for polygon in untex_tri:
            polygons_data += polygon.unknown5
        for polygon in untex_quad:
            polygons_data += polygon.unknown5
        for polygon in tex_tri:
            val1 = (polygon.terrain_coords[1] << 1) + polygon.terrain_coords[2]
            polygons_data += pack('BB', val1, polygon.terrain_coords[0])
        for polygon in tex_quad:
            val1 = (polygon.terrain_coords[1] << 1) + polygon.terrain_coords[2]
            polygons_data += pack('BB', val1, polygon.terrain_coords[0])
        resource.chunks[toc_offset / 4] = polygons_data

    def put_palettes(self, palettes, toc_offset=0x44):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        palette_data = ''
        for palette in palettes:
            for c in range(16):
                (r, g, b, a) = palette.colors.colors[c]
                value = a << 15
                value += b << 10
                value += g << 5
                value += r << 0
                palette_data += pack('<H', value)
        resource.chunks[toc_offset / 4] = palette_data

    def put_dir_lights(self, dir_lights, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        light_data = ''
        for color in range(3):
            for light in dir_lights:
                light_data += pack('<h', light.color[color])
        for light in dir_lights:
            for dim in range(3):
                light_data += pack('<h', int(4096.0 * light.direction.coords[dim]))
        resource.chunks[toc_offset / 4] = data[:offset] + light_data + data[offset + 36:]

    def put_amb_light_rgb(self, light_data, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 36
        resource.chunks[toc_offset / 4] = data[:offset] + light_data + data[offset + 3:]

    def put_background(self, background_data, toc_offset=0x64):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 39
        resource.chunks[toc_offset / 4] = data[:offset] + background_data + data[offset + 6:]

    def put_terrain(self, terrain_data, toc_offset=0x68):
        resource = self.chunks[toc_offset / 4]
        data = resource.chunks[toc_offset / 4]
        offset = 0
        resource.chunks[toc_offset / 4] = data[:offset] + terrain_data + data[offset + len(terrain_data):]

    def put_visible_angles(self, polygons, toc_offset=0xb0):
        try:
            resource = self.chunks[toc_offset / 4]
            data = resource.chunks[toc_offset / 4]
            offset = 0x380
            tex_tri = []
            tex_quad = []
            untex_tri = []
            untex_quad = []
            for polygon in polygons:
                if hasattr(polygon.source, 'D') and polygon.source.A.normal:
                    tex_quad.append(polygon.source)
                elif hasattr(polygon.source, 'D') and not polygon.source.A.normal:
                    untex_quad.append(polygon.source)
                elif polygon.source.A.normal:
                    tex_tri.append(polygon.source)
                else:
                    untex_tri.append(polygon.source)
            tex_tri_data = ''
            tex_quad_data = ''
            untex_tri_data = ''
            untex_quad_data = ''
            for polygon in tex_tri:
                vis = sum([ x * 2**(15-i) for i, x in enumerate(polygon.visible_angles) ])
                tex_tri_data += pack('<H', vis)
            tex_tri_data += '\x00' * (1024 - len(tex_tri_data))
            for polygon in tex_quad:
                vis = sum([ x * 2**(15-i) for i, x in enumerate(polygon.visible_angles) ])
                tex_quad_data += pack('<H', vis)
            tex_quad_data += '\x00' * (1536 - len(tex_quad_data))
            for polygon in untex_tri:
                vis = sum([ x * 2**(15-i) for i, x in enumerate(polygon.visible_angles) ])
                untex_tri_data += pack('<H', vis)
            untex_tri_data += '\x00' * (128 - len(untex_tri_data))
            for polygon in untex_quad:
                vis = sum([ x * 2**(15-i) for i, x in enumerate(polygon.visible_angles) ])
                untex_quad_data += pack('<H', vis)
            untex_quad_data += '\x00' * (512 - len(untex_quad_data))
            visible_angles_data = tex_tri_data + tex_quad_data + untex_tri_data + untex_quad_data
            resource.chunks[toc_offset / 4] = data[:offset] + visible_angles_data + data[offset + len(visible_angles_data):]
        except:
            print("put visible angles error")