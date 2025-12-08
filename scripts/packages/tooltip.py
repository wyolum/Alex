"""
Tooltip utility for tkinter widgets.

Provides a simple way to add tooltips (hover text) to tkinter widgets.
"""

import tkinter as tk


class ToolTip:
    """
    Create a tooltip for a given widget.
    
    Usage:
        button = tk.Button(root, text="Click me")
        ToolTip(button, "This button does something cool!")
    """
    
    def __init__(self, widget, text, delay=500):
        """
        Initialize the tooltip.
        
        Args:
            widget: The tkinter widget to attach the tooltip to
            text: The tooltip text to display
            delay: Delay in milliseconds before showing tooltip (default: 500)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.schedule_id = None
        
        # Bind events
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Button>", self.on_leave)  # Hide on click
    
    def on_enter(self, event=None):
        """Mouse entered widget - schedule tooltip display."""
        self.schedule_tooltip()
    
    def on_leave(self, event=None):
        """Mouse left widget - cancel and hide tooltip."""
        self.cancel_tooltip()
        self.hide_tooltip()
    
    def schedule_tooltip(self):
        """Schedule the tooltip to appear after delay."""
        self.cancel_tooltip()
        self.schedule_id = self.widget.after(self.delay, self.show_tooltip)
    
    def cancel_tooltip(self):
        """Cancel scheduled tooltip."""
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
    
    def show_tooltip(self):
        """Display the tooltip."""
        if self.tooltip_window or not self.text:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip label with styling
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",  # Light yellow background
            foreground="#000000",  # Black text
            relief=tk.SOLID,
            borderwidth=1,
            font=("sans-serif", 10, "normal"),
            padx=5,
            pady=3
        )
        label.pack()
    
    def hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_tooltip(widget, text, delay=500):
    """
    Convenience function to add a tooltip to a widget.
    
    Args:
        widget: The tkinter widget
        text: The tooltip text
        delay: Delay before showing (default: 500ms)
    
    Returns:
        The ToolTip instance
    """
    return ToolTip(widget, text, delay)
