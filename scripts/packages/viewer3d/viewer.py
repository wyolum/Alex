"""
Three.js 3D Viewer for AlexCAD using pywebview.

This module provides a 3D visualization window using Three.js
for interactive viewing of AlexCAD designs.
"""

import os
import webview
import threading
import tempfile
import base64
from pathlib import Path


class Viewer3DAPI:
    """API for communication between Python and JavaScript."""
    
    def __init__(self, viewer):
        self.viewer = viewer
    
    def on_screenshot(self, data_url):
        """Handle screenshot from JavaScript."""
        # Remove data URL prefix
        if ',' in data_url:
            data_url = data_url.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(data_url)
        
        # Save to file
        filename = 'alexcad_3d_screenshot.png'
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        print(f"Screenshot saved to {filename}")
        return filename
    
    def on_part_clicked(self, part_id):
        """Handle part click from JavaScript."""
        print(f"Part clicked: {part_id}")
        if self.viewer.on_part_click_callback:
            self.viewer.on_part_click_callback(part_id)


class Viewer3D:
    """
    Three.js 3D Viewer window.
    
    Provides an interactive 3D visualization of AlexCAD designs
    using Three.js in a webview window.
    """
    
    def __init__(self, title="AlexCAD 3D Viewer", width=800, height=600):
        """
        Initialize the 3D viewer.
        
        Args:
            title: Window title
            width: Window width in pixels
            height: Window height in pixels
        """
        self.title = title
        self.width = width
        self.height = height
        self.window = None
        self.api = Viewer3DAPI(self)
        self.on_part_click_callback = None
        
        # Get path to HTML file
        current_dir = Path(__file__).parent
        self.html_path = current_dir / 'index.html'
        
        if not self.html_path.exists():
            raise FileNotFoundError(f"Viewer HTML not found: {self.html_path}")
    
    def create_window(self):
        """
        Create the webview window (must be called before start).
        """
        self.window = webview.create_window(
            title=self.title,
            url=str(self.html_path),
            width=self.width,
            height=self.height,
            resizable=True,
            js_api=self.api
        )
        return self.window
    
    def start(self, debug=False):
        """
        Start the webview (blocking call - must be on main thread).
        
        Args:
            debug: Enable debug mode
        """
        if not self.window:
            raise RuntimeError("Must call create_window() before start()")
        
        webview.start(debug=debug)
    
    def load_stl_file(self, filepath):
        """
        Load an STL file into the viewer.
        
        Args:
            filepath: Path to STL file
        """
        if not self.window:
            print("Warning: Viewer window not created yet")
            return
        
        # Convert to absolute path
        filepath = os.path.abspath(filepath)
        
        # Use file:// URL for local files
        file_url = f"file://{filepath}"
        
        # Call JavaScript function
        self.window.evaluate_js(f"window.viewer.loadSTL('{file_url}')")
    
    def load_stl_data(self, stl_data):
        """
        Load STL data directly into the viewer.
        
        Args:
            stl_data: Binary STL data
        """
        if not self.window:
            print("Warning: Viewer window not created yet")
            return
        
        # Encode as base64
        encoded = base64.b64encode(stl_data).decode('utf-8')
        
        # Call JavaScript function
        js_code = f"""
        (function() {{
            const data = atob('{encoded}');
            const bytes = new Uint8Array(data.length);
            for (let i = 0; i < data.length; i++) {{
                bytes[i] = data.charCodeAt(i);
            }}
            window.viewer.loadSTLData(bytes.buffer);
        }})();
        """
        self.window.evaluate_js(js_code)
    
    def set_view(self, view_name):
        """
        Set camera to a preset view.
        
        Args:
            view_name: One of 'top', 'front', 'side', 'iso'
        """
        if not self.window:
            return
        
        self.window.evaluate_js(f"window.viewer.setView('{view_name}')")
    
    def reset_camera(self):
        """Reset camera to default position."""
        if not self.window:
            return
        
        self.window.evaluate_js("window.viewer.resetCamera()")
    
    def fit_to_view(self):
        """Fit the model to the view."""
        if not self.window:
            return
        
        self.window.evaluate_js("window.viewer.fitToView()")
    
    def clear(self):
        """Clear all models from the scene."""
        if not self.window:
            return
        
        self.window.evaluate_js("window.viewer.clearModels()")
    
    def set_part_click_callback(self, callback):
        """
        Set callback for part click events.
        
        Args:
            callback: Function to call when part is clicked
        """
        self.on_part_click_callback = callback
    
    def destroy(self):
        """Close the viewer window."""
        if self.window:
            self.window.destroy()
            self.window = None


# Convenience function
def create_viewer(title="AlexCAD 3D Viewer", width=800, height=600):
    """
    Create and return a new 3D viewer instance.
    
    Args:
        title: Window title
        width: Window width
        height: Window height
    
    Returns:
        Viewer3D instance
    """
    return Viewer3D(title, width, height)


# Example usage
if __name__ == "__main__":
    # Create viewer
    viewer = create_viewer(width=1024, height=768)
    
    # Create window
    viewer.create_window()
    
    # You can load an STL file before starting
    # viewer.load_stl_file("path/to/your/model.stl")
    
    # Start viewer (blocking - will run until window is closed)
    print("Starting viewer... Close the window to exit.")
    viewer.start()
    print("Viewer closed.")
