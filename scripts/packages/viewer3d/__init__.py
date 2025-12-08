"""
Three.js 3D Viewer package for AlexCAD.

Provides interactive 3D visualization using Three.js in a webview.
"""

from .viewer import Viewer3D, create_viewer

__all__ = ['Viewer3D', 'create_viewer']
__version__ = '1.0.0'
