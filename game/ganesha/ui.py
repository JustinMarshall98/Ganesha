# Initialize window:
from pandac.PandaModules import WindowProperties
from direct.showbase.ShowBase import ShowBase
# Normal imports:
from pandac.PandaModules import CullFaceAttrib
from direct.showbase.DirectObject import DirectObject
from direct.fsm.FSM import FSM
import wx
import math
from world import World, Polygon, Tile
from ganesha import *

POLYGON_INPUT_ID = 1000
POLYGON_MOVE_ID = 1500
TERRAIN_INPUT_ID = 2000
VISIBILITY_INPUT_ID = 3000
PALETTE_INPUT_ID = 4000

slope_types = [
	(0x00, 'Flat 0'),
	(0x85, 'Incline N'),
	(0x52, 'Incline E'),
	(0x25, 'Incline S'),
	(0x58, 'Incline W'),
	(0x41, 'Convex NE'),
	(0x11, 'Convex SE'),
	(0x14, 'Convex SW'),
	(0x44, 'Convex NW'),
	(0x96, 'Concave NE'),
	(0x66, 'Concave SE'),
	(0x69, 'Concave SW'),
	(0x99, 'Concave NW'),
]

slope_type_names = [x[1] for x in slope_types]

visibility_bits = [
	(3, 'NW'),
	(9, 'NNW'),
	(10, 'NNE'),
	(4, 'NE'),
	(8, 'WNW'),
	(None, ''),
	(None, ''),
	(11, 'ENE'),
	(7, 'WSW'),
	(None, ''),
	(None, ''),
	(12, 'ESE'),
	(2, 'SW'),
	(6, 'SSW'),
	(13, 'SSE'),
	(5, 'SE'),
	(0, '?0'),
	(1, '?1'),
	(14, '?14'),
	(15, '?15'),
]

surface_types = {
	0x00: "Natural Surface",
	0x01: "Sand area",
	0x02: "Stalactite",
	0x03: "Grassland",
	0x04: "Thicket",
	0x05: "Snow",
	0x06: "Rocky cliff",
	0x07: "Gravel",
	0x08: "Wasteland",
	0x09: "Swamp",
	0x0A: "Marsh",
	0x0B: "Poisoned marsh",
	0x0C: "Lava rocks",
	0x0D: "Ice",
	0x0E: "Waterway",
	0x0F: "River",
	0x10: "Lake",
	0x11: "Sea",
	0x12: "Lava",
	0x13: "Road",
	0x14: "Wooden floor",
	0x15: "Stone floor",
	0x16: "Roof",
	0x17: "Stone wall",
	0x18: "Sky",
	0x19: "Darkness",
	0x1A: "Salt",
	0x1B: "Book",
	0x1C: "Obstacle",
	0x1D: "Rug",
	0x1E: "Tree",
	0x1F: "Box",
	0x20: "Brick",
	0x21: "Chimney",
	0x22: "Mud wall",
	0x23: "Bridge",
	0x24: "Water plant",
	0x25: "Stairs",
	0x26: "Furniture",
	0x27: "Ivy",
	0x28: "Deck",
	0x29: "Machine",
	0x2A: "Iron plate",
	0x2B: "Moss",
	0x2C: "Tombstone",
	0x2D: "Waterfall",
	0x2E: "Coffin",
	0x2F: "(blank)",
	0x30: "(blank)",
	0x3F: "Cross section"
}

def vector_to_sphere(x, y, z):
	import math
	radius = math.sqrt(x*x + y*y + z*z)
	if radius == 0:
		return (0, 0)
	elevation = math.acos(-y / radius)
	azimuth = math.atan2(x, z)
	return (math.degrees(elevation), math.degrees(azimuth))

def sphere_to_vector(elevation, azimuth):
	import math
	elevation = math.radians(elevation)
	azimuth = math.radians(azimuth)
	x = math.sin(elevation) * math.sin(azimuth)
	y = -math.cos(elevation)
	z = math.sin(elevation) * math.cos(azimuth)
	return (x, y, z)


class Mouse(DirectObject):
	def __init__(self, app):
		self.app = app
		self.init_collide()
		self.has_mouse = None
		self.prev_pos = None
		self.pos = None
		self.drag_start = None
		self.hovered_object = None
		self.button2 = False
		self.mouseTask = taskMgr.add(self.mouse_task, 'mouseTask')
		self.task = None
		self.accept('mouse1', self.mouse1)
		self.accept('control-mouse1', self.mouse1)
		self.accept('mouse1-up', self.mouse1_up)
		self.accept('mouse2', self.rotateCamera)
		self.accept('mouse2-up', self.stopCamera)
		self.accept('mouse3', self.rotateCamera)
		self.accept('mouse3-up', self.stopCamera)
		self.accept('wheel_up', self.wheel_up)
		self.accept('wheel_down', self.wheel_down)

	def init_collide(self):
		from pandac.PandaModules import CollisionTraverser, CollisionNode, GeomNode
		from pandac.PandaModules import CollisionHandlerQueue, CollisionRay
		self.cTrav = CollisionTraverser('MousePointer')
		self.cQueue = CollisionHandlerQueue()
		self.cNode = CollisionNode('MousePointer')
		self.cNodePath = base.camera.attachNewNode(self.cNode)
		self.cNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
		self.cRay = CollisionRay()
		self.cNode.addSolid(self.cRay)
		self.cTrav.addCollider(self.cNodePath, self.cQueue)

	def find_object(self):
		if self.app.world.node_path:
			self.cRay.setFromLens(base.camNode, self.pos.getX(), self.pos.getY())
			if self.app.terrain_mode in [MESH_ONLY, MOSTLY_MESH]:
				self.cTrav.traverse(self.app.world.node_path_mesh)
			elif self.app.terrain_mode in [MOSTLY_TERRAIN, TERRAIN_ONLY]:
				self.cTrav.traverse(self.app.world.node_path_terrain)
			if self.cQueue.getNumEntries() > 0:
				self.cQueue.sortEntries()
				return self.cQueue.getEntry(0).getIntoNodePath()
		return None

	def mouse_task(self, task):
		from pandac.PandaModules import Point2
		action = task.cont
		self.has_mouse = base.mouseWatcherNode.hasMouse()
		if self.has_mouse:
			self.pos = base.mouseWatcherNode.getMouse()
			if self.prev_pos:
				self.delta = self.pos - self.prev_pos
			else:
				self.delta = None
			if self.task:
				action = self.task(task)
		elif self.app.uv_edit_window.has_mouse():
			action = self.app.uv_edit_window.mouse_task(task)
		else:
			self.pos = None
		if self.pos:
			self.prev_pos = Point2(self.pos.getX(), self.pos.getY())
		return action

	def hover(self, task):
		if self.hovered_object:
			self.hovered_object.unhover()
			self.hovered_object = None
		if self.button2:
			self.camera_drag()
		hovered_node_path = self.find_object()
		if hovered_node_path:
			polygon = hovered_node_path.findNetTag('polygon_i')
			if not polygon.isEmpty():
				tag = polygon.getTag('polygon_i')
				i = int(tag)
				self.hovered_object = self.app.world.polygons[i]
				self.hovered_object.hover()
			tile = hovered_node_path.findNetTag('terrain_xyz')
			if not tile.isEmpty():
				tag = tile.getTag('terrain_xyz')
				(x, y, z) = [int(i) for i in tag.split(',')]
				self.hovered_object = self.app.world.terrain.tiles[y][z][x]
				self.hovered_object.hover()
		return task.cont
	


	def mouse1(self):
		if base.mouseWatcherNode.hasMouse():
			self.app.state.request('mouse1')
		elif self.app.uv_edit_window.has_mouse():
			self.app.uv_edit_window.on_mouse1()

	def mouse1_up(self):
		self.app.state.request('mouse1-up')
		self.app.uv_edit_window.on_mouse1_up()

	def camera_drag(self):
		if self.delta:
			old_heading = base.camera.getH()
			new_heading = old_heading - self.delta.getX() * 180
			new_heading = new_heading % 360
			old_pitch = base.camera.getP()
			new_pitch = old_pitch + self.delta.getY() * 90
			new_pitch = max(-90, min(0, new_pitch))
			new_heading = 270 + new_heading
			new_pitch = - new_pitch
			self.app.world.set_camera_angle(new_heading, new_pitch)

	def rotateCamera(self):
		self.button2 = True
		self.app.state.request('mouse2')

	def stopCamera(self):
		self.button2 = False
		self.app.state.request('mouse2-up')

	def wheel_up(self):
		if base.mouseWatcherNode.hasMouse():
			lens = base.cam.node().getLens()
			size = lens.getFilmSize()
			lens.setFilmSize(size / 1.2)
			scale = self.app.world.background.node_path.getScale()
			self.app.world.background.node_path.setScale(scale / 1.2)
		elif self.app.uv_edit_window.has_mouse():
			self.app.uv_edit_window.zoom_in()
			

	def wheel_down(self):
		if base.mouseWatcherNode.hasMouse():
			lens = base.cam.node().getLens()
			size = lens.getFilmSize()
			lens.setFilmSize(size * 1.2)
			scale = self.app.world.background.node_path.getScale()
			self.app.world.background.node_path.setScale(scale *1.2)
		elif self.app.uv_edit_window.has_mouse():
			self.app.uv_edit_window.zoom_out()


class ViewerState(FSM):
	def __init__(self, app, name):
		FSM.__init__(self, name)
		self.app = app

	def enterSpin(self):
		#print 'enterSpin'
		taskMgr.add(self.app.world.spin_camera, 'spin_camera')
		self.app.mouse.task = self.app.mouse.hover

	def filterSpin(self, request, args):
		#print 'filterSpin'
		if request == 'mouse2':
			return 'FreeRotate'
		if request == 'mouse1':
			self.app.select(self.app.mouse.hovered_object)
		return None

	def exitSpin(self):
		#print 'exitSpin'
		taskMgr.remove('spin_camera')
		self.app.mouse.task = None

	def enterFreeRotate(self):
		#print 'enterFreeRotate'
		self.app.mouse.task = self.app.mouse.hover

	def filterFreeRotate(self, request, args):
		if request == 'mouse1' or request == 'control-mouse1':
			self.app.select(self.app.mouse.hovered_object)
		return None

	def exitFreeRotate(self):
		#print 'exitFreeRotate'
		self.app.mouse.task = None


class ViewerMouse(Mouse):
	pass


class PolygonAddWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		# Prompt
		prompt = wx.StaticText(panel, wx.ID_ANY, 'Create what kind of polygon?')
		sizer_sections.Add(prompt, flag=wx.ALL, border=10)
		# Options
		sizer_options = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(panel, wx.ID_ANY, 'Sides:')
		sizer_options.Add(label)
		self.choice_sides = wx.Choice(panel, wx.ID_ANY, choices=['3', '4'])
		sizer_options.Add(self.choice_sides)
		label = wx.StaticText(panel, wx.ID_ANY, 'Texture:')
		sizer_options.Add(label)
		self.choice_texture = wx.Choice(panel, wx.ID_ANY, choices=['Textured', 'Black'])
		sizer_options.Add(self.choice_texture)
		sizer_sections.Add(sizer_options, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Buttons
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		ok_button = wx.Button(panel, wx.ID_OK)
		ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
		sizer_buttons.Add(ok_button)
		cancel_button = wx.Button(panel, wx.ID_CANCEL)
		cancel_button.Bind(wx.EVT_BUTTON, self.on_close)
		sizer_buttons.Add(cancel_button)
		sizer_sections.Add(sizer_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_ok(self, event):
		sides = 4 if self.choice_sides.GetSelection() else 3
		texture = False if self.choice_texture.GetSelection() else True
		self.app.world.add_polygon(sides, texture)
		self.on_close(None)

	def on_close(self, event):
		self.MakeModal(False)
		self.Show(False)


class PolygonEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		# Vertex point, normal, and UV coordinates
		sizer_point_table = wx.FlexGridSizer(rows=13, cols=7)
		self.inputs = {}
		for i, point in enumerate(['', '', 'A', 'B', 'C', 'D', '']):
			point_label = wx.StaticText(panel, wx.ID_ANY, point, size=wx.Size(20, -1))
			if point == 'A':
				point_label.SetForegroundColour('red')
			elif point == 'B':
				point_label.SetForegroundColour('green')
			elif point == 'C':
				point_label.SetForegroundColour('blue')
			elif point == 'D':
				point_label.SetForegroundColour(wx.Colour(175, 175, 0))
			sizer_point_table.Add(point_label)
		for i, data in enumerate(['X', 'Y', 'Z', 'copyVector', 'pasteVector', 'nE', 'nA', 'copyLighting', 'pasteLighting', 'U', 'V', 'copyUV', 'pasteUV']):
			if data == 'copyVector' or data == 'pasteVector' or data == 'copyLighting' or data == 'pasteLighting' or data == 'copyUV' or data == 'pasteUV':
				data_label = wx.StaticText(panel, wx.ID_ANY, "", size=wx.Size(20, -1))
			else:
				data_label = wx.StaticText(panel, wx.ID_ANY, data, size=wx.Size(20, -1))
			if data == 'X':
				data_label.SetForegroundColour('red')
				sizer_point_table.Add(data_label)
				button = wx.Button(panel, POLYGON_MOVE_ID + 0, '-28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_move)
			elif data == 'Y':
				data_label.SetForegroundColour('green')
				sizer_point_table.Add(data_label)
				button = wx.Button(panel, POLYGON_MOVE_ID + 2, '-12', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_move)
			elif data == 'Z':
				data_label.SetForegroundColour('blue')
				sizer_point_table.Add(data_label)
				button = wx.Button(panel, POLYGON_MOVE_ID + 4, '-28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_move)
			elif data == 'copyVector':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Copy All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_vertex_all)
				#sizer_point_table.Add(button)
			elif data == 'pasteVector':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_vertex)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Paste All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_vertex_all)
				#sizer_point_table.Add(button)
			elif data == 'copyLighting':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Copy All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_lighting_all)
				#sizer_point_table.Add(button)
			elif data == 'pasteLighting':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_lighting)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Paste All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_lighting_all)
				#sizer_point_table.Add(button)
			elif data == 'copyUV':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Copy', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Copy All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_copy_UV_all)
				#sizer_point_table.Add(button)
			elif data == 'pasteUV':
				sizer_point_table.Add(data_label)
				sizer_point_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
				button = wx.Button(panel, 0, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 1, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 2, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 3, 'Paste', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_UV)
				sizer_point_table.Add(button)
				button = wx.Button(panel, 4, 'Paste All', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_paste_UV_all)
				#sizer_point_table.Add(button)
			elif data == 'U':
				data_label.SetForegroundColour('purple')
				sizer_point_table.Add(data_label)
				button = wx.Button(panel, POLYGON_MOVE_ID + 6, '-20', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_move)
			elif data == 'V':
				data_label.SetForegroundColour('orange')
				sizer_point_table.Add(data_label)
				button = wx.Button(panel, POLYGON_MOVE_ID + 8, '-20', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.on_move)
			else:
				sizer_point_table.Add(data_label)
				button = wx.StaticText(panel, wx.ID_ANY, '')
			sizer_point_table.Add(button)
			if data != 'copyVector' and data != 'pasteVector' and data != 'copyLighting' and data != 'pasteLighting' and data != 'copyUV' and data != 'pasteUV':
				for j, point in enumerate(['A', 'B', 'C', 'D']):
					input_id = POLYGON_INPUT_ID + i * 4 + j
					data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
					sizer_point_table.Add(data_input)
					self.inputs[(data, point)] = data_input
				if data == 'X':
					button = wx.Button(panel, POLYGON_MOVE_ID + 1, '+28', size=wx.Size(50, -1))
					button.Bind(wx.EVT_BUTTON, self.on_move)
				elif data == 'Y':
					button = wx.Button(panel, POLYGON_MOVE_ID + 3, '+12', size=wx.Size(50, -1))
					button.Bind(wx.EVT_BUTTON, self.on_move)
				elif data == 'Z':
					button = wx.Button(panel, POLYGON_MOVE_ID + 5, '+28', size=wx.Size(50, -1))
					button.Bind(wx.EVT_BUTTON, self.on_move)
				elif data == 'U':
					button = wx.Button(panel, POLYGON_MOVE_ID + 7, '+20', size=wx.Size(50, -1))
					button.Bind(wx.EVT_BUTTON, self.on_move)
				elif data == 'V':
					button = wx.Button(panel, POLYGON_MOVE_ID + 9, '+20', size=wx.Size(50, -1))
					button.Bind(wx.EVT_BUTTON, self.on_move)
				else:
					button = wx.StaticText(panel, wx.ID_ANY, '')
				sizer_point_table.Add(button)
		sizer_sections.Add(sizer_point_table, flag=wx.ALL, border=10)
		
		
		
		#make new horizontal area for rotate buttons
		sizer_rotate_buttons = wx.BoxSizer(wx.HORIZONTAL)
		
		#create button with label Rotate 90
		button = wx.Button(panel, wx.ID_ANY, 'Rotate Polygon Face 90\xb0')
		#set it to run rotate90 on click
		button.Bind(wx.EVT_BUTTON, self.neg_rotateFace90)
		#add button to the horizontal box
		sizer_rotate_buttons.Add(button)
	
		#create button with label Rotate -90
		button = wx.Button(panel, wx.ID_ANY, 'Rotate Polygon Face -90\xb0')
		#set it to run rotate90 on click
		button.Bind(wx.EVT_BUTTON, self.rotateFace90)
		#add button to the horizontal box
		sizer_rotate_buttons.Add(button)
		
	
		
		#add horizontal box to whole list
		sizer_sections.Add(sizer_rotate_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		
		
		
		#make new horizontal area for rotate buttons
		sizer_rotate_colbuttons = wx.BoxSizer(wx.HORIZONTAL)

		button_label = wx.StaticText(panel, wx.ID_ANY, "(X, Z)", size=wx.Size(30, -1))
		sizer_rotate_colbuttons.Add(button_label)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate A 90\xb0')
		button.SetForegroundColour('red')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonAOnXZ)
		sizer_rotate_colbuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate B 90\xb0')
		button.SetForegroundColour('green')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonBOnXZ)
		sizer_rotate_colbuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate C 90\xb0')
		button.SetForegroundColour('blue')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonCOnXZ)
		sizer_rotate_colbuttons.Add(button)

		button = wx.Button(panel, wx.ID_ANY, 'Rotate D 90\xb0')
		button.SetForegroundColour(wx.Colour(175, 175, 0))
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonDOnXZ)
		sizer_rotate_colbuttons.Add(button)
		
		#add horizontal box to whole list
		sizer_sections.Add(sizer_rotate_colbuttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		
		#make new horizontal area for rotate on XY buttons
		sizer_rotate_xybuttons = wx.BoxSizer(wx.HORIZONTAL)

		button_label = wx.StaticText(panel, wx.ID_ANY, "(X, Y)", size=wx.Size(30, -1))
		sizer_rotate_xybuttons.Add(button_label)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate A 90\xb0')
		button.SetForegroundColour('red')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonAOnXY)
		sizer_rotate_xybuttons.Add(button)

		button = wx.Button(panel, wx.ID_ANY, 'Rotate B 90\xb0')
		button.SetForegroundColour('green')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonBOnXY)
		sizer_rotate_xybuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate C 90\xb0')
		button.SetForegroundColour('blue')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonCOnXY)
		sizer_rotate_xybuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate D 90\xb0')
		button.SetForegroundColour(wx.Colour(175, 175, 0))
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonDOnXY)
		sizer_rotate_xybuttons.Add(button)
		
		#add horizontal box to whole list
		sizer_sections.Add(sizer_rotate_xybuttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)


		#make new horizontal area for rotate on XY buttons
		sizer_rotate_zybuttons = wx.BoxSizer(wx.HORIZONTAL)

		button_label = wx.StaticText(panel, wx.ID_ANY, "(Z, Y)", size=wx.Size(30, -1))
		sizer_rotate_zybuttons.Add(button_label)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate A 90\xb0')
		button.SetForegroundColour('red')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonAOnZY)
		sizer_rotate_zybuttons.Add(button)

		button = wx.Button(panel, wx.ID_ANY, 'Rotate B 90\xb0')
		button.SetForegroundColour('green')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonBOnZY)
		sizer_rotate_zybuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate C 90\xb0')
		button.SetForegroundColour('blue')
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonCOnZY)
		sizer_rotate_zybuttons.Add(button)
		
		button = wx.Button(panel, wx.ID_ANY, 'Rotate D 90\xb0')
		button.SetForegroundColour(wx.Colour(175, 175, 0))
		button.Bind(wx.EVT_BUTTON, self.rotatePolygonDOnZY)
		sizer_rotate_zybuttons.Add(button)
		
		#add horizontal box to whole list
		sizer_sections.Add(sizer_rotate_zybuttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		
		sizer_mid_buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Guess normal vectors button
		self.button_guess_normal = wx.Button(panel, wx.ID_ANY, 'Guess Normal Vectors')
		self.button_guess_normal.Bind(wx.EVT_BUTTON, self.on_guess_normal)
		sizer_mid_buttons.Add(self.button_guess_normal)
		# Show UV button
		self.button_show_uv = wx.Button(panel, wx.ID_ANY, 'Show UV')
		self.button_show_uv.Bind(wx.EVT_BUTTON, self.on_show_uv)
		sizer_mid_buttons.Add(self.button_show_uv)
		# Find tile and select it
		button = wx.Button(panel, wx.ID_ANY, 'Find Terrain Tile')
		button.Bind(wx.EVT_BUTTON, self.on_find_tile)
		sizer_mid_buttons.Add(button)
		sizer_sections.Add(sizer_mid_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		

		# Texture page, palette | Terrain X, Z
		texture_terrain_sizer = wx.BoxSizer(wx.HORIZONTAL)
		page_palette_sizer = wx.FlexGridSizer(rows=2, cols=2)
		input_id += 1
		label = wx.StaticText(panel, wx.ID_ANY, 'Tex. Page:')
		data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
		page_palette_sizer.Add(label)
		page_palette_sizer.Add(data_input)
		self.inputs['page'] = data_input
		input_id += 1
		label = wx.StaticText(panel, wx.ID_ANY, 'Tex. Palette:')
		data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
		page_palette_sizer.Add(label)
		page_palette_sizer.Add(data_input)
		self.inputs['palette'] = data_input
		texture_terrain_sizer.Add(page_palette_sizer)
		terrain_x_z_sizer = wx.FlexGridSizer(rows=3, cols=2)
		input_id += 1
		label = wx.StaticText(panel, wx.ID_ANY, 'Terrain X:')
		data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
		terrain_x_z_sizer.Add(label)
		terrain_x_z_sizer.Add(data_input)
		self.inputs['tX'] = data_input
		input_id += 1
		label = wx.StaticText(panel, wx.ID_ANY, 'Terrain Z:')
		data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
		terrain_x_z_sizer.Add(label)
		terrain_x_z_sizer.Add(data_input)
		self.inputs['tZ'] = data_input
		input_id += 1
		label = wx.StaticText(panel, wx.ID_ANY, 'Terr. Lvl:')
		data_input = wx.TextCtrl(panel, input_id, size=wx.Size(60, -1))
		terrain_x_z_sizer.Add(label)
		terrain_x_z_sizer.Add(data_input)
		self.inputs['tlvl'] = data_input
		texture_terrain_sizer.Add(terrain_x_z_sizer)
		
		
		
		
		sizer_sections.Add(texture_terrain_sizer, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Visibility Angles
		label = wx.StaticText(panel, wx.ID_ANY, 'Invisible from:')
		sizer_sections.Add(label, flag=wx.LEFT | wx.RIGHT, border=10)
		sizer_angles = wx.FlexGridSizer(rows=4, cols=8)
		for bit, label in visibility_bits:
			if bit is not None:
				input_ = wx.CheckBox(panel, VISIBILITY_INPUT_ID + bit)
				self.inputs[('visibility', bit)] = input_
				sizer_angles.Add(input_)
			else:
				static_text = wx.StaticText(panel, wx.ID_ANY, '')
				sizer_angles.Add(static_text)
			static_text = wx.StaticText(panel, wx.ID_ANY, label)
			sizer_angles.Add(static_text)
		sizer_sections.Add(sizer_angles, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		#self.inputs['unknown1'] = wx.TextCtrl(panel, wx.ID_ANY)
		#sizer_sections.Add(self.inputs['unknown1'], flag=wx.ALL, border=10)
		#self.inputs['unknown2'] = wx.TextCtrl(panel, wx.ID_ANY)
		#sizer_sections.Add(self.inputs['unknown2'], flag=wx.ALL, border=10)
		#self.inputs['unknown3'] = wx.TextCtrl(panel, wx.ID_ANY)
		#sizer_sections.Add(self.inputs['unknown3'], flag=wx.ALL, border=10)
		#self.inputs['unknown4'] = wx.TextCtrl(panel, wx.ID_ANY)
		#sizer_sections.Add(self.inputs['unknown4'], flag=wx.ALL, border=10)
		#self.inputs['unknown5'] = wx.TextCtrl(panel, wx.ID_ANY)
		#sizer_sections.Add(self.inputs['unknown5'], flag=wx.ALL, border=10)
		# Buttons
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		apply_button = wx.Button(panel, wx.ID_APPLY)
		apply_button.Bind(wx.EVT_BUTTON, self.to_data)
		sizer_buttons.Add(apply_button, flag=wx.RIGHT, border=20)
		delete_button = wx.Button(panel, wx.ID_DELETE)
		delete_button.Bind(wx.EVT_BUTTON, self.on_delete)
		sizer_buttons.Add(delete_button, flag=wx.RIGHT, border=20)
		sizer_sections.Add(sizer_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_copy_vertex(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		self.copyX = self.inputs[('X', vert)].GetValue()
		self.copyY = self.inputs[('Y', vert)].GetValue()
		self.copyZ = self.inputs[('Z', vert)].GetValue()

	def on_paste_vertex(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		try:
			self.inputs[('X', vert)].SetValue(str(self.copyX))
			self.inputs[('Y', vert)].SetValue(str(self.copyY))
			self.inputs[('Z', vert)].SetValue(str(self.copyZ))
			self.to_data(None)
		except:
			print("No vertex info to paste")

	def on_copy_vertex_all(self, event):
		self.copyXA = self.inputs[('X', 'A')].GetValue()
		self.copyYA = self.inputs[('Y', 'A')].GetValue()
		self.copyZA = self.inputs[('Z', 'A')].GetValue()
		self.copyXB = self.inputs[('X', 'B')].GetValue()
		self.copyYB = self.inputs[('Y', 'B')].GetValue()
		self.copyZB = self.inputs[('Z', 'B')].GetValue()
		self.copyXC = self.inputs[('X', 'C')].GetValue()
		self.copyYC = self.inputs[('Y', 'C')].GetValue()
		self.copyZC = self.inputs[('Z', 'C')].GetValue()
		self.copyXD = self.inputs[('X', 'D')].GetValue()
		self.copyYD = self.inputs[('Y', 'D')].GetValue()
		self.copyZD = self.inputs[('Z', 'D')].GetValue()

	def on_paste_vertex_all(self, event):
		try:
			self.inputs[('X', 'A')].SetValue(str(self.copyXA))
			self.inputs[('Y', 'A')].SetValue(str(self.copyYA))
			self.inputs[('Z', 'A')].SetValue(str(self.copyZA))
			self.inputs[('X', 'B')].SetValue(str(self.copyXB))
			self.inputs[('Y', 'B')].SetValue(str(self.copyYB))
			self.inputs[('Z', 'B')].SetValue(str(self.copyZB))
			self.inputs[('X', 'C')].SetValue(str(self.copyXC))
			self.inputs[('Y', 'C')].SetValue(str(self.copyYC))
			self.inputs[('Z', 'C')].SetValue(str(self.copyZC))
			self.inputs[('X', 'D')].SetValue(str(self.copyXD))
			self.inputs[('Y', 'D')].SetValue(str(self.copyYD))
			self.inputs[('Z', 'D')].SetValue(str(self.copyZD))
			self.to_data(None)
		except:
			print("No vertex info to paste")

	def on_copy_UV(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		self.copyU = self.inputs[('U', vert)].GetValue()
		self.copyV = self.inputs[('V', vert)].GetValue()

	def on_paste_UV(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		try:
			self.inputs[('U', vert)].SetValue(str(self.copyU))
			self.inputs[('V', vert)].SetValue(str(self.copyV))
			self.to_data(None)
		except:
			print("No UV info to paste")
	
	def on_copy_UV_all(self, event):
		self.copyUV_UA = self.inputs[('U', 'A')].GetValue()
		self.copyUV_UB = self.inputs[('U', 'B')].GetValue()
		self.copyUV_UC = self.inputs[('U', 'C')].GetValue()
		self.copyUV_UD = self.inputs[('U', 'D')].GetValue()
		self.copyUV_VA = self.inputs[('V', 'A')].GetValue()
		self.copyUV_VB = self.inputs[('V', 'B')].GetValue()
		self.copyUV_VC = self.inputs[('V', 'C')].GetValue()
		self.copyUV_VD = self.inputs[('V', 'D')].GetValue()
		
	def on_paste_UV_all(self, event):
		try:
			self.inputs[('U', 'A')].SetValue(str(self.copyUV_UA))
			self.inputs[('U', 'B')].SetValue(str(self.copyUV_UB))
			self.inputs[('U', 'C')].SetValue(str(self.copyUV_UC))
			self.inputs[('U', 'D')].SetValue(str(self.copyUV_UD))
			self.inputs[('V', 'A')].SetValue(str(self.copyUV_VA))
			self.inputs[('V', 'B')].SetValue(str(self.copyUV_VB))
			self.inputs[('V', 'C')].SetValue(str(self.copyUV_VC))
			self.inputs[('V', 'D')].SetValue(str(self.copyUV_VD))
			self.to_data(None)
		except:
			print("No UV info to paste")

	def on_copy_lighting(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		self.copynE = self.inputs[('nE', vert)].GetValue()
		self.copynA = self.inputs[('nA', vert)].GetValue()

	def on_paste_lighting(self, event):
		command = event.GetId()
		vert = ''
		
		if command == 0:
			vert = 'A'
		if command == 1:
			vert = 'B'
		if command == 2:
			vert = 'C'
		if command == 3:
			vert = 'D'
		
		try:
			self.inputs[('nE', vert)].SetValue(str(self.copynE))
			self.inputs[('nA', vert)].SetValue(str(self.copynA))
			self.to_data(None)
		except:
			print("No nE/nA info to paste")
	
	def on_copy_lighting_all(self, event):
		self.copy_nEA = self.inputs[('nE', 'A')].GetValue()
		self.copy_nEB = self.inputs[('nE', 'B')].GetValue()
		self.copy_nEC = self.inputs[('nE', 'C')].GetValue()
		self.copy_nED = self.inputs[('nE', 'D')].GetValue()
		self.copy_nAA = self.inputs[('nA', 'A')].GetValue()
		self.copy_nAB = self.inputs[('nA', 'B')].GetValue()
		self.copy_nAC = self.inputs[('nA', 'C')].GetValue()
		self.copy_nAD = self.inputs[('nA', 'D')].GetValue()
		
	def on_paste_lighting_all(self, event):
		try:
			self.inputs[('nE', 'A')].SetValue(str(self.copy_nEA))
			self.inputs[('nE', 'B')].SetValue(str(self.copy_nEB))
			self.inputs[('nE', 'C')].SetValue(str(self.copy_nEC))
			self.inputs[('nE', 'D')].SetValue(str(self.copy_nED))
			self.inputs[('nA', 'A')].SetValue(str(self.copy_nAA))
			self.inputs[('nA', 'B')].SetValue(str(self.copy_nAB))
			self.inputs[('nA', 'C')].SetValue(str(self.copy_nAC))
			self.inputs[('nA', 'D')].SetValue(str(self.copy_nAD))
			self.to_data(None)
		except:
			print("No nE/nA info to paste")

	def on_close(self, event):
		self.app.uv_edit_window.close()
		self.Show(False)

	def on_move(self, event):
		button_id = event.GetId() - POLYGON_MOVE_ID
		if button_id in [0, 1]:
			dim = 'X'
			amount = 28
		elif button_id in [2, 3]:
			dim = 'Y'
			amount = 12
		elif button_id in [4, 5]:
			dim = 'Z'
			amount = 28
		elif button_id in [6, 7]:
			dim = 'U'
			amount = 20
		elif button_id in [8, 9]:
			dim = 'V'
			amount = 20
		if button_id % 2 == 0:
			sign = -1
		else:
			sign = 1
		inputs = [
			self.inputs[(dim, 'A')],
			self.inputs[(dim, 'B')],
			self.inputs[(dim, 'C')],
			self.inputs[(dim, 'D')],
		]
		for input_ in inputs:
			if input_.IsEnabled():
				input_.SetValue(str(int(input_.GetValue()) + sign * amount))
		self.to_data(None)
		
	def on_delete(self, event):
		sure = wx.MessageDialog(self, 'Are you sure?', style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		choice = sure.ShowModal()
		if choice == wx.ID_YES:
			self.app.delete_polygon()

	def clear_inputs(self):
		#print 'clearing'
		pass

	def on_guess_normal(self, event):
		A = self.app.selected_object.source.A.point
		B = self.app.selected_object.source.B.point
		C = self.app.selected_object.source.C.point
		vector1 = (C.X - A.X, C.Y - A.Y, C.Z - A.Z)
		vector2 = (B.X - A.X, B.Y - A.Y, B.Z - A.Z)
		# Cross product
		nX = vector1[1] * vector2[2] - vector1[2] * vector2[1]
		nY = vector1[2] * vector2[0] - vector1[0] * vector2[2]
		nZ = vector1[0] * vector2[1] - vector1[1] * vector2[0]
		(elevation, azimuth) = vector_to_sphere(nX, nY, nZ)
		pts = ['A', 'B', 'C']
		if hasattr(self.app.selected_object.source, 'D'):
			pts.append('D')
		for pt in pts:
			self.inputs[('nE', pt)].SetValue(str(90 - elevation))
			self.inputs[('nA', pt)].SetValue(str(azimuth))

	def on_show_uv(self, event):
		self.app.uv_edit_window.open()
		pass

	def on_find_tile(self, event):
		self.app.find_tile()

		
	def rotateFace90(self, event):
	
		if hasattr(self.app.selected_object.source, 'D'):	
			for dim in ['X', 'Y', 'Z', 'nE', 'nA']:
				storedValueA = self.inputs[(dim, 'A')].GetValue()
				storedValueB = self.inputs[(dim, 'B')].GetValue()
				storedValueC = self.inputs[(dim, 'C')].GetValue()
				storedValueD = self.inputs[(dim, 'D')].GetValue()
					
				self.inputs[(dim, 'B')].SetValue(str(storedValueD))
				self.inputs[(dim, 'D')].SetValue(str(storedValueC))
				self.inputs[(dim, 'C')].SetValue(str(storedValueA))
				self.inputs[(dim, 'A')].SetValue(str(storedValueB))
		else:
			for dim in ['X', 'Y', 'Z', 'nE', 'nA']:
				storedValueA = self.inputs[(dim, 'A')].GetValue()
				storedValueB = self.inputs[(dim, 'B')].GetValue()
				storedValueC = self.inputs[(dim, 'C')].GetValue()
					
				self.inputs[(dim, 'A')].SetValue(str(storedValueB))
				self.inputs[(dim, 'C')].SetValue(str(storedValueA))
				self.inputs[(dim, 'B')].SetValue(str(storedValueC))
		self.to_data(None)
				
	
	def neg_rotateFace90(self, event):
	
		if hasattr(self.app.selected_object.source, 'D'):
			for dim in ['X', 'Y', 'Z', 'nE', 'nA']:
				storedValueA = self.inputs[(dim, 'A')].GetValue()
				storedValueB = self.inputs[(dim, 'B')].GetValue()
				storedValueC = self.inputs[(dim, 'C')].GetValue()
				storedValueD = self.inputs[(dim, 'D')].GetValue()
				
				self.inputs[(dim, 'B')].SetValue(str(storedValueA))
				self.inputs[(dim, 'D')].SetValue(str(storedValueB))
				self.inputs[(dim, 'C')].SetValue(str(storedValueD))
				self.inputs[(dim, 'A')].SetValue(str(storedValueC))
		else:
			for dim in ['X', 'Y', 'Z', 'nE', 'nA']:
				storedValueA = self.inputs[(dim, 'A')].GetValue()
				storedValueB = self.inputs[(dim, 'B')].GetValue()
				storedValueC = self.inputs[(dim, 'C')].GetValue()
				
				self.inputs[(dim, 'B')].SetValue(str(storedValueA))
				self.inputs[(dim, 'C')].SetValue(str(storedValueB))
				self.inputs[(dim, 'A')].SetValue(str(storedValueC))
		self.to_data(None)
		

	def rotatePolygonAOnXZ(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'A')].GetValue())
		vector[1] = int(self.inputs[('Z', 'A')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['A', 'B', 'D', 'C']:
			x = int(self.inputs[('X', pts)].GetValue())
			z = int(self.inputs[('Z', pts)].GetValue())
			coordinates.append([x, z])
		
		for xNum in range(0,4):
			for zNum in range(0,2):
				coordinates[xNum][zNum] -= vector[zNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['A', 'B', 'D', 'C']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Z', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)
		
	def rotatePolygonBOnXZ(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'B')].GetValue())
		vector[1] = int(self.inputs[('Z', 'B')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['B', 'D', 'C', 'A']:
			x = int(self.inputs[('X', pts)].GetValue())
			z = int(self.inputs[('Z', pts)].GetValue())
			coordinates.append([x, z])
		
		for xNum in range(0,4):
			for zNum in range(0,2):
				coordinates[xNum][zNum] -= vector[zNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['B', 'D', 'C', 'A']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Z', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)
	
	
	def rotatePolygonCOnXZ(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'C')].GetValue())
		vector[1] = int(self.inputs[('Z', 'C')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['C', 'A', 'B', 'D']:
			x = int(self.inputs[('X', pts)].GetValue())
			z = int(self.inputs[('Z', pts)].GetValue())
			coordinates.append([x, z])
		
		for xNum in range(0,4):
			for zNum in range(0,2):
				coordinates[xNum][zNum] -= vector[zNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['C', 'A', 'B', 'D']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Z', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)

		
	def rotatePolygonDOnXZ(self, event):
	
		if hasattr(self.app.selected_object.source, 'D'):
			vector = [0,0]
			vector[0] = int(self.inputs[('X', 'D')].GetValue())
			vector[1] = int(self.inputs[('Z', 'D')].GetValue())
			
			coordinates = [];

			#copy to new list
			for pts in ['D', 'C', 'A', 'B']:
				x = int(self.inputs[('X', pts)].GetValue())
				z = int(self.inputs[('Z', pts)].GetValue())
				coordinates.append([x, z])
			
			for xNum in range(0,4):
				for zNum in range(0,2):
					coordinates[xNum][zNum] -= vector[zNum]
		
				tempvar = coordinates[xNum][0]
				coordinates[xNum][0] = coordinates[xNum][1]
				coordinates[xNum][1] = tempvar * -1

				coordinates[xNum][0] += vector[0]
				coordinates[xNum][1] += vector[1]
			
			count = 0
			
			for pts in ['D', 'C', 'A', 'B']:
				self.inputs['X', pts].SetValue(str(coordinates[count][0]))
				self.inputs['Z', pts].SetValue(str(coordinates[count][1]))
			
				count += 1
			self.to_data(None)	

	def rotatePolygonAOnXY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'A')].GetValue())
		vector[1] = int(self.inputs[('Y', 'A')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['A', 'B', 'D', 'C']:
			x = int(self.inputs[('X', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([x, y])
		
		for xNum in range(0,4):
			for yNum in range(0,2):
				coordinates[xNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['A', 'B', 'D', 'C']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)	

	def rotatePolygonBOnXY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'B')].GetValue())
		vector[1] = int(self.inputs[('Y', 'B')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['B', 'D', 'C', 'A']:
			x = int(self.inputs[('X', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([x, y])
		
		for xNum in range(0,4):
			for yNum in range(0,2):
				coordinates[xNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['B', 'D', 'C', 'A']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)

	def rotatePolygonCOnXY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('X', 'C')].GetValue())
		vector[1] = int(self.inputs[('Y', 'C')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['C', 'A', 'B', 'D']:
			x = int(self.inputs[('X', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([x, y])
		
		for xNum in range(0,4):
			for yNum in range(0,2):
				coordinates[xNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[xNum][0]
			coordinates[xNum][0] = coordinates[xNum][1]
			coordinates[xNum][1] = tempvar * -1

			coordinates[xNum][0] += vector[0]
			coordinates[xNum][1] += vector[1]
		
		count = 0
		
		for pts in ['C', 'A', 'B', 'D']:
			self.inputs['X', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)

		
	def rotatePolygonDOnXY(self, event):
	
		if hasattr(self.app.selected_object.source, 'D'):
			vector = [0,0]
			vector[0] = int(self.inputs[('X', 'D')].GetValue())
			vector[1] = int(self.inputs[('Y', 'D')].GetValue())
			
			coordinates = [];

			#copy to new list
			for pts in ['D', 'C', 'A', 'B']:
				x = int(self.inputs[('X', pts)].GetValue())
				y = int(self.inputs[('Y', pts)].GetValue())
				coordinates.append([x, y])
			
			for xNum in range(0,4):
				for yNum in range(0,2):
					coordinates[xNum][yNum] -= vector[yNum]
		
				tempvar = coordinates[xNum][0]
				coordinates[xNum][0] = coordinates[xNum][1]
				coordinates[xNum][1] = tempvar * -1

				coordinates[xNum][0] += vector[0]
				coordinates[xNum][1] += vector[1]
			
			count = 0
			
			for pts in ['D', 'C', 'A', 'B']:
				self.inputs['X', pts].SetValue(str(coordinates[count][0]))
				self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
			
				count += 1
			self.to_data(None)

	def rotatePolygonAOnZY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('Z', 'A')].GetValue())
		vector[1] = int(self.inputs[('Y', 'A')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['A', 'B', 'D', 'C']:
			z = int(self.inputs[('Z', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([z, y])
		
		for zNum in range(0,4):
			for yNum in range(0,2):
				coordinates[zNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[zNum][0]
			coordinates[zNum][0] = coordinates[zNum][1]
			coordinates[zNum][1] = tempvar * -1

			coordinates[zNum][0] += vector[0]
			coordinates[zNum][1] += vector[1]
		
		count = 0
		
		for pts in ['A', 'B', 'D', 'C']:
			self.inputs['Z', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)	

	def rotatePolygonBOnZY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('Z', 'B')].GetValue())
		vector[1] = int(self.inputs[('Y', 'B')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['B', 'D', 'C', 'A']:
			z = int(self.inputs[('Z', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([z, y])
		
		for zNum in range(0,4):
			for yNum in range(0,2):
				coordinates[zNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[zNum][0]
			coordinates[zNum][0] = coordinates[zNum][1]
			coordinates[zNum][1] = tempvar * -1

			coordinates[zNum][0] += vector[0]
			coordinates[zNum][1] += vector[1]
		
		count = 0
		
		for pts in ['B', 'D', 'C', 'A']:
			self.inputs['Z', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)

	def rotatePolygonCOnZY(self, event):
	
		vector = [0,0]
		vector[0] = int(self.inputs[('Z', 'C')].GetValue())
		vector[1] = int(self.inputs[('Y', 'C')].GetValue())
		
		coordinates = [];

		#copy to new list
		for pts in ['C', 'A', 'B', 'D']:
			z = int(self.inputs[('Z', pts)].GetValue())
			y = int(self.inputs[('Y', pts)].GetValue())
			coordinates.append([z, y])
		
		for zNum in range(0,4):
			for yNum in range(0,2):
				coordinates[zNum][yNum] -= vector[yNum]
	
			tempvar = coordinates[zNum][0]
			coordinates[zNum][0] = coordinates[zNum][1]
			coordinates[zNum][1] = tempvar * -1

			coordinates[zNum][0] += vector[0]
			coordinates[zNum][1] += vector[1]
		
		count = 0
		
		for pts in ['C', 'A', 'B', 'D']:
			self.inputs['Z', pts].SetValue(str(coordinates[count][0]))
			self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
		
			count += 1
		self.to_data(None)

		
	def rotatePolygonDOnZY(self, event):
	
		if hasattr(self.app.selected_object.source, 'D'):
			vector = [0,0]
			vector[0] = int(self.inputs[('Z', 'D')].GetValue())
			vector[1] = int(self.inputs[('Y', 'D')].GetValue())
			
			coordinates = [];

			#copy to new list
			for pts in ['D', 'C', 'A', 'B']:
				z = int(self.inputs[('Z', pts)].GetValue())
				y = int(self.inputs[('Y', pts)].GetValue())
				coordinates.append([z, y])
			
			for zNum in range(0,4):
				for yNum in range(0,2):
					coordinates[zNum][yNum] -= vector[yNum]
		
				tempvar = coordinates[zNum][0]
				coordinates[zNum][0] = coordinates[zNum][1]
				coordinates[zNum][1] = tempvar * -1

				coordinates[zNum][0] += vector[0]
				coordinates[zNum][1] += vector[1]
			
			count = 0
			
			for pts in ['D', 'C', 'A', 'B']:
				self.inputs['Z', pts].SetValue(str(coordinates[count][0]))
				self.inputs['Y', pts].SetValue(str(coordinates[count][1]))
			
				count += 1
			self.to_data(None)

	def from_data(self, polygon):
		for dim in ['X', 'Y', 'Z']:
			for pt in ['A', 'B', 'C', 'D']:
				if not hasattr(polygon.source, pt):
					self.inputs[(dim, pt)].SetValue('0')
					self.inputs[(dim, pt)].Disable()
					continue
				point = getattr(polygon.source, pt).point
				self.inputs[(dim, pt)].Enable()
				if dim == 'Y':
					self.inputs[(dim, pt)].SetValue(str(0 - getattr(point, dim)))
				else:
					self.inputs[(dim, pt)].SetValue(str(getattr(point, dim)))
		for pt in ['A', 'B', 'C', 'D']:
			if not hasattr(polygon.source, pt) or getattr(polygon.source, pt).normal is None:
				self.inputs[('nE', pt)].SetValue('0')
				self.inputs[('nE', pt)].Disable()
				self.inputs[('nA', pt)].SetValue('0')
				self.inputs[('nA', pt)].Disable()
				continue
			normal = getattr(polygon.source, pt).normal
			(elevation, azimuth) = vector_to_sphere(*normal.coords)
			self.inputs[('nE', pt)].Enable()
			self.inputs[('nE', pt)].SetValue(str(90 - elevation))
			self.inputs[('nA', pt)].Enable()
			self.inputs[('nA', pt)].SetValue(str(azimuth))
		for dim in ['U', 'V']:
			for pt in ['A', 'B', 'C', 'D']:
				if not hasattr(polygon.source, pt):
					self.inputs[(dim, pt)].SetValue('0')
					self.inputs[(dim, pt)].Disable()
					continue
				texcoord = getattr(polygon.source, pt).texcoord
				if not hasattr(texcoord, dim):
					self.inputs[(dim, pt)].SetValue('0')
					self.inputs[(dim, pt)].Disable()
					continue
				self.inputs[(dim, pt)].Enable()
				self.inputs[(dim, pt)].SetValue(str(getattr(texcoord, dim)))
		if polygon.source.texture_page is not None:
			self.inputs['page'].Enable()
			self.inputs['page'].SetValue(str(polygon.source.texture_page))
			self.button_guess_normal.Enable()
			self.button_show_uv.Enable()
		else:
			self.inputs['page'].SetValue('0')
			self.inputs['page'].Disable()
			self.button_guess_normal.Disable()
			self.button_show_uv.Disable()
		if polygon.source.texture_palette is not None:
			self.inputs['palette'].Enable()
			self.inputs['palette'].SetValue(str(polygon.source.texture_palette))
		else:
			self.inputs['palette'].SetValue('0')
			self.inputs['palette'].Disable()
		if polygon.source.terrain_coords is not None:
			self.inputs['tX'].Enable()
			self.inputs['tZ'].Enable()
			self.inputs['tlvl'].Enable()
			if polygon.source.terrain_coords[0] == 255 and polygon.source.terrain_coords[1] == 127:
				self.inputs['tX'].SetValue('')
				self.inputs['tZ'].SetValue('')
				self.inputs['tlvl'].SetValue('')
			else:
				self.inputs['tX'].SetValue(str(polygon.source.terrain_coords[0]))
				self.inputs['tZ'].SetValue(str(polygon.source.terrain_coords[1]))
				self.inputs['tlvl'].SetValue(str(polygon.source.terrain_coords[2]))
		else:
			self.inputs['tX'].SetValue('0')
			self.inputs['tX'].Disable()
			self.inputs['tZ'].SetValue('0')
			self.inputs['tZ'].Disable()
			self.inputs['tlvl'].SetValue('0')
			self.inputs['tlvl'].Disable()
		#if polygon.source.texture_palette is not None:
		#	self.inputs['unknown1'].SetValue(str(polygon.source.unknown1))
		#	self.inputs['unknown2'].SetValue(str(polygon.source.unknown2))
		#	self.inputs['unknown3'].SetValue(str(polygon.source.unknown3))
		#	self.inputs['unknown4'].SetValue(str(polygon.source.unknown4))
		#else:
		#	self.inputs['unknown5'].SetValue(str(polygon.source.unknown5))
		for bit, label in visibility_bits:
			if bit is not None:
				self.inputs[('visibility', bit)].SetValue(bool(polygon.source.visible_angles[bit]))
		self.app.uv_edit_window.from_data()

	def to_data(self, foo):
		for dim in ['X', 'Y', 'Z']:
			for pt in ['A', 'B', 'C', 'D']:
				if hasattr(self.app.selected_object.source, pt):
					point = getattr(self.app.selected_object.source, pt).point
					if dim == 'Y':
						setattr(point, dim, 0 - int(self.inputs[(dim, pt)].GetValue()))
					else:
						setattr(point, dim, int(self.inputs[(dim, pt)].GetValue()))
					setattr(point, 'coords', (point.X, point.Y, point.Z))
		for pt in ['A', 'B', 'C', 'D']:
			if not hasattr(self.app.selected_object.source, pt):
				continue
			normal = getattr(self.app.selected_object.source, pt).normal
			if normal is None:
				continue
			elevation = 90 - float(self.inputs[('nE', pt)].GetValue())
			azimuth = float(self.inputs[('nA', pt)].GetValue())
			(nX, nY, nZ) = sphere_to_vector(elevation, azimuth)
			normal.X = nX
			normal.Y = nY
			normal.Z = nZ
			normal.coords = (normal.X, normal.Y, normal.Z)
		for dim in ['U', 'V']:
			for pt in ['A', 'B', 'C', 'D']:
				if not hasattr(self.app.selected_object.source, pt):
					continue
				texcoord = getattr(self.app.selected_object.source, pt).texcoord
				if not hasattr(texcoord, dim):
					continue
				newVal = int(self.inputs[(dim, pt)].GetValue())
				if newVal < 0:
					newVal = 0
					print("UV Warning: UV values cannot be below 0 (ubyte)")
				elif newVal > 255:
					newVal = 255
					print("UV Warning: UV values cannot be above 255 (ubyte)")
				setattr(texcoord, dim, newVal)
				setattr(texcoord, 'coords', (texcoord.U, texcoord.V))
		if self.app.selected_object.source.texture_page is not None:
			self.app.selected_object.source.texture_page = int(self.inputs['page'].GetValue())
		if self.app.selected_object.source.texture_palette is not None:
			self.app.selected_object.source.texture_palette = int(self.inputs['palette'].GetValue())
		if self.app.selected_object.source.terrain_coords is not None:
			if self.inputs['tX'].GetValue() == '' or self.inputs['tZ'].GetValue() == '':
				terrain_coords = (255, 127, 0)
			else:
				terrain_coords = (int(self.inputs['tX'].GetValue()), int(self.inputs['tZ'].GetValue()), int(self.inputs['tlvl'].GetValue()))
			self.app.selected_object.source.terrain_coords = terrain_coords
		for bit, label in visibility_bits:
			if bit is not None:
				self.app.selected_object.source.visible_angles[bit] = 1 if self.inputs[('visibility', bit)].GetValue() else 0
		#self.app.selected_object.source.unknown1 = int(self.inputs['unknown1'].GetValue())
		#self.app.selected_object.source.unknown2 = int(self.inputs['unknown2'].GetValue())
		#self.app.selected_object.source.unknown3 = int(self.inputs['unknown3'].GetValue())
		#self.app.selected_object.source.unknown4 = int(self.inputs['unknown4'].GetValue())
		# TODO: Should probably go somewhere else
		tag = self.app.selected_object.node_path.getTag('polygon_i')
		self.app.selected_object.init_node_path()
		self.app.selected_object.node_path.setTag('polygon_i', tag)
		self.app.selected_object.select()
		self.app.uv_edit_window.from_data()


class UVEditWindow(DirectObject):
	def __init__(self, parent):
		self.app = parent
		self.uv_window = None
		self.node_path_texture = None
		self.node_path_uv_polygon = None
		self.mwn = None
		self.zoom_level = 1
		self.render_uv = None
		self.selected_object = None
		self.mouse_old_pos = None

	def init_collide(self):
		from pandac.PandaModules import CollisionTraverser, CollisionNode, GeomNode
		from pandac.PandaModules import CollisionHandlerQueue, CollisionRay
		self.cTrav = CollisionTraverser('MousePointer')
		self.cQueue = CollisionHandlerQueue()
		self.cNode = CollisionNode('MousePointer')
		self.cNodePath = self.camera.attachNewNode(self.cNode)
		self.cNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
		self.cRay = CollisionRay()
		self.cNode.addSolid(self.cRay)
		self.cTrav.addCollider(self.cNodePath, self.cQueue)

	def find_object(self):
		if self.render_uv:
			pos = self.mwn.getMouse()
			self.cRay.setFromLens(self.camera.node(), pos.getX(), pos.getY())
			self.cTrav.traverse(self.render_uv)
			if self.cQueue.getNumEntries() > 0:
				self.cQueue.sortEntries()
				return self.cQueue.getEntry(0).getIntoNodePath()
		return None

	def make_properties(self):
		wp = WindowProperties.getDefault()
		wp.setTitle('UV Coordinates')
		wp.setSize(512, 512)
		return wp

	def open(self):
		if self.uv_window:
			return False
		from pandac.PandaModules import GraphicsPipe, FrameBufferProperties, WindowProperties, MouseAndKeyboard, MouseWatcher, ButtonThrower
		fp = FrameBufferProperties.getDefault()
		wp = self.make_properties()
		self.uv_window = base.graphicsEngine.makeOutput(base.pipe, 'UV Coordinates', 2, fp, wp, GraphicsPipe.BFRequireWindow)
		self.uv_window.setCloseRequestEvent('uv_edit_window_closed')
		self.dr = self.uv_window.makeDisplayRegion()
		from pandac.PandaModules import NodePath, Camera, OrthographicLens
		self.render_uv = NodePath('render_uv')
		self.camera = self.render_uv.attachNewNode(Camera('camera_uv'))
		self.dr.setCamera(self.camera)
		self.camera.setPos(0, 0, 1)
		self.camera.lookAt(0,0,0)
		lens = OrthographicLens()
		lens.setAspectRatio(1.0)
		lens.setNear(-10)
		lens.setFar(10)
		lens.setFilmSize(512)
		self.camera.node().setLens(lens)
		self.zoom_level = 1
		wp = self.make_properties()
		wp.setOpen(True)
		self.uv_window.requestProperties(wp)
		self.init_collide()
		self.draw_texture()
		self.draw_uv_polygon()
		# Set up mouse
		dev_kbd_mouse = self.uv_window.getInputDeviceNames().index('keyboard_mouse')
		self.mak = MouseAndKeyboard(self.uv_window, dev_kbd_mouse, 'keyboard_mouse')
		self.mak = base.dataRoot.attachNewNode(self.mak)
		self.mw = self.mak.attachNewNode(MouseWatcher('keyboard_mouse'))
		self.mwn = self.mw.node()
		self.bt = self.mw.attachNewNode(ButtonThrower('keyboard_mouse'))

	def close(self):
		if self.uv_window:
			base.graphicsEngine.removeWindow(self.uv_window)
			self.uv_window = None

	def has_mouse(self):
		return self.mwn and self.mwn.hasMouse()

	def on_mouse1(self):
		found = self.find_object()
		if found:
			page = found.getTag('texture_page')
			point = found.getTag('point')
			polygon = found.getTag('whole_polygon')
			if page:
				self.app.polygon_edit_window.inputs['page'].SetValue(str(page))
				self.draw_uv_polygon()
				pass
			elif point or polygon:
				self.selected_object = found

	def on_mouse1_up(self):
		self.mouse_old_pos = None
		if self.selected_object:
			self.selected_object = None

	def mouse_task(self, task):
		if self.has_mouse() and self.selected_object:
			self.drag()
		return task.cont

	def drag(self):
		def mouse_to_window(page, x, y):
			x = 128 + int(128 * x)
			y = 128 + int(128 * y)
			if page < 2:
				win_x = -256
			else:
				win_x = 0
			if page % 2 == 0:
				win_y = 0
			else:
				win_y = -256
			win_x += x
			win_y += y
			return (win_x, win_y)
		def window_to_uv(page, x, y):
			if page < 2:
				u = 256
			else:
				u = 0
			if page % 2 == 0:
				v = 256
			else:
				v = 0
			u += x
			v -= y
			return (u, v)
		if self.zoom_level == 2:
			inputs = self.app.polygon_edit_window.inputs
			page = int(inputs['page'].GetValue())
			pos = self.mwn.getMouse()
			x = min(max(pos.getX(), -1.0), 1.0)
			y = min(max(pos.getY(), -1.0), 1.0)
			(x, y) = mouse_to_window(page, x, y)
			(u, v) = window_to_uv(page, x, y)
			if not self.mouse_old_pos:
				self.mouse_old_pos = (u, v)
			point = self.selected_object.getTag('point')
			polygon = self.selected_object.getTag('whole_polygon')
			if point:
				inputs[('U', point)].SetValue(str(u))
				inputs[('V', point)].SetValue(str(v))
			elif polygon:
				dU = u - self.mouse_old_pos[0]
				dV = v - self.mouse_old_pos[1]
				for point in ['A', 'B', 'C', 'D']:
					if not hasattr(self.app.selected_object.source, point):
						continue
					old_u = int(inputs[('U', point)].GetValue())
					old_v = int(inputs[('V', point)].GetValue())
					inputs[('U', point)].SetValue(str(old_u + dU))
					inputs[('V', point)].SetValue(str(old_v + dV))
				self.mouse_old_pos = (u, v)
			self.draw_uv_polygon()

	def on_close(self):
		self.close()

	def draw_texture(self):
		from pandac.PandaModules import Geom, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTristrips, GeomNode
		if self.node_path_uv_polygon is not None:
			self.node_path_uv_polygon.removeNode()
		self.node_path_texture = self.render_uv.attachNewNode('node_path_texture')
		for page in range(4):
			if page < 2:
				x = -256
			else:
				x = 0
			if page % 2 == 0:
				y = 256
			else:
				y = 0
			vdata = GeomVertexData('texture_page_%u' % page, GeomVertexFormat.getV3c4t2(), Geom.UHStatic)
			vertex = GeomVertexWriter(vdata, 'vertex')
			color = GeomVertexWriter(vdata, 'color')
			texcoord = GeomVertexWriter(vdata, 'texcoord')
			geom = Geom(vdata)
			primitive = GeomTristrips(Geom.UHStatic)
			vertex.addData3f(x, y, 0)
			vertex.addData3f(x+256, y, 0)
			vertex.addData3f(x, y-256, 0)
			vertex.addData3f(x+256, y-256, 0)
			color.addData4f(1.0, 1.0, 1.0, 1.0)
			color.addData4f(1.0, 1.0, 1.0, 1.0)
			color.addData4f(1.0, 1.0, 1.0, 1.0)
			color.addData4f(1.0, 1.0, 1.0, 1.0)
			texcoord.addData2f(0, 1 - 0.25 * page)
			texcoord.addData2f(1, 1 - 0.25 * page)
			texcoord.addData2f(0, 0.75 - 0.25 * page)
			texcoord.addData2f(1, 0.75 - 0.25 * page)
			primitive.addNextVertices(4)
			primitive.closePrimitive()
			geom.addPrimitive(primitive)
			node = GeomNode('gnode_%u' % page)
			node.addGeom(geom)
			node_path = self.node_path_texture.attachNewNode(node)
			node_path.setTag('texture_page', str(page))

		self.node_path_texture.setTexture(self.app.world.texture.texture2)

	def draw_uv_polygon(self):
		def uv_to_window(page, u, v):
			if page < 2:
				x = -256
			else:
				x = 0
			if page % 2 == 0:
				y = 256
			else:
				y = 0
			x = x + u
			y = y - v
			return (x, y, 1)
		from pandac.PandaModules import NodePath, Geom, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomLinestrips, GeomNode, GeomTristrips, TransparencyAttrib
		if self.node_path_uv_polygon is not None:
			self.node_path_uv_polygon.removeNode()
		self.node_path_uv_polygon = self.render_uv.attachNewNode('node_path_uv_polygon')
		polygon = self.app.selected_object.source
		if polygon.A.texcoord is None:
			return False
		# Draw wireframe polygon
		vdata = GeomVertexData('name_me', GeomVertexFormat.getV3c4(), Geom.UHStatic)
		vertex = GeomVertexWriter(vdata, 'vertex')
		color = GeomVertexWriter(vdata, 'color')
		primitive = GeomLinestrips(Geom.UHStatic)
		inputs = self.app.polygon_edit_window.inputs
		page = int(inputs['page'].GetValue())
		A = [int(inputs[('U', 'A')].GetValue()), int(inputs[('V', 'A')].GetValue())]
		B = [int(inputs[('U', 'B')].GetValue()), int(inputs[('V', 'B')].GetValue())]
		C = [int(inputs[('U', 'C')].GetValue()), int(inputs[('V', 'C')].GetValue())]
		if hasattr(polygon, 'D'):
			D = [int(inputs[('U', 'D')].GetValue()), int(inputs[('V', 'D')].GetValue())]
		vertex.addData3f(*uv_to_window(page, A[0], A[1]))
		vertex.addData3f(*uv_to_window(page, B[0], B[1]))
		if hasattr(polygon, 'D'):
			vertex.addData3f(*uv_to_window(page, D[0], D[1]))
		vertex.addData3f(*uv_to_window(page, C[0], C[1]))
		vertex.addData3f(*uv_to_window(page, A[0], A[1]))
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		if hasattr(polygon, 'D'):
			color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		if hasattr(polygon, 'D'):
			primitive.addNextVertices(5)
		else:
			primitive.addNextVertices(4)
		primitive.closePrimitive()
		geom = Geom(vdata)
		geom.addPrimitive(primitive)
		node = GeomNode('gnode')
		node.addGeom(geom)
		self.node_path_uv_polygon.attachNewNode(node)
		# Draw solid, partially-transparent polygon
		vdata = GeomVertexData('name_me', GeomVertexFormat.getV3c4(), Geom.UHStatic)
		vertex = GeomVertexWriter(vdata, 'vertex')
		color = GeomVertexWriter(vdata, 'color')
		primitive = GeomTristrips(Geom.UHStatic)
		inputs = self.app.polygon_edit_window.inputs
		page = int(inputs['page'].GetValue())
		A = [int(inputs[('U', 'A')].GetValue()), int(inputs[('V', 'A')].GetValue())]
		B = [int(inputs[('U', 'B')].GetValue()), int(inputs[('V', 'B')].GetValue())]
		C = [int(inputs[('U', 'C')].GetValue()), int(inputs[('V', 'C')].GetValue())]
		if hasattr(polygon, 'D'):
			D = [int(inputs[('U', 'D')].GetValue()), int(inputs[('V', 'D')].GetValue())]
		vertex.addData3f(*uv_to_window(page, A[0], A[1]))
		vertex.addData3f(*uv_to_window(page, B[0], B[1]))
		if hasattr(polygon, 'D'):
			vertex.addData3f(*uv_to_window(page, D[0], D[1]))
		vertex.addData3f(*uv_to_window(page, C[0], C[1]))
		vertex.addData3f(*uv_to_window(page, A[0], A[1]))
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		if hasattr(polygon, 'D'):
			color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		color.addData4f(1.0, 0.0, 1.0, 1.0)
		if hasattr(polygon, 'D'):
			primitive.addNextVertices(5)
		else:
			primitive.addNextVertices(4)
		primitive.closePrimitive()
		geom = Geom(vdata)
		geom.addPrimitive(primitive)
		node = GeomNode('gnode_poly')
		node.addGeom(geom)
		trans_poly = self.node_path_uv_polygon.attachNewNode(node)
		trans_poly.setTransparency(TransparencyAttrib.MAlpha)
		trans_poly.setAlphaScale(0.1)
		trans_poly.setTag('whole_polygon', 'whole_polygon')
		# Draw points
		self.render_uv.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
		for point in ['A', 'B', 'C', 'D']:
			if not hasattr(polygon, point):
				continue
			vdata = GeomVertexData('name_me', GeomVertexFormat.getV3c4(), Geom.UHStatic)
			vertex = GeomVertexWriter(vdata, 'vertex')
			color = GeomVertexWriter(vdata, 'color')
			primitive = GeomTristrips(Geom.UHStatic)
			vertex.addData3f(0, 2, -2)
			vertex.addData3f(2, 0, -2)
			vertex.addData3f(0, -2, -2)
			vertex.addData3f(-2, 0, -2)
			vertex.addData3f(0, 2, -2)
			if point == 'A':
				color_tuple = (1.0, 0.0, 0.0)
			elif point == 'B':
				color_tuple = (0.0, 1.0, 0.0)
			elif point == 'C':
				color_tuple = (0.0, 0.0, 1.0)
			elif point == 'D':
				color_tuple = (1.0, 1.0, 0.0)
			color.addData4f(*color_tuple + (1.0,))
			color.addData4f(*color_tuple + (1.0,))
			color.addData4f(*color_tuple + (1.0,))
			color.addData4f(*color_tuple + (1.0,))
			color.addData4f(*color_tuple + (1.0,))
			primitive.addNextVertices(5)
			primitive.closePrimitive()
			geom = Geom(vdata)
			geom.addPrimitive(primitive)
			node = GeomNode('gnode_%s' % point)
			node.addGeom(geom)
			node_path = self.node_path_uv_polygon.attachNewNode(node)
			node_path.setP(180)
			node_path.setPos(*uv_to_window(page, *locals()[point]))
			node_path.setTag('point', point)

	def from_data(self):
		if self.uv_window:
			self.draw_uv_polygon()

	def zoom_in(self):
		if self.zoom_level == 1:
			page = int(self.app.polygon_edit_window.inputs['page'].GetValue())
			if page < 2:
				x = -128
			else:
				x = 128
			if page % 2 == 0:
				y = 128
			else:
				y = -128
			lens = self.camera.node().getLens()
			self.camera.setPos(x, y, 1)
			lens.setFilmSize(256)
			self.zoom_level = 2

	def zoom_out(self):
		if self.zoom_level == 2:
			lens = self.camera.node().getLens()
			self.camera.setPos(0, 0, 1)
			lens.setFilmSize(512)
			self.zoom_level = 1


class SettingsWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		text = ("[: Previous state\t]: Next State\n\n"+
		"n: Next map\t\tt: Next terrain mode\n\n" +
		"s: Save\t\t\to: Output texture\n\n" +
		"i: Import Texture\tp: Edit palette\n\n" +
		"l: Edit lighting\t\t+: Add polygon\n\n" +
		"d: Edit terrain dimensions\n\n" +
		"f: Copy selected polygon (Only singularly selected Polygons)\n\n" +
		"u: Move all polygons\n\n" +
		"Holding CTRL: Allows selection of multiple polygons\non which you can perform the following on:\n\n" +
		"q: Decrease Y (12)\te: Increase Y (12)\n\n" +
		"Up: Increase X (28)\tDown: Decrease X (28)\n\n" +
		"Left: Increase Z (28)\tRight: Decrease Z (28)\n\n" +
		"del: Delete selected polygons (Warning: No confirmation menu given)")
		text_label = wx.StaticText(panel, wx.ID_ANY, text)
		textArea = wx.BoxSizer(wx.HORIZONTAL)
		textArea.Add(text_label)
		sizer_sections.Add(textArea, flag=wx.ALL, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_close(self, event):
		self.Show(False)

			
class MoveAllPolygonsEditWindow(wx.Frame):			
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
				
		for i, data in enumerate(['X', 'Y', 'Z']):
			sizer_movementbuttons = wx.BoxSizer(wx.HORIZONTAL)
		
			data_label = wx.StaticText(panel, wx.ID_ANY, data, size=wx.Size(20, -1))
			sizer_movementbuttons.Add(data_label)
			
			if data == 'X':
				button = wx.Button(panel, POLYGON_MOVE_ID + 0, '-28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			elif data == 'Y':
				button = wx.Button(panel, POLYGON_MOVE_ID + 2, '-12', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			elif data == 'Z':
				button = wx.Button(panel, POLYGON_MOVE_ID + 4, '-28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			else:
				button = wx.StaticText(panel, wx.ID_ANY, '')
			sizer_movementbuttons.Add(button)

			if data == 'X':
				button = wx.Button(panel, POLYGON_MOVE_ID + 1, '+28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			elif data == 'Y':
				button = wx.Button(panel, POLYGON_MOVE_ID + 3, '+12', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			elif data == 'Z':
				button = wx.Button(panel, POLYGON_MOVE_ID + 5, '+28', size=wx.Size(50, -1))
				button.Bind(wx.EVT_BUTTON, self.move_all)
			else:
				button = wx.StaticText(panel, wx.ID_ANY, '')
			sizer_movementbuttons.Add(button)
			sizer_sections.Add(sizer_movementbuttons, flag=wx.ALL, border=10)
				
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		cancel_button = wx.Button(panel, wx.ID_CANCEL)
		cancel_button.Bind(wx.EVT_BUTTON, self.on_close)
		sizer_buttons.Add(cancel_button)
		sizer_sections.Add(sizer_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)


	def on_close(self, event):
		#self.MakeModal(False)
		self.Show(False)

	def move_all(self, event):

		#find which button was pushed and whether it is positive or negative value
		button_id = event.GetId() - POLYGON_MOVE_ID
		if button_id in [0, 1]:
			dim = 'X'
			amount = 28
		elif button_id in [2, 3]:
			dim = 'Y'
			amount = 12
		elif button_id in [4, 5]:
			dim = 'Z'
			amount = 28
		if button_id % 2 == 0:
			sign = -1
		else:
			sign = 1
				

		self.app.world.move_all_poly(dim,amount,sign)	

	

class TerrainDimensionsEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		# Prompt
		prompt = wx.StaticText(panel, wx.ID_ANY, 'Set terrain dimensions to:')
		sizer_sections.Add(prompt, flag=wx.ALL, border=10)
		# Options
		sizer_options = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(panel, wx.ID_ANY, 'X')
		sizer_options.Add(label)
		self.input_x = wx.TextCtrl(panel, wx.ID_ANY)
		sizer_options.Add(self.input_x)
		label = wx.StaticText(panel, wx.ID_ANY, 'Z')
		sizer_options.Add(label)
		self.input_z = wx.TextCtrl(panel, wx.ID_ANY)
		sizer_options.Add(self.input_z)
		sizer_sections.Add(sizer_options, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Buttons
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		ok_button = wx.Button(panel, wx.ID_OK)
		ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
		sizer_buttons.Add(ok_button)
		cancel_button = wx.Button(panel, wx.ID_CANCEL)
		cancel_button.Bind(wx.EVT_BUTTON, self.on_close)
		sizer_buttons.Add(cancel_button)
		sizer_sections.Add(sizer_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_ok(self, event):
		new_x = int(self.input_x.GetValue())
		new_z = int(self.input_z.GetValue())
		if (new_x == 0 or new_z == 0):
			print("Terrain Dimension Warning: X and Z can't be equal to 0 (nonexistant size).")
		elif (new_x == 256 or new_z == 256):
			print("Terrain Dimension Warning: X and Z can't be equal to 256 (ubyte range 0-255).")
		elif (new_x * new_z > 256):
			print("Terrain Dimension Warning: (X*Z) cannot be greater than 256. (256 tile maximum for maps)")
		else:
			self.app.world.resize_terrain(new_x, new_z)
			self.on_close(None)

	def on_close(self, event):
		self.MakeModal(False)
		self.Show(False)

	def from_data(self, terrain):
		z = len(terrain.tiles[0])
		x = len(terrain.tiles[0][0])
		self.input_x.SetValue(str(x))
		self.input_z.SetValue(str(z))


class TerrainEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		sizer_main_table = wx.FlexGridSizer(rows=8, cols=3)
		self.inputs = {}
		# Headings
		label = wx.StaticText(panel, wx.ID_ANY, '')
		sizer_main_table.Add(label)
		label = wx.StaticText(panel, wx.ID_ANY, 'Level 0')
		sizer_main_table.Add(label)
		label = wx.StaticText(panel, wx.ID_ANY, 'Level 1')
		sizer_main_table.Add(label)
		# Coordinates
		label = wx.StaticText(panel, wx.ID_ANY, 'Coords (X,Z)')
		sizer_main_table.Add(label)
		self.coords0_label = wx.StaticText(panel, wx.ID_ANY, '(0,0)')
		sizer_main_table.Add(self.coords0_label)
		self.coords1_label = wx.StaticText(panel, wx.ID_ANY, '(0,0)')
		sizer_main_table.Add(self.coords1_label)
		# Height
		label = wx.StaticText(panel, wx.ID_ANY, 'Height')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 1)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'height')] = data_input
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 2)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'height')] = data_input
		# Depth
		label = wx.StaticText(panel, wx.ID_ANY, 'Depth')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 3)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'depth')] = data_input
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 4)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'depth')] = data_input
		# Slope
		label = wx.StaticText(panel, wx.ID_ANY, 'Slope')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 5)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'slope_height')] = data_input
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 6)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'slope_height')] = data_input
		# Slope Type
		label = wx.StaticText(panel, wx.ID_ANY, 'Slope Type')
		sizer_main_table.Add(label)
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 7, choices=slope_type_names)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'slope_type')] = data_input
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 8, choices=slope_type_names)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'slope_type')] = data_input
		# Surface
		label = wx.StaticText(panel, wx.ID_ANY, 'Surface')
		sizer_main_table.Add(label)
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 9, choices=surface_types.values())
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'surface_type')] = data_input
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 10, choices=surface_types.values())
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'surface_type')] = data_input
		# Impassable
		label = wx.StaticText(panel, wx.ID_ANY, 'Impassable')
		sizer_main_table.Add(label)
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 11)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'cant_walk')] = data_input
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 12)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'cant_walk')] = data_input
		# Unselectable
		label = wx.StaticText(panel, wx.ID_ANY, 'Unselectable')
		sizer_main_table.Add(label)
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 13)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'cant_cursor')] = data_input
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 14)
		sizer_main_table.Add(data_input)
		self.inputs[(1, 'cant_cursor')] = data_input
		# Find polygon and select it
		label = wx.StaticText(panel, wx.ID_ANY, '')
		sizer_main_table.Add(label)
		button = wx.Button(panel, wx.ID_ANY, 'Find Polygon')
		button.Bind(wx.EVT_BUTTON, self.on_find_polygon0)
		sizer_main_table.Add(button)
		button = wx.Button(panel, wx.ID_ANY, 'Find Polygon')
		button.Bind(wx.EVT_BUTTON, self.on_find_polygon1)
		sizer_main_table.Add(button)
		sizer_sections.Add(sizer_main_table, flag=wx.ALL, border=10)
		# Buttons
		apply_button = wx.Button(panel, wx.ID_APPLY)
		apply_button.Bind(wx.EVT_BUTTON, self.to_data)
		sizer_sections.Add(apply_button, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_close(self, event):
		self.Show(False)

	def on_find_polygon0(self, event):
		self.app.find_polygon(0)

	def on_find_polygon1(self, event):
		self.app.find_polygon(1)

	def clear_inputs(self):
		#print 'clearing'
		pass

	def from_data(self, clicked_tile):
		(x, z) = (clicked_tile.x, clicked_tile.z)
		tiles = []
		tiles.append(self.app.world.terrain.tiles[0][z][x])
		tiles.append(self.app.world.terrain.tiles[1][z][x])
		for i, tile in enumerate(tiles):
			self.coords0_label.SetLabel('(%u,%u)' % (x, z))
			self.coords1_label.SetLabel('(%u,%u)' % (x, z))
			slope_type_id = None
			for j, slope_type in enumerate(slope_types):
				if slope_type[0] == tile.slope_type:
					slope_type_id = j
					break
			self.inputs[(i, 'height')].SetValue(str(tile.height))
			self.inputs[(i, 'depth')].SetValue(str(tile.depth))
			self.inputs[(i, 'slope_height')].SetValue(str(tile.slope_height))
			
			if (slope_type_id is None):
				self.inputs[(i, 'slope_type')].SetSelection(0)
			else:
				self.inputs[(i, 'slope_type')].SetSelection(slope_type_id)
			
			
			self.inputs[(i, 'surface_type')].SetSelection(tile.surface_type)
			self.inputs[(i, 'cant_walk')].SetValue(bool(tile.cant_walk))
			self.inputs[(i, 'cant_cursor')].SetValue(bool(tile.cant_cursor))

	def to_data(self, foo):
		selected_tile = self.app.selected_object
		(x, z) = (selected_tile.x, selected_tile.z)
		tiles = []
		tiles.append(self.app.world.terrain.tiles[0][z][x])
		tiles.append(self.app.world.terrain.tiles[1][z][x])
		for i, tile in enumerate(tiles):
			tile.height = int(self.inputs[(i, 'height')].GetValue())
			if(tile.height < 0):
				tile.height = 0
				print("Terrain Warning: Height can't be less than 0.")

			#Info from Xifanie, max height is 63.5?
			elif(tile.height > 63):
				tile.height = 63
				print("Terrain Warning: Height can't be greater than 63.")
			tile.depth = int(self.inputs[(i, 'depth')].GetValue())
			if(tile.depth < 0):
				tile.depth = 0
				print("Terrain Warning: Depth can't be less than 0.")
			#Current max depth game allows is unknown, but ubyte max is 255
			elif(tile.depth > 255):
				tile.depth = 255
				print("Terrain Warning: Depth can't be greater than 255.")
			tile.slope_height = int(self.inputs[(i, 'slope_height')].GetValue())
			if(tile.slope_height < 0):
				tile.slope_height = 0
				print("Terrain Warning: Slope Height can't be less than 0.")
			#Current max slope game allows is unknown, but ubyte max is 255
			elif(tile.slope_height > 255):
				tile.slope_height = 255
				print("Terrain Warning: Slope Height can't be greater than 255.")
			tile.slope_type = slope_types[self.inputs[(i, 'slope_type')].GetCurrentSelection()][0]
			tile.surface_type = self.inputs[(i, 'surface_type')].GetCurrentSelection()
			tile.cant_walk = 1 if self.inputs[(i, 'cant_walk')].GetValue() else 0
			tile.cant_cursor = 1 if self.inputs[(i, 'cant_cursor')].GetValue() else 0
			# TODO: Should probably go somewhere else
			tag = tile.node_path.getTag('tile_xyz')
			tile.init_node_path()
			tile.node_path.setTag('tile_xyz', tag)
			if tile.is_selected:
				tile.select()

class MultiTerrainEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		sizer_main_table = wx.FlexGridSizer(rows=8, cols=2)
		self.inputs = {}
		# Heading
		label = wx.StaticText(panel, wx.ID_ANY, '')
		sizer_main_table.Add(label)
		label = wx.StaticText(panel, wx.ID_ANY, 'Tile')
		sizer_main_table.Add(label)
		# Height
		label = wx.StaticText(panel, wx.ID_ANY, 'Height')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 1)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'height')] = data_input
		# Depth
		label = wx.StaticText(panel, wx.ID_ANY, 'Depth')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 3)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'depth')] = data_input
		# Slope
		label = wx.StaticText(panel, wx.ID_ANY, 'Slope')
		sizer_main_table.Add(label)
		data_input = wx.TextCtrl(panel, TERRAIN_INPUT_ID + 5)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'slope_height')] = data_input
		# Slope Type
		label = wx.StaticText(panel, wx.ID_ANY, 'Slope Type')
		sizer_main_table.Add(label)
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 7, choices=slope_type_names)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'slope_type')] = data_input
		# Surface
		label = wx.StaticText(panel, wx.ID_ANY, 'Surface')
		sizer_main_table.Add(label)
		data_input = wx.Choice(panel, TERRAIN_INPUT_ID + 9, choices=surface_types.values())
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'surface_type')] = data_input
		# Impassable
		label = wx.StaticText(panel, wx.ID_ANY, 'Impassable')
		sizer_main_table.Add(label)
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 11)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'cant_walk')] = data_input
		# Unselectable
		label = wx.StaticText(panel, wx.ID_ANY, 'Unselectable')
		sizer_main_table.Add(label)
		data_input = wx.CheckBox(panel, TERRAIN_INPUT_ID + 13)
		sizer_main_table.Add(data_input)
		self.inputs[(0, 'cant_cursor')] = data_input
		sizer_sections.Add(sizer_main_table, flag=wx.ALL, border=10)
		# Buttons
		apply_button = wx.Button(panel, wx.ID_APPLY)
		apply_button.Bind(wx.EVT_BUTTON, self.to_data)
		sizer_sections.Add(apply_button, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_close(self, event):
		self.Show(False)

	def clear_inputs(self):
		#print 'clearing'
		pass

	def to_data(self, foo):
		for tile in self.app.selected_objects:
			if self.inputs[(0, 'height')].GetValue():
				print("height", self.inputs[(0, 'height')].GetValue())
				tile.height = int(self.inputs[(0, 'height')].GetValue())
				if(tile.height < 0):
					tile.height = 0
					print("Terrain Warning: Height can't be less than 0.")
				#Info from Xifanie, max height is 63.5?
				elif(tile.height > 63):
					tile.height = 63
					print("Terrain Warning: Height can't be greater than 63.")
			if self.inputs[(0, 'depth')].GetValue():
				print("depth", self.inputs[(0, 'depth')].GetValue())
				tile.depth = int(self.inputs[(0, 'depth')].GetValue())
				if(tile.depth < 0):
					tile.depth = 0
					print("Terrain Warning: Depth can't be less than 0.")
				#Current max depth game allows is unknown, but ubyte max is 255
				elif(tile.depth > 255):
					tile.depth = 255
					print("Terrain Warning: Depth can't be greater than 255.")
			if self.inputs[(0, 'slope_height')].GetValue():
				print("slope_height", self.inputs[(0, 'slope_height')].GetValue())
				tile.slope_height = int(self.inputs[(0, 'slope_height')].GetValue())
				if(tile.slope_height < 0):
					tile.slope_height = 0
					print("Terrain Warning: Depth can't be less than 0.")
				#Current max slope_height game allows is unknown, but ubyte max is 255
				elif(tile.slope_height > 255):
					tile.slope_height = 255
					print("Terrain Warning: Depth can't be greater than 255.")
			if self.inputs[(0, 'slope_type')].GetCurrentSelection():
				tile.slope_type = slope_types[self.inputs[(0, 'slope_type')].GetCurrentSelection()][0]
			if self.inputs[(0, 'surface_type')].GetCurrentSelection():
				tile.surface_type = self.inputs[(0, 'surface_type')].GetCurrentSelection()

			tile.cant_walk = 1 if self.inputs[(0, 'cant_walk')].GetValue() else 0
			tile.cant_cursor = 1 if self.inputs[(0, 'cant_cursor')].GetValue() else 0
				
			tag = tile.node_path.getTag('tile_xyz')
			tile.init_node_path()
			tile.node_path.setTag('tile_xyz', tag)
			if tile.is_selected:
				tile.select()





class PaletteEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		# Configure window
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title, wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.palettes = []
		
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		
		# Color buttons grid for all 16 palettes
		sizer_color_table = wx.FlexGridSizer(rows=17, cols=19)
		self.color_buttons = []
		
		# Top row header
		sizer_color_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
		for headerIndex in range(16):
			sizer_color_table.Add(wx.StaticText(panel, wx.ID_ANY,  str(headerIndex)))
		
		sizer_color_table.Add(wx.StaticText(panel, wx.ID_ANY, '  ACT file'))
		sizer_color_table.Add(wx.StaticText(panel, wx.ID_ANY, ''))
			
		#palette rows
		for y in range(16):
			label = wx.StaticText(panel, wx.ID_ANY, str(y), size=wx.Size(20,20))
			sizer_color_table.Add(label)
			for x in range(16):
				button = wx.Window(panel, PALETTE_INPUT_ID + y*16 + x, size=wx.Size(20,20))
				button.Bind(wx.EVT_LEFT_DOWN, self.on_color_button)
				sizer_color_table.Add(button)
				self.color_buttons.append(button)
				
			button = wx.Button(panel, y, 'Import', size=wx.Size(50, -1))
			button.Bind(wx.EVT_BUTTON, self.import_palette)
			sizer_color_table.Add(button)
			
			button = wx.Button(panel, y, 'Export', size=wx.Size(50, -1))
			button.Bind(wx.EVT_BUTTON, self.export_palette)
			sizer_color_table.Add(button)
				
		sizer_sections.Add(sizer_color_table, flag=wx.ALL, border=10)
		
		# Color sliders
		sizer_sliders_preview = wx.BoxSizer(wx.HORIZONTAL)
		sizer_color_sliders = wx.BoxSizer(wx.VERTICAL)
		self.color_sliders = []
		self.color_inputs = []
		
		for i, color in enumerate(['R', 'G', 'B']):
			sizer_slide_input = wx.BoxSizer(wx.HORIZONTAL)
			max_value = 31
			
			color_label = wx.StaticText(panel, wx.ID_ANY, color, size=wx.Size(20, -1))
			sizer_slide_input.Add(color_label, 0)
			
			color_slider = wx.Slider(panel, 5000 + i, 0, 0, max_value, size=wx.Size(290, -1))
			color_slider.Bind(wx.EVT_SCROLL, self.on_color_slide)
			color_slider.Disable()
			sizer_slide_input.Add(color_slider, 0)
			
			color_input = wx.TextCtrl(panel, 6000 + i, size=wx.Size(40, -1))
			color_input.Bind(wx.EVT_TEXT_ENTER, self.on_color_enter)
			color_input.Disable()
			sizer_slide_input.Add(color_input, 0)
			
			janky_padding = wx.StaticText(panel, wx.ID_ANY, '', size=wx.Size(20, -1))
			sizer_slide_input.Add(janky_padding, 0)
			
			sizer_color_sliders.Add(sizer_slide_input)
			self.color_sliders.append(color_slider)
			self.color_inputs.append(color_input)
			
		sizer_sliders_preview.Add(sizer_color_sliders)
		self.preview = wx.Window(panel, wx.ID_ANY, size=wx.Size(70, 70))
		self.preview.SetBackgroundColour(wx.Colour(0, 0, 0))
		sizer_sliders_preview.Add(self.preview)
		sizer_sections.Add(sizer_sliders_preview, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		# Buttons
		bottom_row_buttons = wx.BoxSizer(wx.HORIZONTAL)
		
		apply_button = wx.Button(panel, wx.ID_APPLY)
		apply_button.Bind(wx.EVT_BUTTON, self.to_data)
		bottom_row_buttons.Add(apply_button)
		
		export_default_palette_button = wx.Button(panel, wx.ID_ANY, 'Export Default palette')
		export_default_palette_button.Bind(wx.EVT_BUTTON, self.export_default_palette)
		bottom_row_buttons.Add(export_default_palette_button)
		
		sizer_sections.Add(bottom_row_buttons, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(self)
		sizer_sections.SetSizeHints(panel)

	def on_close(self, event):
		self.Show(False)

	def clear_inputs(self):
		#print 'clearing'
		pass

	def on_color_button(self, event):
		color_id = event.GetId() - PALETTE_INPUT_ID
		clicked = event.GetEventObject()
		self.active_button = clicked
		color = self.palettes[color_id / 16][color_id % 16]
		for i, value in enumerate(color):
			if i < 3:
				self.color_sliders[i].SetValue(value)
				self.color_sliders[i].Update()
				self.color_inputs[i].SetValue(str(value))
				self.color_inputs[i].Update()

		self.preview.SetBackgroundColour(clicked.GetBackgroundColour())
		self.preview.Refresh()

		self.FindWindowById(5000).Enable()
		self.FindWindowById(5001).Enable()
		self.FindWindowById(5002).Enable()
		self.FindWindowById(6000).Enable()
		self.FindWindowById(6001).Enable()
		self.FindWindowById(6002).Enable()
		


	def on_color_slide(self, event):
		if not hasattr(self, 'active_button'):
			return
			
		slider = event.GetId()
		position = event.GetPosition()
		color = slider - 5000
		color_input = self.color_inputs[color]
		color_input.SetValue(str(position))
		color_input.Update()
			
		r = self.color_sliders[0].GetValue()
		g = self.color_sliders[1].GetValue()
		b = self.color_sliders[2].GetValue()
		a = 1
		color_id = self.active_button.GetId() - PALETTE_INPUT_ID
		self.palettes[color_id / 16][color_id % 16] = (r, g, b, a)
		self.set_button_color(self.active_button, r, g, b, a)
		factor = 255.0 / 31.0
		self.preview.SetBackgroundColour(wx.Colour(int(r * factor), int(g * factor), int(b * factor)))
		self.preview.Refresh()

	def on_color_enter(self, event):
		try:
			newInt = int(event.GetString())
		except:
			print("Palette Edit Warning: use a valid int between 0-31")
			return
		if newInt < 0:
			newInt = 0
		elif newInt > 31:
			newInt = 31
		whichSlider = event.GetId() - 6000
		position = newInt
		#Text update in case an out of bounds number is typed
		color_input = self.color_inputs[whichSlider]
		color_input.SetValue(str(position))
		color_input.Update()
		#Update slider
		self.color_sliders[whichSlider].SetValue(position)
		if not self.active_button:
			return
		#Update colour
		r = self.color_sliders[0].GetValue()
		g = self.color_sliders[1].GetValue()
		b = self.color_sliders[2].GetValue()
		#a = self.color_sliders[3].GetValue()
		#Alpha slider has been removed
		a = 0
		color_id = self.active_button.GetId() - PALETTE_INPUT_ID
		self.palettes[color_id / 16][color_id % 16] = (r, g, b)
		self.set_button_color(self.active_button, r, g, b, a)
		factor = 255.0 / 31.0
		self.preview.SetBackgroundColour(wx.Colour(int(r * factor), int(g * factor), int(b * factor)))
		self.preview.Refresh()

	def set_button_color(self, button, r, g, b, a):
		factor = 255.0 / 31.0
		if (r, g, b, a) == (0, 0, 0):
			button.SetForegroundColour(wx.Colour(255, 255, 255))
		else:
			button.SetForegroundColour(wx.Colour(r, g, b))
		r = int(r * factor)
		g = int(g * factor)
		b = int(b * factor)
		button.SetBackgroundColour(wx.Colour(r, g, b))
		button.Refresh()
		
	def set_button_id_color(self, button_id, r, g, b, a):
		button = self.FindWindowById(button_id)
		factor = 255.0 / 31.0
		if (r, g, b, a) == (0, 0, 0):
			button.SetForegroundColour(wx.Colour(255, 255, 255))
		else:
			button.SetForegroundColour(wx.Colour(r, g, b))
		r = int(r * factor)
		g = int(g * factor)
		b = int(b * factor)
		button.SetBackgroundColour(wx.Colour(r, g, b))
		button.Refresh()
		
	def export_palette(self, event):
		palette_id = event.GetId()
		hex_list = [];
		
		for i, color in enumerate(self.palettes[palette_id]):
			hex_list.append(color[0] * 8)
			hex_list.append(color[1] * 8)
			hex_list.append(color[2] * 8)
		
		extraBytesNeeded = (256 - 16) * 3
		
		for index in range(extraBytesNeeded):
			hex_list.append(0)
		
		fileDialog = wx.FileDialog(self, 'Palette ACT', style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard = 'ACT Files (*.ACT)|*.ACT;*.act')
		fileDialog.SetFilename(self.app.world.map.gns.file_path + '.palette_' + str(palette_id) + '.act')
		
		
		if fileDialog.ShowModal() == wx.ID_CANCEL:
			fileDialog.Destroy()
			return
		
		pathname = fileDialog.GetPath()
		file = open (pathname, 'w') 
		
		for index in hex_list:
			file.write(chr(index))
			
		file.close()
		fileDialog.Destroy()
		
	def export_default_palette(self, event):
		hex_list = [];
		
		for i in range(16):
			hex_list.append(i * 17)
			hex_list.append(i * 17)
			hex_list.append(i * 17)
		
		extraBytesNeeded = (256 - 16) * 3
		
		for index in range(extraBytesNeeded):
			hex_list.append(0)
		
		fileDialog = wx.FileDialog(self, 'Palette ACT', style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard = 'ACT Files (*.ACT)|*.ACT;*.act')
		fileDialog.SetFilename('default_fft_palette.act')
		if fileDialog.ShowModal() == wx.ID_CANCEL:
			fileDialog.Destroy()
			return
		
		pathname = fileDialog.GetPath()
		file = open (pathname, 'w') 
		
		for index in hex_list:
			file.write(chr(index))
			
		file.close()
		fileDialog.Destroy()
		
	def import_palette(self, event):
		palette_id = event.GetId()
		
		fileDialog = wx.FileDialog(self, 'Import Palette from ACT', wildcard = 'ACT Files (*.ACT)|*.ACT;*.act')
		
		if fileDialog.ShowModal() == wx.ID_CANCEL:
			fileDialog.Destroy()
			return

		pathname = fileDialog.GetPath()
		file = open(pathname, 'r')
		all_hex = file.read();
		
		hex_list = []
		for index in all_hex:
			int_value = int(ord(index) / 8)
			hex_list.append(int_value)
		
		for index, color in enumerate(hex_list):
			palette_length = 16
			color_length = 3
			
			if(index % color_length == 0 and index < palette_length * color_length):
				color_id = index / color_length
				r = hex_list[index]
				g = hex_list[index + 1]
				b = hex_list[index + 2]
				a = 1
				self.palettes[palette_id][color_id] = (r, g, b, a)
				self.set_button_id_color(PALETTE_INPUT_ID + palette_id * 16 + color_id, r, g, b, a)
			
		self.to_data(self)
		file.close()
		fileDialog.Destroy()

	def from_data(self, palettes):
		self.palettes = []
		for y, palette in enumerate(palettes):
			selfpalette = []
			for x, color in enumerate(palette.colors.colors):
				self.set_button_color(self.color_buttons[y*16 + x], *color)
				selfpalette.append(color)
			self.palettes.append(selfpalette)

	def to_data(self, foo):
		for y, palette in enumerate(self.palettes):
			for x, color in enumerate(palette):
				self.app.world.color_palettes[y].colors.colors[x] = color


class LightsEditWindow(wx.Frame):
	def __init__(self, parent, ID, title):
		self.app = parent
		wx.Frame.__init__(self, parent.wx_win, ID, title,
				wx.DefaultPosition, wx.DefaultSize)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.active_button = None
		panel = wx.Panel(self, wx.ID_ANY)
		sizer_sections = wx.BoxSizer(wx.VERTICAL)
		self.undo_data = []
		self.color_buttons = {}
		self.colors = []
		# Light Preview checkbox
		self.light_preview = wx.CheckBox(panel, wx.ID_ANY, 'Preview In-Game Lighting')
		self.light_preview.Bind(wx.EVT_CHECKBOX, self.on_light_preview_click)
		sizer_sections.Add(self.light_preview, flag=wx.ALL, border=10)
		# Directional lights
		self.elevation_sliders = []
		self.elevation_inputs = []
		self.azimuth_sliders = []
		self.azimuth_inputs = []
		for i in range(3):
			label_light = wx.StaticText(panel, wx.ID_ANY, 'Directional Light %u' % i)
			sizer_sections.Add(label_light)
			sizer_light = wx.FlexGridSizer(rows=3, cols=3)
			color_label = wx.StaticText(panel, wx.ID_ANY, 'Color')
			color = wx.Window(panel, 7000 + i, size=wx.Size(60,20))
			color.SetBackgroundColour(wx.Colour(0,0,0))
			color.Bind(wx.EVT_LEFT_DOWN, self.on_color_button)
			sizer_light.Add(color_label)
			sizer_light.Add(color)
			sizer_light.AddSpacer(1)
			self.color_buttons[('directional', i)] = color
			elevation_label = wx.StaticText(panel, wx.ID_ANY, 'Elevation')
			elevation_slider = wx.Slider(panel, 7000 + i, 0, -90, 90, size=wx.Size(180, -1))
			elevation_slider.Bind(wx.EVT_SCROLL, self.on_elevation_slide)
			elevation_input = wx.TextCtrl(panel, 7000 + i)
			elevation_input.Bind(wx.EVT_TEXT_ENTER, self.on_elevation_enter)
			sizer_light.Add(elevation_label)
			sizer_light.Add(elevation_slider)
			sizer_light.Add(elevation_input)
			self.elevation_sliders.append(elevation_slider)
			self.elevation_inputs.append(elevation_input)
			azimuth_label = wx.StaticText(panel, wx.ID_ANY, 'Azimuth')
			azimuth_slider = wx.Slider(panel, 7000 + i, 0, -180, 180, size=wx.Size(180, -1))
			azimuth_slider.Bind(wx.EVT_SCROLL, self.on_azimuth_slide)
			azimuth_input = wx.TextCtrl(panel, 7000 + i)
			azimuth_input.Bind(wx.EVT_TEXT_ENTER, self.on_azimuth_enter)
			sizer_light.Add(azimuth_label)
			sizer_light.Add(azimuth_slider)
			sizer_light.Add(azimuth_input)
			self.azimuth_sliders.append(azimuth_slider)
			self.azimuth_inputs.append(azimuth_input)
			sizer_sections.Add(sizer_light, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Ambient light
		label_light = wx.StaticText(panel, wx.ID_ANY, 'Ambient Light')
		sizer_sections.Add(label_light)
		sizer_light = wx.FlexGridSizer(rows=1, cols=2)
		color_label = wx.StaticText(panel, wx.ID_ANY, 'Color')
		i += 1
		color = wx.Window(panel, 7000 + i, size=wx.Size(60,20))
		color.Bind(wx.EVT_LEFT_DOWN, self.on_color_button)
		color.SetBackgroundColour(wx.Colour(0,0,0))
		sizer_light.Add(color_label)
		sizer_light.Add(color)
		self.color_buttons['ambient'] = color
		sizer_sections.Add(sizer_light, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Background
		label_background = wx.StaticText(panel, wx.ID_ANY, 'Background Colors')
		sizer_sections.Add(label_background)
		sizer_background = wx.FlexGridSizer(rows=2, cols=2)
		color_label = wx.StaticText(panel, wx.ID_ANY, 'Color 0')
		i += 1
		color = wx.Window(panel, 7000 + i, size=wx.Size(60,20))
		color.Bind(wx.EVT_LEFT_DOWN, self.on_color_button)
		color.SetBackgroundColour(wx.Colour(0,0,0))
		sizer_background.Add(color_label)
		sizer_background.Add(color)
		self.color_buttons[('background', 0)] = color
		color_label = wx.StaticText(panel, wx.ID_ANY, 'Color 1')
		i += 1
		color = wx.Window(panel, 7000 + i, size=wx.Size(60,20))
		color.Bind(wx.EVT_LEFT_DOWN, self.on_color_button)
		color.SetBackgroundColour(wx.Colour(0,0,0))
		sizer_background.Add(color_label)
		sizer_background.Add(color)
		self.color_buttons[('background', 1)] = color
		sizer_sections.Add(sizer_background, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Color sliders
		label_picker = wx.StaticText(panel, wx.ID_ANY, 'Color Picker')
		sizer_sections.Add(label_picker)
		sizer_sliders_preview = wx.BoxSizer(wx.HORIZONTAL)
		sizer_color_sliders = wx.BoxSizer(wx.VERTICAL)
		self.color_sliders = []
		self.color_inputs = []
		for i, color in enumerate(['R', 'G', 'B']):
			sizer_slide_input = wx.BoxSizer(wx.HORIZONTAL)
			color_label = wx.StaticText(panel, wx.ID_ANY, color, size=wx.Size(20, -1))
			color_slider = wx.Slider(panel, 7000 + i, 0, 0, 255, size=wx.Size(128, -1))
			color_slider.Bind(wx.EVT_SCROLL, self.on_color_slide)
			color_input = wx.TextCtrl(panel, 7000 + i)
			color_input.Bind(wx.EVT_TEXT_ENTER, self.on_color_enter)
			sizer_slide_input.Add(color_label, 0)
			sizer_slide_input.Add(color_slider, 0)
			sizer_slide_input.Add(color_input, 0)
			sizer_color_sliders.Add(sizer_slide_input)
			self.color_sliders.append(color_slider)
			self.color_inputs.append(color_input)
		sizer_sliders_preview.Add(sizer_color_sliders)
		self.preview = wx.Window(panel, wx.ID_ANY, size=wx.Size(80, 80))
		self.preview.SetBackgroundColour(wx.Colour(0, 0, 0))
		sizer_sliders_preview.Add(self.preview)
		sizer_sections.Add(sizer_sliders_preview, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		# Buttons
		undo_button = wx.Button(panel, wx.ID_UNDO)
		undo_button.Bind(wx.EVT_BUTTON, self.undo)
		sizer_sections.Add(undo_button, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10)
		panel.SetSizer(sizer_sections)
		sizer_sections.SetSizeHints(panel)
		sizer_sections.SetSizeHints(self)

	def on_close(self, event):
		for i in range(3):
			self.app.world.dir_lights[i].show_line(False)
		self.Show(False)

	def clear_inputs(self):
		#print 'clearing'
		pass

	def on_color_button(self, event):
		color_id = event.GetId() - 7000
		range_max = 255
		if color_id < 3:
			range_max = 32767
		clicked = event.GetEventObject()
		self.active_button = clicked
		color = self.colors[color_id]
		for i, value in enumerate(color):
			self.color_sliders[i].SetRange(0, range_max)
			self.color_sliders[i].SetValue(value)
			self.color_sliders[i].Update()
			self.color_inputs[i].SetValue(str(value))
			self.color_inputs[i].Update()
		self.preview.SetBackgroundColour(clicked.GetBackgroundColour())
		self.preview.Refresh()

	def on_color_slide(self, event):
		if not self.active_button:
			return
		slider_id = event.GetId()
		position = event.GetPosition()
		input_id = slider_id - 7000
		color_input = self.color_inputs[input_id]
		color_input.SetValue(str(position))
		color_input.Update()
		r = self.color_sliders[0].GetValue()
		g = self.color_sliders[1].GetValue()
		b = self.color_sliders[2].GetValue()
		color_id = self.active_button.GetId() - 7000
		range_max = 255
		if color_id < 3:
			range_max = 32767
		self.colors[color_id] = (r, g, b)
		factor = 255.0 / range_max
		self.preview.SetBackgroundColour(wx.Colour(int(r * factor), int(g * factor), int(b * factor)))
		self.preview.Refresh()
		self.set_button_color(range_max, self.active_button, r, g, b)
		self.to_data()

	def on_color_enter(self, event):
		if not self.active_button:
			return
		try:
			position = int(event.GetString())
		except:
			print("Light Edit Warning: use a valid int between 0-32767")
			return
		if position < 0:
			position = 0
		elif position > 32767:
			position = 32767
		slider_id = event.GetId()
		input_id = slider_id - 7000
		color_input = self.color_inputs[input_id]
		color_input.SetValue(str(position))
		color_input.Update()
		self.color_sliders[input_id].SetValue(position)
		r = self.color_sliders[0].GetValue()
		g = self.color_sliders[1].GetValue()
		b = self.color_sliders[2].GetValue()
		color_id = self.active_button.GetId() - 7000
		range_max = 255
		if color_id < 3:
			range_max = 32767
		self.colors[color_id] = (r, g, b)
		factor = 255.0 / range_max
		self.preview.SetBackgroundColour(wx.Colour(int(r * factor), int(g * factor), int(b * factor)))
		self.preview.Refresh()
		self.set_button_color(range_max, self.active_button, r, g, b)
		self.to_data()

	def on_elevation_slide(self, event):
		slider_id = event.GetId()
		position = event.GetPosition()
		input_id = slider_id - 7000
		elevation_input = self.elevation_inputs[input_id]
		elevation_input.SetValue(str(position))
		elevation_input.Update()
		self.to_data()

	def on_elevation_enter(self, event):
		slider_id = event.GetId()
		try:
			position = float(event.GetString())
		except:
			print("Light Edit Warning: use a valid float between 0-90")
			return
		if position < -90:
			position = -90
		elif position > 90:
			position = 90
		input_id = slider_id - 7000
		elevation_input = self.elevation_inputs[input_id]
		elevation_input.SetValue(str(position))
		elevation_input.Update()
		self.elevation_sliders[input_id].SetValue(position)
		self.to_data()

	def on_azimuth_slide(self, event):
		slider_id = event.GetId()
		position = event.GetPosition()
		input_id = slider_id - 7000
		azimuth_input = self.azimuth_inputs[input_id]
		azimuth_input.SetValue(str(position))
		azimuth_input.Update()
		self.to_data()

	def on_azimuth_enter(self, event):
		slider_id = event.GetId()
		try:
			position = float(event.GetString())
		except:
			print("Light Edit Warning: use a valid float between -180 - 180")
			return
		if position < -180:
			position = -180
		elif position > 180:
			position = 180
		input_id = slider_id - 7000
		azimuth_input = self.azimuth_inputs[input_id]
		azimuth_input.SetValue(str(position))
		azimuth_input.Update()
		self.azimuth_sliders[input_id].SetValue(position)
		self.to_data()

	def on_light_preview_click(self, event):
		self.app.set_full_light(not event.IsChecked())

	def set_button_color(self, max_value, button, r, g, b):
		factor = 255.0 / max_value
		r = int(r * factor)
		g = int(g * factor)
		b = int(b * factor)
		button.SetBackgroundColour(wx.Colour(r, g, b))
		button.Refresh()

	def from_data(self, dir_lights, amb_light, background):
		self.undo_data = []
		self.colors = []
		for i, light in enumerate(dir_lights):
			(elevation, azimuth) = vector_to_sphere(*light.direction.coords)
			self.elevation_sliders[i].SetValue(90 - elevation)
			self.elevation_inputs[i].SetValue(str(90 - elevation))
			self.azimuth_sliders[i].SetValue(azimuth)
			self.azimuth_inputs[i].SetValue(str(azimuth))
			self.set_button_color(32768, self.color_buttons[('directional', i)], *light.color)
			self.colors.append(light.color)
			self.undo_data.append((90-elevation, azimuth, light.color))
		self.set_button_color(255, self.color_buttons['ambient'], *amb_light.color)
		self.colors.append(amb_light.color)
		self.undo_data.append(amb_light.color)
		self.colors.append(background.color1)
		self.set_button_color(255, self.color_buttons[('background', 0)], *background.color1)
		self.undo_data.append(background.color1)
		self.colors.append(background.color2)
		self.set_button_color(255, self.color_buttons[('background', 1)], *background.color2)
		self.undo_data.append(background.color2)

	def undo(self, event):
		for i in range(3):
			(elevation, azimuth, color) = self.undo_data[i]
			self.elevation_sliders[i].SetValue(elevation)
			self.azimuth_sliders[i].SetValue(azimuth)
			self.set_button_color(32768, self.color_buttons[('directional', i)], *color)
			self.colors[i] = color
		(amb_color, bg_color1, bg_color2) = self.undo_data[3:]
		self.set_button_color(255, self.color_buttons['ambient'], *amb_color)
		self.colors[3] = amb_color
		self.set_button_color(255, self.color_buttons[('background', 0)], *bg_color1)
		self.colors[4] = bg_color1
		self.set_button_color(255, self.color_buttons[('background', 1)], *bg_color2)
		self.colors[5] = bg_color2
		self.to_data()

	def to_data(self):
		for i in range(3):
			self.app.world.dir_lights[i].color = self.colors[i]
			elevation = 90 - self.elevation_sliders[i].GetValue()
			azimuth = self.azimuth_sliders[i].GetValue()
			(x, y, z) = sphere_to_vector(elevation, azimuth)
			self.app.world.dir_lights[i].direction.X = x
			self.app.world.dir_lights[i].direction.Y = y
			self.app.world.dir_lights[i].direction.Z = z
			self.app.world.dir_lights[i].direction.coords = (x, y, z)
			self.app.world.dir_lights[i].init_node_path()
			self.app.world.dir_lights[i].init_node_path_line(i)
			self.app.world.dir_lights[i].show_line(True)
		self.app.world.amb_light.color = self.colors[3]
		self.app.world.amb_light.init_node_path()
		self.app.world.background.color1 = self.colors[4]
		self.app.world.background.color2 = self.colors[5]
		self.app.world.background.init_node_path()


		
# This defines what the mouse clicks do		
class Map_Viewer(DirectObject):
	def __init__(self, *args, **kwargs):
		self.showbase = ShowBase()
		wp = WindowProperties()
		wp.setTitle('Ganesha')
		self.showbase.win.requestProperties(wp)
		self.state = ViewerState(self, 'viewer_state')
		self.mouse = ViewerMouse(self)
		self.world = World(self)
		self.selected_object = None
		self.full_light_enabled = False
		self.terrain_mode = MESH_ONLY
		self.width = None
		self.height = None
		self.accept('window-event', self.on_window_event)
		self.accept(']', self.next_situation)
		self.accept('[', self.prev_situation)
		self.accept('n', self.next_gns)
		self.accept('t', self.next_terrain_mode)
		self.accept('s', self.world.write)
		self.accept('o', self.output_texture)
		self.accept('i', self.import_texture)
		self.accept('p', self.edit_palettes)
		self.accept('l', self.edit_lights)
		self.accept('+', self.add_polygon)
		self.accept('d', self.edit_terrain_dimensions)
		self.accept('f', self.copy_polygon)
		self.accept('shift-=', self.add_polygon)
		self.accept('u', self.move_all_polygons)

		base.disableMouse()
		self.state.request('Spin')
		self.selected_objects = []
		self.multiSelect = False
		self.accept('control', self.multi_select)
		self.accept('control-up', self.end_multi_select)
		self.accept('q', self.decrease_Y)
		self.accept('e', self.increase_Y)
		self.accept('arrow_down', self.decrease_X)
		self.accept('arrow_up', self.increase_X)
		self.accept('arrow_right', self.decrease_Z)
		self.accept('arrow_left', self.increase_Z)
		self.accept('delete', self.delete_selected)
		self.accept('escape', self.open_settings_window)
		self.accept('control-a', self.select_all)
		self.accept('tab', self.open_multi_terrain_editor)
		#base.messenger.toggleVerbose()

	# TODO: move these functions somewhere after start (organize)
	def multi_select(self):
		self.multiSelect = True
	
	def end_multi_select(self):
		self.multiSelect = False

	def select_all(self):
		print("select all!")
		#Needs special version of unselect to avoid crashes
		for obj in self.selected_objects:
			obj.unselect()
			self.selected_objects = []
		if self.selected_object:
			self.selected_object.unselect()
			self.selected_object = None
		
		for obj in self.world.polygons:
			obj.select()
			self.selected_objects.append(obj)
		
	def copy_polygon(self):
		if not len(self.selected_objects) == 0:
			for poly in self.selected_objects:
				texture = True
				if(poly.source.unknown5 is not None):
					texture = False
				if poly is not None:
					self.world.copy_polygon_to_XOffset(poly, 0 * 28, texture)
		elif self.selected_object:
			if(self.selected_object.source.unknown5 is not None):
				texture = False
			self.world.copy_polygon_to_XOffset(self.selected_object, 0 * 28, texture)

	def increase_Y(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('Y', 12, 1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('Y', 12, 1, [self.selected_object])
		else: #It is a tile
			if not len(self.selected_objects) == 0:
				self.world.move_selected_tile(1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_tile(1, [self.selected_object])

	def decrease_Y(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('Y', 12, -1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('Y', 12, -1, [self.selected_object])
		else: #It is a tile
			if not len(self.selected_objects) == 0:
				self.world.move_selected_tile(-1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_tile(-1, [self.selected_object])

	def increase_X(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('X', 28, 1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('X', 28, 1, [self.selected_object])

	def decrease_X(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('X', 28, -1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('X', 28, -1, [self.selected_object])
		
	def increase_Z(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('Z', 28, 1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('Z', 28, 1, [self.selected_object])

	def decrease_Z(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				self.world.move_selected_poly('Z', 28, -1, self.selected_objects)
			elif self.selected_object:
				self.world.move_selected_poly('Z', 28, -1, [self.selected_object])

	def delete_selected(self):
		if isinstance(self.selected_object, Polygon) or isinstance(self.selected_objects[0], Polygon):
			if not len(self.selected_objects) == 0:
				for obj in self.selected_objects:
					self.world.delete_polygon(obj)
					self.unselect()
					self.polygon_edit_window.clear_inputs()
					self.polygon_edit_window.Show(False)
					self.uv_edit_window.close()
			elif self.selected_object:
				self.world.delete_polygon(self.selected_object)
				self.unselect()
				self.polygon_edit_window.clear_inputs()
				self.polygon_edit_window.Show(False)
				self.uv_edit_window.close()
	
		
	def start(self, gns_path):
		self.wx_app = wx.App(0)
		self.wx_win = wx.Frame(None, -1, 'Ganesha wxWindow', wx.DefaultPosition)
		self.wx_event_loop = wx.EventLoop()
		wx.EventLoop.SetActive(self.wx_event_loop)
		self.polygon_add_window = PolygonAddWindow(self, -1, 'Add Polygon')
		self.polygon_edit_window = PolygonEditWindow(self, -1, 'Edit Polygon')
		self.uv_edit_window = UVEditWindow(self)
		self.accept('uv_edit_window_closed', self.uv_edit_window.on_close)
		self.terrain_edit_window = TerrainEditWindow(self, -1, 'Edit Terrain')
		self.multi_terrain_edit_window = MultiTerrainEditWindow(self, -1, 'Edit Multiple Terrains')
		self.terrain_dimensions_edit_window = TerrainDimensionsEditWindow(self, -1, 'Edit Terrain Dimensions')
		self.move_all_polygons_edit_window = MoveAllPolygonsEditWindow(self, -1, 'Move All Polygons')
		self.palette_edit_window = PaletteEditWindow(self, -1, 'Edit Palettes')
		self.lights_edit_window = LightsEditWindow(self, -1, 'Edit Lights and Background')
		taskMgr.add(self.handle_wx_events, 'handle_wx_events')
		render.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
		self.world.read_gns(gns_path)
		self.world.read()
		self.world.set_terrain_alpha(self.terrain_mode)
		self.set_full_light(self.full_light_enabled)
		self.settings_window = SettingsWindow(self, -1, 'Settings Window')
		run()

	def handle_wx_events(self, task):
		while self.wx_event_loop.Pending():
			self.wx_event_loop.Dispatch()
		self.wx_app.ProcessIdle()
		return task.cont

	def on_window_event(self, window):
		changed = False
		size_x = window.getProperties().getXSize()
		size_y = window.getProperties().getYSize()
		title = window.getProperties().getTitle()
		if title != 'Ganesha':
			return None
		if size_x != self.width:
			self.width = size_x
			changed = True
		if size_y != self.height:
			self.height = size_y
			changed = True
		if changed:
			self.world.init_camera(1.0 * size_x / size_y)
			self.world.set_camera_zoom()

	def file_dialog(self):
		dlg = wx.FileDialog(self.wx_win, "Choose a GNS file", wildcard = 'GNS Files (*.GNS)|*.GNS;*.gns')
		if dlg.ShowModal() == wx.ID_OK:
			return dlg.GetPath()
		dlg.Destroy()
		return None

	def output_texture(self):
		import os.path
		dlg = wx.FileDialog(self.wx_win, "Output Texture to PNG", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, wildcard = 'PNG Files (*.PNG)|*.PNG;*.png')
		filename = os.path.basename(self.world.map.texture_files[0])
		dlg.SetFilename(filename + '.png')
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			if path[-4:].lower() != '.png':
				path += '.png'
			self.world.texture.export(path, self.world.map.get_texture())
		dlg.Destroy()
		return None
		
	def import_texture(self):
		dlg = wx.FileDialog(self.wx_win, "Import Texture from PNG", wildcard = 'PNG Files (*.PNG)|*.PNG;*.png')
		if dlg.ShowModal() == wx.ID_OK:
			self.world.texture.import_(dlg.GetPath(), self.world.color_palettes)
		dlg.Destroy()
		return None

	def set_full_light(self, light_on):
		self.full_light_enabled = light_on
		self.world.set_full_light(light_on)

	def find_polygon(self, level):
		tile = self.selected_object
		found = False
		for polygon in self.world.polygons:
			if polygon.terrain_coords == (tile.x, tile.z, level):
				self.terrain_mode = MOSTLY_MESH
				self.world.set_terrain_alpha(self.terrain_mode)
				self.select(polygon)
				found = True
				break
		if not found:
			print 'No polygon found for the selected tile.'

	def find_tile(self):
		polygon = self.selected_object
		(x, z, level) = polygon.source.terrain_coords
		tile = None
		try:
			tile = self.world.terrain.tiles[level][z][x]
		except IndexError:
			print 'No tile found for the selected polygon.'
		if tile is not None:
			self.terrain_mode = MOSTLY_TERRAIN
			self.world.set_terrain_alpha(self.terrain_mode)
			self.select(tile)

	def add_polygon(self):
		if self.terrain_mode in [MESH_ONLY, MOSTLY_MESH]:
			self.polygon_add_window.Show(True)
			self.polygon_add_window.MakeModal(True)
		
	def move_all_polygons(self):
		self.move_all_polygons_edit_window.Show(True)
		#self.move_all_polygons_edit_window.MakeModal(True)	

	def open_settings_window(self):
		self.settings_window.Show(True)	

	def open_multi_terrain_editor(self):
		self.multi_terrain_edit_window.clear_inputs()
		self.multi_terrain_edit_window.Show(True)
		self.multi_terrain_edit_window.Raise()
			
			
	def edit_terrain_dimensions(self):
		if self.terrain_mode in [TERRAIN_ONLY, MOSTLY_TERRAIN]:
			self.terrain_dimensions_edit_window.from_data(self.world.terrain)
			self.terrain_dimensions_edit_window.Show(True)
			self.terrain_dimensions_edit_window.MakeModal(True)

	def delete_polygon(self):
		self.world.delete_polygon(self.selected_object)
		self.unselect()
		self.polygon_edit_window.clear_inputs()
		self.polygon_edit_window.Show(False)
		self.uv_edit_window.close()

	def edit_lights(self):
		self.lights_edit_window.from_data(self.world.dir_lights, self.world.amb_light, self.world.background)
		self.lights_edit_window.light_preview.SetValue(not self.full_light_enabled)
		self.lights_edit_window.Show(True)
		for i in range(3):
			self.world.dir_lights[i].show_line(True)

	def edit_palettes(self):
		self.palette_edit_window.from_data(self.world.color_palettes)
		self.palette_edit_window.Show(True)

	def select(self, hovered_object):
		self.unselect()
		if hovered_object:
			if self.multiSelect:
				#If the object is not already selected
				if not hovered_object in self.selected_objects:
					#If the list is empty, or if the types in the list match the type selected (so we don't mix Tile / Poly)
					if len(self.selected_objects) == 0 or type(self.selected_objects[0]) == type(hovered_object):
						self.selected_objects.append(hovered_object)
						hovered_object.select()
					#If the user tries to multi-select polygons and tiles together, don't
					else:
						pass
				#If the object is already selected
				else:
					self.selected_objects.remove(hovered_object)
					hovered_object.unselect()
			else:
				self.selected_object = hovered_object
				self.selected_object.select()

			if isinstance(self.selected_object, Polygon):
				self.terrain_edit_window.clear_inputs()
				self.terrain_edit_window.Show(False)
				self.polygon_edit_window.from_data(self.selected_object)
				self.polygon_edit_window.Show(True)
				self.polygon_edit_window.Raise()
			elif isinstance(self.selected_object, Tile):
				self.polygon_edit_window.clear_inputs()
				self.polygon_edit_window.Show(False)
				self.uv_edit_window.close()
				self.terrain_edit_window.from_data(self.selected_object)
				self.terrain_edit_window.Show(True)
				self.terrain_edit_window.Raise()
		else:
			self.polygon_edit_window.clear_inputs()
			self.polygon_edit_window.Show(False)
			self.uv_edit_window.close()
			self.terrain_edit_window.clear_inputs()
			self.terrain_edit_window.Show(False)
			self.multi_terrain_edit_window.clear_inputs()
			self.multi_terrain_edit_window.Show(False)

	def unselect(self):
		if not self.multiSelect:
			for obj in self.selected_objects:
				obj.unselect()
			self.selected_objects = []
		if self.selected_object:
			self.selected_object.unselect()
			self.selected_object = None

	def next_situation(self):
		self.unselect()
		self.polygon_edit_window.clear_inputs()
		self.polygon_edit_window.Show(False)
		self.terrain_edit_window.clear_inputs()
		self.terrain_edit_window.Show(False)
		self.uv_edit_window.close()
		self.world.next_situation()
		if self.palette_edit_window.IsShown():
			self.palette_edit_window.from_data(self.world.color_palettes)
		if self.lights_edit_window.IsShown():
			self.lights_edit_window.from_data(self.world.dir_lights, self.world.amb_light, self.world.background)
		self.world.set_terrain_alpha(self.terrain_mode)
		self.set_full_light(self.full_light_enabled)

	def prev_situation(self):
		self.unselect()
		self.polygon_edit_window.clear_inputs()
		self.polygon_edit_window.Show(False)
		self.terrain_edit_window.clear_inputs()
		self.terrain_edit_window.Show(False)
		self.uv_edit_window.close()
		self.world.prev_situation()
		if self.palette_edit_window.IsShown():
			self.palette_edit_window.from_data(self.world.color_palettes)
		if self.lights_edit_window.IsShown():
			self.lights_edit_window.from_data(self.world.dir_lights, self.world.amb_light, self.world.background)
		self.world.set_terrain_alpha(self.terrain_mode)
		self.set_full_light(self.full_light_enabled)

	def next_gns(self):
		self.unselect()
		self.polygon_edit_window.clear_inputs()
		self.polygon_edit_window.Show(False)
		self.terrain_edit_window.clear_inputs()
		self.terrain_edit_window.Show(False)
		self.uv_edit_window.close()
		self.world.next_gns()
		if self.palette_edit_window.IsShown():
			self.palette_edit_window.from_data(self.world.color_palettes)
		if self.lights_edit_window.IsShown():
			self.lights_edit_window.from_data(self.world.dir_lights, self.world.amb_light, self.world.background)
		self.world.set_terrain_alpha(self.terrain_mode)
		self.set_full_light(self.full_light_enabled)

	def next_terrain_mode(self):
		self.terrain_mode += 1
		self.terrain_mode %= len(terrain_modes)
		self.world.set_terrain_alpha(self.terrain_mode)
		self.set_full_light(self.full_light_enabled)
