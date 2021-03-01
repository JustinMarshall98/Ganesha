Ganesha
=======

A map editor for Final Fantasy Tactics (PSX)


Hardware Requirements
=====================

 - Video card with at least:
   - 2MB of VRAM
   - Support for OpenGL 1.x


Find out more about Ganesha, and the FFT Hacking community
==========================================================
https://ffhacktics.com/smf/index.php?msg=217648

https://gomtuu.org/fft/Ganesha/ (Gomtuu's original program, download for v0.60)

CREDITS
=======
Gomtuu: Creating Ganesha and bringing it up to v0.60, creating all of the original documentation
Twinees: Updating Ganesha to v0.72 and bringing it into TECHNICOLOR
Jumza: Owner of the repo, updated Ganesha to v0.73
   
Changelog
=========
2021-02-28 - v0.73 - Jumza Update
 - Added the ability to select / unselect multiple polygons at once for mass editing / deleting
 - Added hotkeys for adjusting X (+-28), Z (+-28), Y (+-12), and deleting polygons in the map viewer
 - Added rotate vertex buttons in relation to two more planes (Just XZ in v0.70, now XZ, XY, ZY rotation possible)
 - Added new 'settings' window with a legend for what every button does (Escape)
 - Lighting and Palette textboxes now accept typed entries
 - Fixed Lighting Elevation range from being bound [0,90] to [-90,90]

2016-07-16 - v0.72 - Twin Update
 - Added -20 and +20 buttons for easier UV movement per request.
 - Fixed "Invisible from:" layout per request.

2016-05-26 - v0.71 - Twin Update
 - Fixed malfunction with the import and export options. 

2016-05-25 - v0.70 - Twin Update
 - Added Rotate Face buttons and Rotate Vertex buttons in the polygon edit window.
 - Added new window to move the map. Simply press 'u' (Warning: do not move map into negative zones, then back into positive zones
   otherwise you will need to fix the Terrain X and Terrain Z values that moved into the negative zone.)
 - Ganesha is now in color! Note: This may cause lag in slow computers. The map will not update the palette/s dynamically.
   If you want to see the new changes to the palette/s save and reload!

(All previous updates and creation credits to Gomtuu)

2010-08-04 - v0.60
 - Added code to detect and fix broken polygons created in 0.55.
 - Put new polygons at maxY+12 instead of maxY+1.
 - Added ability to edit UV coordinates in a popup window.
 - Fixed texture import bug when used in Windows.
 - Fixed bug that prevented Guess Normal Coordinates from working on triangles.

2010-02-18 - v0.57
 - Fixed bug that caused new polygons to look wrong.
 - Made new polygons appear 1 unit above the highest polygon.
 - Prevented zoom from resetting when clicking polygons.
 - Made text inputs in polygon edit window smaller.
 - Added +28/-28 and +12/-12 buttons for moving polygons.
 - Improved the sizing and behavior of edit windows.

2010-02-14 - v0.55
 - Changed texture output dialog into a Save dialog.
 - Added Terr. Lvl input in polygon edit window.
 - Fixed Terrain X, Terrain Z inputs in polygon edit window.
 - Added ability to toggle in-game lighting preview.
 - Added terrain X, Z coordinates to terrain edit window for reference.
 - Added buttons to switch between terrain edit window and polygon edit window.
 - Made Ganesha close files while it's not using them.
 - Added ability to add polygons.
 - Added notification of any change in the number of sectors a file requires.
 - Added ability to delete polygons.
 - Made the right mouse button rotate the camera just like the mouse wheel.
 - Added ability to set terrain dimensions.
 - Let Ganesha load data files regardless of sector number listed in GNS file.

2010-02-10 - v0.40
 - Added ability to edit most things.

2009-04-07 - v0.02
 - Added background gradient.
 - Added Mac OSX readme file.

2009-03-12 - v0.01
 - First release.

2009-02-24
 - Started development.


Using Ganesha
=============

For instructions on how to use Ganesha, please visit:

http://gomtuu.org/fft/Ganesha/instructions.html

or see instructions below:



Warning: Ganesha does not have many "foolproofing" features. If you apply a change, you usually can't undo it; 
if you close a window without applying a change, you will not be prompted about unsaved changes; etc. So be careful.
Before You Start

