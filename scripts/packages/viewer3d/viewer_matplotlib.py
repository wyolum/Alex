"""
3D STL Viewer using matplotlib for tkinter integration.

This provides a working 3D viewer that can display STL files
directly in a tkinter window.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from stl import mesh as stl_mesh


class STLViewer3D(tk.Frame):
    """
    3D STL Viewer widget using matplotlib.
    
    Can be embedded in any tkinter window.
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the 3D viewer."""
        super().__init__(parent, **kwargs)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='#2c3e50')
        self.ax = self.figure.add_subplot(111, projection='3d', facecolor='#34495e')
        
        # Style the plot
        self.ax.set_xlabel('X', color='white')
        self.ax.set_ylabel('Y', color='white')
        self.ax.set_zlabel('Z', color='white')
        self.ax.tick_params(colors='white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add toolbar (optional - skip if it causes errors)
        try:
            toolbar = NavigationToolbar2Tk(self.canvas, self)
            toolbar.update()
        except Exception as e:
            print(f"Note: Toolbar not available ({e})")
            # Toolbar is optional - viewer still works without it
        
        # Store current mesh
        self.current_mesh = None
        
        # Show initial message
        self._show_empty_message()
    
    def _show_empty_message(self):
        """Show message when no model is loaded."""
        self.ax.clear()
        self.ax.text2D(0.5, 0.5, 'No model loaded\nUse "Reload Scene" to load your design',
                      transform=self.ax.transAxes,
                      ha='center', va='center',
                      fontsize=14, color='white',
                      bbox=dict(boxstyle='round', facecolor='#3498db', alpha=0.8))
        self.ax.set_xlabel('X', color='white')
        self.ax.set_ylabel('Y', color='white')
        self.ax.set_zlabel('Z', color='white')
        self.canvas.draw()
    
    def load_stl_file(self, filepath):
        """
        Load and display an STL file.
        
        Args:
            filepath: Path to STL file
        """
        try:
            # Load the STL file
            self.current_mesh = stl_mesh.Mesh.from_file(filepath)
            
            # Clear the plot
            self.ax.clear()
            
            # Get the mesh data
            vectors = self.current_mesh.vectors
            
            # Create the 3D polygon collection
            collection = Poly3DCollection(vectors, 
                                         alpha=0.9,
                                         facecolor='#3498db',
                                         edgecolor='#2c3e50',
                                         linewidths=0.5)
            
            self.ax.add_collection3d(collection)
            
            # Auto-scale to fit the mesh
            scale = self.current_mesh.points.flatten()
            self.ax.auto_scale_xyz(scale, scale, scale)
            
            # Set labels
            self.ax.set_xlabel('X (mm)', color='white', fontsize=10)
            self.ax.set_ylabel('Y (mm)', color='white', fontsize=10)
            self.ax.set_zlabel('Z (mm)', color='white', fontsize=10)
            
            # Style
            self.ax.tick_params(colors='white', labelsize=8)
            self.ax.grid(True, alpha=0.3)
            
            # Set background
            self.ax.set_facecolor('#34495e')
            self.figure.patch.set_facecolor('#2c3e50')
            
            # Draw
            self.canvas.draw()
            
            # Calculate stats
            num_triangles = len(vectors)
            bounds = self.current_mesh.points
            size_x = bounds[:, 0].max() - bounds[:, 0].min()
            size_y = bounds[:, 1].max() - bounds[:, 1].min()
            size_z = bounds[:, 2].max() - bounds[:, 2].min()
            
            print(f"✓ STL loaded: {num_triangles} triangles")
            print(f"  Size: {size_x:.1f} x {size_y:.1f} x {size_z:.1f} mm")
            
        except Exception as e:
            print(f"Error loading STL: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message
            self.ax.clear()
            self.ax.text2D(0.5, 0.5, f'Error loading STL:\n{str(e)}',
                          transform=self.ax.transAxes,
                          ha='center', va='center',
                          fontsize=12, color='white',
                          bbox=dict(boxstyle='round', facecolor='#e74c3c', alpha=0.8))
            self.canvas.draw()
    
    def set_view(self, view_name):
        """Set camera to a preset view."""
        if view_name == 'top':
            self.ax.view_init(elev=90, azim=0)
        elif view_name == 'front':
            self.ax.view_init(elev=0, azim=0)
        elif view_name == 'side':
            self.ax.view_init(elev=0, azim=90)
        elif view_name == 'iso':
            self.ax.view_init(elev=30, azim=45)
        
        self.canvas.draw()
    
    def reset_camera(self):
        """Reset to default isometric view."""
        self.set_view('iso')
    
    def fit_to_view(self):
        """Fit the model to the view."""
        if self.current_mesh is not None:
            scale = self.current_mesh.points.flatten()
            self.ax.auto_scale_xyz(scale, scale, scale)
            self.canvas.draw()
    
    def clear(self):
        """Clear the viewer."""
        self.current_mesh = None
        self._show_empty_message()


def create_viewer_widget(parent, **kwargs):
    """
    Create and return a new 3D STL viewer widget.
    
    Args:
        parent: Parent tkinter widget
        **kwargs: Additional frame arguments
    
    Returns:
        STLViewer3D instance
    """
    return STLViewer3D(parent, **kwargs)


# Test the viewer
if __name__ == "__main__":
    import sys
    
    root = tk.Tk()
    root.title("STL Viewer Test")
    root.geometry("1024x768")
    
    viewer = create_viewer_widget(root)
    viewer.pack(fill='both', expand=True)
    
    # Add control buttons
    button_frame = tk.Frame(root)
    button_frame.pack(fill='x', padx=5, pady=5)
    
    tk.Button(button_frame, text="Top", command=lambda: viewer.set_view('top')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Front", command=lambda: viewer.set_view('front')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Side", command=lambda: viewer.set_view('side')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Iso", command=lambda: viewer.set_view('iso')).pack(side='left', padx=2)
    tk.Button(button_frame, text="Fit", command=viewer.fit_to_view).pack(side='left', padx=2)
    tk.Button(button_frame, text="Clear", command=viewer.clear).pack(side='left', padx=2)
    
    # Load STL if provided
    if len(sys.argv) > 1:
        viewer.load_stl_file(sys.argv[1])
    
    root.mainloop()
