"""
View panel components for Alex CAD.
"""
import tkinter as tk
from typing import Optional, Callable
from PIL import ImageTk
from packages.constants import bgcolor


class ViewPanel:
    """A resizable view panel with canvas and control button"""
    
    def __init__(
        self, 
        parent: tk.Widget,
        name: str,
        width: int,
        height: int,
        button_image: Optional[ImageTk.PhotoImage] = None,
        button_command: Optional[Callable] = None,
        button_offset_x: int = 5,
        button_offset_y: int = 5
    ):
        """
        Create a view panel with canvas and button.
        
        Args:
            parent: Parent widget (typically a PanedWindow)
            name: Display name for the view (e.g., "Top", "Side")
            width: Initial canvas width
            height: Initial canvas height
            button_image: Optional image for the button
            button_command: Optional command for button click
            button_offset_x: X offset for button placement
            button_offset_y: Y offset for button placement
        """
        self.name = name
        self.frame = tk.Frame(parent, bg=bgcolor)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.frame, 
            width=width, 
            height=height, 
            bg=bgcolor
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create button
        button_kwargs = {
            'text': name,
            'bg': bgcolor
        }
        
        if button_image is not None:
            button_kwargs['image'] = button_image
            button_kwargs['compound'] = tk.RIGHT
            
        if button_command is not None:
            button_kwargs['command'] = button_command
            
        self.button = tk.Button(self.frame, **button_kwargs)
        self.button.place(x=button_offset_x, y=button_offset_y)
    
    def get_frame(self) -> tk.Frame:
        """Get the frame containing this panel"""
        return self.frame
    
    def get_canvas(self) -> tk.Canvas:
        """Get the canvas widget"""
        return self.canvas
