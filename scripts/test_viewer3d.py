#!/usr/bin/env python
"""
Test script for the 3D viewer.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from packages.viewer3d import create_viewer
import time

def main():
    print("Creating 3D viewer...")
    viewer = create_viewer(title="Test 3D Viewer", width=1024, height=768)
    
    print("Starting viewer...")
    viewer.start(blocking=False)
    
    print("Waiting for viewer to initialize...")
    time.sleep(3)
    
    print("Setting isometric view...")
    viewer.set_view('iso')
    
    print("\nViewer is running!")
    print("Try the following commands:")
    print("  - Click view buttons in the viewer")
    print("  - Use mouse to orbit, pan, zoom")
    print("  - Toggle wireframe, grid, axes")
    print("\nPress Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        viewer.destroy()

if __name__ == "__main__":
    main()
