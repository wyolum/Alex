"""
Three.js 3D Viewer for AlexCAD using tkinterweb.

This module provides a 3D visualization widget that can be embedded
in tkinter windows.
"""

import tkinter as tk
from tkinterweb import HtmlFrame
import os
import base64
from pathlib import Path


class Viewer3DTk(tk.Frame):
    """
    Three.js 3D Viewer widget for tkinter.
    
    Can be embedded in any tkinter window as a frame.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the 3D viewer widget.
        
        Args:
            parent: Parent tkinter widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        # Get path to HTML file
        current_dir = Path(__file__).parent
        self.html_path = current_dir / 'index.html'
        
        if not self.html_path.exists():
            raise FileNotFoundError(f"Viewer HTML not found: {self.html_path}")
        
        # Create HTML frame
        self.html_frame = HtmlFrame(self, messages_enabled=False)
        self.html_frame.pack(fill='both', expand=True)
        
        # Load the viewer HTML
        self._load_viewer()
    
    def _load_viewer(self):
        """Load the Three.js viewer HTML."""
        try:
            with open(self.html_path, 'r') as f:
                html_content = f.read()
            
            # Load the HTML
            self.html_frame.load_html(html_content)
            print("3D Viewer loaded successfully")
        except Exception as e:
            print(f"Error loading viewer: {e}")
            # Show error message in the frame
            error_html = f"""
            <html>
            <body style="background: #2c3e50; color: white; font-family: sans-serif; padding: 20px;">
                <h2>❌ Error Loading 3D Viewer</h2>
                <p>{str(e)}</p>
                <p>HTML Path: {self.html_path}</p>
            </body>
            </html>
            """
            self.html_frame.load_html(error_html)
    
    def load_stl_file(self, filepath):
        """
        Load an STL file into the viewer.
        
        Args:
            filepath: Path to STL file
        """
        # Convert to absolute path and file URL
        filepath = os.path.abspath(filepath)
        file_url = f"file://{filepath}"
        
        # Execute JavaScript
        js_code = f"window.viewer.loadSTL('{file_url}')"
        try:
            self.html_frame.evaluate_javascript(js_code)
        except Exception as e:
            print(f"Error loading STL: {e}")
    
    def load_stl_data(self, stl_data):
        """
        Load STL data directly into the viewer.
        
        Args:
            stl_data: Binary STL data
        """
        # Encode as base64
        encoded = base64.b64encode(stl_data).decode('utf-8')
        
        # Execute JavaScript
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
        try:
            self.html_frame.evaluate_javascript(js_code)
        except Exception as e:
            print(f"Error loading STL data: {e}")
    
    def set_view(self, view_name):
        """
        Set camera to a preset view.
        
        Args:
            view_name: One of 'top', 'front', 'side', 'iso'
        """
        js_code = f"window.viewer.setView('{view_name}')"
        try:
            self.html_frame.evaluate_javascript(js_code)
        except Exception as e:
            print(f"Error setting view: {e}")
    
    def reset_camera(self):
        """Reset camera to default position."""
        try:
            self.html_frame.evaluate_javascript("window.viewer.resetCamera()")
        except Exception as e:
            print(f"Error resetting camera: {e}")
    
    def fit_to_view(self):
        """Fit the model to the view."""
        try:
            self.html_frame.evaluate_javascript("window.viewer.fitToView()")
        except Exception as e:
            print(f"Error fitting to view: {e}")
    
    def clear(self):
        """Clear all models from the scene."""
        try:
            self.html_frame.evaluate_javascript("window.viewer.clearModels()")
        except Exception as e:
            print(f"Error clearing models: {e}")


# Convenience function
def create_viewer_widget(parent, **kwargs):
    """
    Create and return a new 3D viewer widget.
    
    Args:
        parent: Parent tkinter widget
        **kwargs: Additional frame arguments
    
    Returns:
        Viewer3DTk instance
    """
    return Viewer3DTk(parent, **kwargs)


# Example usage
if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    root.title("AlexCAD 3D Viewer Test")
    root.geometry("1024x768")
    
    # Create viewer widget
    viewer = create_viewer_widget(root)
    viewer.pack(fill='both', expand=True)
    
    # Add control buttons
    button_frame = tk.Frame(root)
    button_frame.pack(fill='x', padx=5, pady=5)
    
    tk.Button(button_frame, text="Top View", command=lambda: viewer.set_view('top')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Front View", command=lambda: viewer.set_view('front')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Side View", command=lambda: viewer.set_view('side')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Iso View", command=lambda: viewer.set_view('iso')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Reset Camera", command=viewer.reset_camera).pack(side='left', padx=2)
    tk.Button(button_frame, text="Fit to View", command=viewer.fit_to_view).pack(side='left', padx=2)
    tk.Button(button_frame, text="Clear", command=viewer.clear).pack(side='left', padx=2)
    
    # Run
    print("Starting tkinter 3D viewer...")
    root.mainloop()