In order to edit maps, you'll need to copy the MAP folder from the Final Fantasy Tactics CD onto your hard drive. 
Some operating systems will mark files copied from a CD as read-only, even when they're on your hard drive, so make 
sure the files are writable before you start.

    On Map Files
    The MAP folder contains 2 basic kinds of files: GNS files, which end with a .GNS extension, and numbered files,
	which end in numbers like .9, .10, .11, etc. Ganesha will need both types of files to edit maps. GNS files are
	essentially indexes of which numbered files contain which types of data and when to use each numbered file. Since
	there is 1 GNS file per map and it references all the other necessary files, GNS files are the ones Ganesha looks
	for when it prompts you to open a map.

	
Viewing Maps
============
If you ran Ganesha by double-clicking it, you'll be prompted to choose a GNS file to load. Otherwise, Ganesha will
open the GNS file you gave on the command line.

When Ganesha starts, it will display the map you selected, and the camera will automatically rotate around the map.
You can take control of the camera, however. Scroll your mouse wheel to zoom in and out of the map. Click and drag
the mouse wheel or the right mouse button to rotate the map to any angle. If you rotate the map manually, automatic
rotation will not resume.

The red, green, and blue lines are the X, Y, and Z axes, respectively.

Ganesha will view the map's first "situation" by default. A situation is a combination of an "arrangement" (different
configurations of polygons and terrain), a weather condition (sunny, cloudy, very cloudy), and a time of day. To cycle
through situations, use the [ and ] keys. Most maps have about 10 situations, but this varies. Be sure you have the
right situation selected before you start editing a map, or you won't see your changes in the game when you're done.
(This is especially true for lights and backgrounds because there are many alternate copies of these, and not so many
copies of polygons and terrain.)

You can also load the next map by pressing N (or n).

Ganesha has 4 viewing/editing modes. Press T (or t) to cycle through them:

    Polygon mode with no terrain visible (default)
    Polygon mode with terrain partially visible
    Terrain mode with polygons partially visible
    Terrain mode with no polygons visible

	
Editing Polygons
================
First, you should understand that polygons are entirely cosmetic in Final Fantasy Tactics. This means that the placement
and appearance of polygons doesn't affect the heights and depths of tiles, the materials they're made of, and so on. A
polygon can be anywhere and look like anything, and it doesn't affect gameplay (unless it happens to obscure a monster
or something). To edit terrain, which does directly affect gameplay, see the next section.

To edit a polygon, click on it once. The polygon will be highlighted, and a colored marker will be placed at each of its
points to help you identify which points you want to edit. You'll also notice a line sticking out of each polygon. This
line is a visual representation of the point's normal vector, which is used in lighting calculations.

For each of the polygon's points, the edit window shows:

    The point's X, Y, and Z coordinates
    The point's normal vector, in spherical coordinates (nE and nA)
    The point's U and V (texture) coordinates

    On Spherical Coordinates
    Elevation (nE) is the angle (in degrees) between the horizon (the X,Z plane) and the direction the vector is pointing.
	A vector with a 90-degree elevation will point straight up.

    Azimuth (nA) is the angle (in degrees) between north (which is parallel to the +Z axis) and the direction the vector
	is pointing. As long as its elevation is less than 90, a vector with azimuth 0 will point north, a vector with azimuth
	90 will point east, a vector with azimuth 180 will point south, and a vector with azimuth -90 will point west.

Next to the X, Y, and Z coordinate input boxes, you'll notice +28, -28, +12, and -12 buttons. Pressing these will
immediately move the selected polygon's points over, up, or down by an amount equal to the dimensions of a terrain tile.


Underneath the coordinate input boxes you will find the Rotate Polygon Face buttons as well as the Rotate A, B, C and D
buttons. The Rotate Polygon Face buttons rotate the face of the polygon in the rotation direction. The Rotate A, B, C and D
buttons rotate the polygon about the respective A, B, C or D vertex. In general, the rotate buttons are just in place to
simply speed up the map editing process.

