"""
Three.js 3D Viewer package for AlexCAD.

Provides interactive 3D visualization using matplotlib (works!) or Three.js (future).
- viewer.py: Standalone pywebview version (requires GTK/Qt)
- viewer_tk.py: Tkinter-embedded version with tkinterweb (limited JS support)
- viewer_matplotlib.py: Matplotlib 3D viewer (WORKING! - recommended)
"""

from .viewer import Viewer3D, create_viewer
from .viewer_matplotlib import STLViewer3D, create_viewer_widget

# Use matplotlib viewer by default (it actually works!)
__all__ = ['Viewer3D', 'create_viewer', 'STLViewer3D', 'create_viewer_widget']
__version__ = '1.0.0'
