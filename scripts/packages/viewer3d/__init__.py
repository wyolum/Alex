"""
Three.js 3D Viewer package for AlexCAD.

Provides interactive 3D visualization using Three.js.
- viewer.py: Standalone pywebview version (requires GTK/Qt)
- viewer_tk.py: Tkinter-embedded version (recommended for AlexCAD)
"""

from .viewer import Viewer3D, create_viewer
from .viewer_tk import Viewer3DTk, create_viewer_widget

__all__ = ['Viewer3D', 'create_viewer', 'Viewer3DTk', 'create_viewer_widget']
__version__ = '1.0.0'