In the middle of the window, you'll see a Guess Normal Vectors button. Press this button to automatically set the normal
vector of every point in the polygon to a vector that is perpendicular to the polygon's face. This is useful as a starting
point for setting a polygon's normal vectors, but if you simply use this button to set the vectors of every polygon in
your map, then all the polygons will be lit as flat, angular surfaces. You'll need to adjust the vectors if you want
surfaces to be shaded smoothly. See the section about editing lights for more information.

The Show UV button will open the UV Coordinates window, showing the entire texture image for the current map (in grayscale
because no palettes are applied). The UV polygon corresponding to the the currently-selected 3D polygon will be shown in
magenta. This is the area of the texture that will be applied to the selected 3D polygon. If you select a different 3D
polygon while the UV Coordinates window is still open, the UV polygon will change to show the newly-selected 3D polygon's
UV polygon.
You can also use the UV Coordinates window to edit the selected 3D polygon's texture page and UV polygon. To change the
texture page, simply click on a quadrant of the UV Coordinates window. The UV polygon will be moved to that quadrant.
(Each quadrant is one page.) To change the shape of the UV polygon, you must first zoom in by scrolling up on the mouse
wheel. (Scroll down to zoom back out.) Then, click one of the colored points and drag it to a new position. The colors of
the UV polygon's points match the corresponding points of the 3D polygon. You can also move the whole UV polygon by
clicking anywhere inside it and dragging it around.

The Find Terrain Tile button will attempt to find a terrain tile whose coordinates match the terrain coordinates of the
selected polygon, and then select that tile. If no tile can be found or the terrain coordinate inputs are blank, a notice
will be printed in the console. Warning: If you click Find Terrain Tile, any unapplied changes you've made to the polygon
will be lost when the tile is selected.

The edit window also shows some attributes that apply to the polygon as a whole: Tex. Page tells the game which of the
four 256x256 squares the polygon gets its texture from. (Textures are stored as a vertical stack of four 256x256 squares.)
Tex. Palette tells the game which of the 16 texture palettes to apply to this polygon while it's being rendered. Terrain X,
Terrain Z, and Terr. Lvl let the game know whether the polygon corresponds to a tile of terrain. This information is used
when the game highlights squares to indicate that you can move to them or to show that a spell or ability will affect a
square.

The Invisible From checkboxes, when checked, tell the game not to render the polygon when it is viewed from certain angles.
In some cases, this is used to remove obstructions from the foreground so the player can see what's behind them. In other
cases, it's used to avoid drawing polygons that are obscured behind obstacles (presumably to increase performance). If you
want a polygon to be visible from all angles, just leave them all unchecked. (Except that this does not prevent backface
culling.)

The Delete button will delete the selected polygon. Ganesha will first ask you if you're sure you want to delete the
polygon. If you click Yes, the polygon will be deleted immediately.

The Apply button will let you see your changes in the viewer window. Your changes will persist for as long as Ganesha is
open (i.e. there is no undo), but they are not saved back to the map file at this point. To save your changes to the disk,
press S (or s).


Adding Polygons
===============
To add a polygon, you must be in polygon mode. Press + to add a polygon. A dialog box will appear asking if you want to add
a 3-sided or 4-sided polygon and if you want it to be textured (like most polygons) or black (like the polygons around the
edges of a map). Make your selections and press Ok to add the polygon.

    On Black Polygons
    A black polygon is not quite the same as a normal polygon colored black. For one thing, adding a black polygon to a map
	increases the size of the map file less than adding a textured polygon would. This is because normal vector and texture
	data are not stored for black polygons.

    Another noteworthy attribute of black polygons is that they will cover up textured polygons, even if the black polygon
	is behind the textured polygon. When Final Fantasy Tactics draws all the polygons to the screen, it first draws the
	textured polygons, then goes back and draws the black polygons, overwriting any textured polygons it has already drawn.
	This isn't normally obvious in the game because the game designers were careful not to place any textured polygons in
	front of any black polygons, and because a black polygon that is viewed from the back will not be drawn at all (this
	is known as backface culling, and it applies to textured polygons too).

    Ganesha does not yet support this somewhat odd drawing behavior: In Ganesha, black polygons don't automatically obscure
	textured polygons.

A new polygon will appear at (0, Y+1, 0), where Y is the maximum Y coordinate of any existing polygon. This is to make sure
the new polygon won't be underneath existing polygons, so you'll be able to see it.

