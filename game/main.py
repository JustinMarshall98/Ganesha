#!/usr/bin/python
# coding: utf-8

# Ganesha
# a Final Fantasy Tactics Map Editor
# Don Laursen, 2009

map_viewer = None
try:
    import os
    import sys

    from ganesha.ui import Map_Viewer

    try:
        gns_path = sys.argv[1]
    except IndexError:
        gns_path = None

    map_viewer = Map_Viewer()
    map_viewer.start(gns_path)
except:
    if map_viewer is not None:
        if hasattr(map_viewer, "showbase"):
            map_viewer.showbase.destroy()
    import traceback

    print()
    print("ERROR:")
    traceback.print_exc()
    input("Press Enter to continue.")
