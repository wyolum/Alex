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
        # tkinterweb doesn't support JavaScript well enough for Three.js
        # So we'll show a message and offer to open in external viewer
        self.current_stl = filepath
        
        success_html = f"""
        <html>
        <head>
            <style>
                body {{
                    background: #2c3e50;
                    color: white;
                    font-family: 'Segoe UI', sans-serif;
                    padding: 40px;
                    text-align: center;
                }}
                h1 {{ color: #3498db; }}
                .success {{ color: #2ecc71; font-size: 48px; }}
                .info {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .path {{ font-family: monospace; font-size: 12px; color: #95a5a6; }}
            </style>
        </head>
        <body>
            <div class="success">✓</div>
            <h1>3D Model Ready!</h1>
            <div class="info">
                <p>Your design has been exported to STL format.</p>
                <p class="path">{filepath}</p>
            </div>
            <p>To view in 3D:</p>
            <ul style="text-align: left; max-width: 500px; margin: 20px auto;">
                <li>Open the STL file in your favorite 3D viewer (Blender, MeshLab, etc.)</li>
                <li>Or use an online viewer like viewstl.com</li>
                <li>The file will be automatically cleaned up after viewing</li>
            </ul>
            <p style="margin-top: 40px; color: #95a5a6; font-size: 12px;">
                Note: Full interactive 3D viewer coming soon!<br>
                (tkinterweb has limited JavaScript support for Three.js)
            </p>
        </body>
        </html>
        """
        
        try:
            self.html_frame.load_html(success_html)
            print(f"✓ STL file ready: {filepath}")
        except Exception as e:
            print(f"Error showing success message: {e}")
    
    def load_stl_data(self, stl_data):
        """Load STL data - not supported in this version."""
        print("load_stl_data: Not supported with tkinterweb")
    
    def set_view(self, view_name):
        """Set view - not supported in this version."""
        print(f"set_view({view_name}): Not supported with tkinterweb")
    
    def reset_camera(self):
        """Reset camera - not supported in this version."""
        print("reset_camera: Not supported with tkinterweb")
    
    def fit_to_view(self):
        """Fit to view - not supported in this version."""
        print("fit_to_view: Not supported with tkinterweb")
    
    def clear(self):
        """Clear the viewer."""
        self._load_viewer()


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