Edit the polygon the way you would edit any other polygon. Be sure to give the polygon Terrain X, Terrain Z, and Terr. Lvl
values if the polygon is part of a tile of terrain and should be highlighted in areas of effect.


Editing Terrain
===============
To edit terrain, you must be in terrain mode. This will allow you to select terrain tiles (instead of polygons) by clicking
on them.

The edit window will show several properties for the selected tile. You'll notice that there are columns labeled "Level 0"
and "Level 1". Whenever a bridge appears in the game, and you can stand on or under the bridge, that means there's one tile
on Level 0 and one tile on Level 1. Both tiles have the same (X, Z) coordinate (remember: X is East, Z is North), but they're
on different levels. So really, only one of the tiles displayed in the edit window is the one you clicked on. The other is
shown for convenience, and because it can be difficult to click on a Level 0 tile if it's directly underneath a Level 1 tile,
for instance.

The currently-selected tile's (X, Z) coordinates are shown for reference. These, combined with the Level number, are the
numbers you would need to enter in the Terrain X, Terrain Z, and Terr. Lvl fields of the polygon edit window in order to
associate a polygon with this tile of terrain.

Height is the height of the bottom of the tile. For tiles with depth, it's the ground below the water. For tiles that slope,
it's the lowest part of the slope. Depth is added to the tile's height to give the apparent height of the tile in the game.
For example, a tile with height 0 and depth 2 will show up as "2h depth 2" in the game. Half the slope height is also added
to the height for apparent height, so a tile with height 3 and slope 1 will appear as "3.5h".

There are four possible slope types: Flat, Incline, Convex, and Concave. These tell the game which corners of the tile are
at the top of the incline and which are at the bottom.

    Flat means all four corners are at the bottom.
    Incline means two adjacent corners are at the bottom and the other two are at the top (and Incline N means the two at the
	top are the northern corners of the tile).
    Convex means three corners are at the bottom and one is at the top (and Convex NE means the one at the top is the
	northeastern corner).
    Concave means one corner is at the bottom and the other three are at the top (and Concave NE means the middle corner of
	the top three is the northeastern corner).

Surface affects Geomancy, etc.

Impassable means that if you move your cursor to this tile, your cursor will be red. Characters are unable to move to or over
impassable tiles.

Unselectable means that you cannot move your cursor to this tile. For all intents and purposes, if a tile is unselectable,
the game ignores it. Some maps even have a row or two of unselectable tiles along one edge (outside the visible/usable portion
of the map), and you'd never know it from playing the game.

The Find Polygon button will attempt to find a polygon whose terrain coordinates match the coordinates of the selected tile,
and then select that polygon. If more than one such polygon exists, the first one found will be selected. If none exist, a
notice will be printed in the console. Warning: If you click Find Polygon, any unapplied changes you've made to the tile will
be lost when the polygon is selected.

The Apply button will let you see your changes in the viewer window. Your changes will persist for as long as Ganesha is open
(i.e. there is no undo), but they are not saved back to the map file at this point. To save your changes to the disk, press S
(or s).


Resizing Terrain
================
To resize terrain, you must be in terrain mode. Press D (or d) to display the Edit Terrain Dimensions dialog. Enter the new
dimensions and click Ok. The terrain will immediately be resized to the new dimensions. If you make the terrain smaller than
it was, tiles around the edges will be removed and lost permanently. If you make the terrain larger than it was, new flat,
"Natural Surface" tiles at height 0 will be created around the edges.


Editing Lights and the Background
=================================
To edit the map's lights and background, press L (or l).

The "Preview In-Game Lighting" checkbox at the top of the edit window (checked by default) tells Ganesha whether it should
illuminate the map the way it would be illuminated in the game, or simply with full-intensity white ambient light. If you want
to work on dark maps like the Deep Dungeon maps, you may find it easier to uncheck this checkbox than to change the map's
actual lights just so you can see what you're doing. The state of this checkbox will not affect the data saved in the map file;
it is for viewing purposes only.

The edit window shows the three directional lights, the ambient light, and the background colors. If you click any of the
colored rectangles labeled "Color", you'll be able to edit that color using the sliders at the bottom of the window.

