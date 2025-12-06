"""
Configuration constants for Alex CAD views.
"""

class ViewConfig:
    """Configuration for view panels and layout"""
    # Default canvas dimensions
    DEFAULT_WIDTH = 500
    DEFAULT_HEIGHT = 400
    
    # PanedWindow settings
    SASH_WIDTH = 5
    
    # Button positioning
    BUTTON_OFFSET_X = 5
    BUTTON_OFFSET_Y = 5
    
    # Resize debouncing
    RESIZE_DEBOUNCE_MS = 50
    
    # View scale
    DEFAULT_SCALE = 1.0
    
    # Iso view angles (in radians, will be multiplied by DEG)
    ISO_THETA = 240  # degrees
    ISO_PHI = 35     # degrees
