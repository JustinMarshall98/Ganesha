#!/usr/bin/env python3

import sys
import os
from ganesha.ui import Map_Viewer


def main():
    map_path = None
    if len(sys.argv) > 1:
        map_path = sys.argv[1]
        _, ext = os.path.splitext(map_path)
        if ext.lower() != ".gns":
            print("File type must be GSN")
            sys.exit()

    map_viewer = Map_Viewer()
    map_viewer.start(map_path)


if __name__ == "__main__":
    main()