Use the elevation and azimuth sliders to change the direction of each directional light.

    On Lighting
    The way a directional light works is as follows: For each point on a polygon, the point's normal vector is compared against
	the light's vector (direction). If the two vectors are pointing directly at one another (the angle between them is 180
	degrees), then the light at that point will be as bright as possible. If the angle is around 135 degrees (the vectors are
	sort of pointing at each other but not directly), then the light will be moderately intense. If the angle is 90 degrees or
	lower, then the light will not affect that point of the polygon much, if at all.

    After the brightness of each point of the polygon is calculated, a 3-way gradient (or a 4-way gradient, for quadrilaterals)
	is generated and used as the brightness for all the pixels inside the polygon. This is why, as explained above, a polygon
	with automatically-generated normal vectors (which are all the same) will appear flat: All the polygon's points will have
	the same intensity under all lighting conditions, so the entire polygon will have a single light intensity, with no gradient.
	If several adjacent polygons make up a surface that is supposed to appear curved, and each polygon is lit this way, then the
	surface will look angular. To avoid this, you'll need to adjust your normal vectors so the surfaces get shaded smoothly.
	Here's a rule of thumb: if two polygons share an edge, then the points that are touching should have the same normal vector
	in both polygons. This will result in a continuous gradient of light between the far edges of the two polygons.

    If you're still confused, look at some of the maps that come with the game and try to get a feel for how they use normal
	vectors.

    Ambient light is simply applied to all polygons evenly, regardless of the polygons' normal vectors.

Any changes you make in this window will be displayed immediately in the viewer. Press Undo to return everything to the way it
was when you opened the edit window. Keep in mind that you still have to press S (or s) to save your changes to the disk.


Editing Texture Palettes
========================
To edit the texture palettes, press P (or p).

The edit window shows all 16 texture palettes, one per row. Click a color to edit it using the sliders at the bottom of the
window. Click Apply to see your changes in the viewer (Note: you won't be able to see your changes yet because maps are displayed
in grayscale for now, but you still have to press Apply before you can save your changes.) After you've clicked Apply, you still
need to press S (or s) to save your changes to the disk.

If a color's R, G, B, and A values are all 0, then the color will be completely transparent.


Editing Textures
================
Ganesha does not edit textures itself, but it can output textures as PNG files which you can then edit and import back into
Ganesha.

To output a texture as a PNG, press O (or o). You'll be asked where you want to save the file. Save it anywhere you like.

The PNG will have a palette of 16 shades of gray. You cannot edit these colors. Use colors from the palette to make your changes.
Also, do not change the dimensions of the image.

To import a texture from a PNG file, press I (or i). You'll be asked which PNG file you want to import. Once you've chosen a PNG
file to import, you'll see the changes in the viewer immediately. Press S (or s) to save your changes to the disk.


Editing Map Position
====================
In version 0.70 you can now displace the whole map, rather than having to edit every single polygon in the direction you want.

To open up the menu, press U (or u). Simply press the button corresponding to the direction you want to move the entire map.

(Warning: do not move map into negative zones, then back into positive zones otherwise you will need to fix the Terrain X and
Terrain Z values that moved into the negative zone.)


Using Your Map
==============
When you save your map by pressing S (or s), Ganesha will write any files you're currently working on to the disk. It will not ask
you where to save these file, it will simply overwrite the old files. You can see which files were written by looking at Ganesha's
console window. This will help you identify which files you need to re-insert into the ISO in order to use your map.

While saving a file, Ganesha will check to see if the file's size, in CD sectors, is different than it was the last time Ganesha
opened or saved the file. If it is larger, a warning (e.g. "WARNING: File has grown from 18 sectors to 19 sectors!") will be printed
to the console. If it is smaller, a note (e.g. "Note: file has shrunk from 19 to 18 sectors") will be printed to the console.

If Ganesha warns you about the file having grown, then you have added too many new polygons to the map and you will not be able to
re-insert your file into the ISO without moving some files around. If you move files around on the ISO, you'll need to edit the
entries for those files in the appropriate GNS file with the new sector number and file size.

Use a tool like CDmage to insert your files into the ISO. Save a copy of your newly-patched ISO, load it up in a Playstation emulator,
and enjoy your modified map!
