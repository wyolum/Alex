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
    
    print("Creating viewer window...")
    viewer.create_window()
    
    print("\nViewer window created!")
    print("The viewer will open in a new window.")
    print("\nTry the following:")
    print("  - Click view buttons (Top, Front, Side, Iso)")
    print("  - Use mouse to orbit, pan, zoom")
    print("  - Toggle wireframe, grid, axes")
    print("  - Take screenshots")
    print("\nClose the window to exit.")
    
    # Start viewer (blocking - will run until window is closed)
    viewer.start()
    
    print("Viewer closed.")

if __name__ == "__main__":
    main()
