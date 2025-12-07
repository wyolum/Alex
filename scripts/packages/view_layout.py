"""
View layout creation for Alex CAD.
"""
import tkinter as tk
from tkinter import ttk
from typing import Tuple, Dict
from PIL import Image, ImageTk
import numpy as np
import os

from packages import isometric_view as iv
from packages.view_panel import ViewPanel
from packages.view_config import ViewConfig
from packages.constants import bgcolor, DEG

# Get the base directory for resources
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
resources_dir = os.path.join(base_dir, 'resources')


def load_rotation_images() -> Dict[str, ImageTk.PhotoImage]:
    """Load rotation button images"""
    return {
        'base': ImageTk.PhotoImage(Image.open(os.path.join(resources_dir, 'rt_angle.png'))),
        'yaw': ImageTk.PhotoImage(Image.open(os.path.join(resources_dir, 'rt_angle_yaw.png'))),
        'pitch': ImageTk.PhotoImage(Image.open(os.path.join(resources_dir, 'rt_angle_pitch.png'))),
        'roll': ImageTk.PhotoImage(Image.open(os.path.join(resources_dir, 'rt_angle_roll.png')))
    }


def create_paned_structure(root: tk.Tk) -> Tuple[tk.PanedWindow, tk.PanedWindow, tk.PanedWindow]:
    """
    Create the PanedWindow structure for resizable panels.
    
    Returns:
        Tuple of (main_paned, left_paned, right_paned)
    """
    # Main horizontal split (left/right)
    main_paned = tk.PanedWindow(
        root, 
        orient=tk.HORIZONTAL, 
        sashwidth=ViewConfig.SASH_WIDTH, 
        bg=bgcolor
    )
    main_paned.grid(row=1, column=3, rowspan=10, columnspan=3, sticky="nsew")
    
    # Configure root grid to expand
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(3, weight=1)
    
    # Left vertical split (Top and Front views)
    left_paned = tk.PanedWindow(
        main_paned, 
        orient=tk.VERTICAL, 
        sashwidth=ViewConfig.SASH_WIDTH, 
        bg=bgcolor
    )
    
    # Right vertical split (Iso and Side views)
    right_paned = tk.PanedWindow(
        main_paned, 
        orient=tk.VERTICAL, 
        sashwidth=ViewConfig.SASH_WIDTH, 
        bg=bgcolor
    )
    
    # Add panes to main window
    main_paned.add(left_paned, stretch="always")
    main_paned.add(right_paned, stretch="always")
    
    # Add separator between sidebar and views
    ttk.Separator(root, orient=tk.VERTICAL).grid(
        column=2, row=0, rowspan=10, sticky='ns'
    )
    
    return main_paned, left_paned, right_paned


def create_view_layout(
    root: tk.Tk,
    sidebar,
    rotate_yaw,
    rotate_pitch,
    rotate_roll,
    shift_key,
    control_key
) -> Tuple[iv.Views, Dict[str, ImageTk.PhotoImage]]:
    """
    Create the complete view layout with 4 resizable panels.
    
    Args:
        root: Root Tk window
        sidebar: Sidebar widget
        rotate_yaw: Callback for yaw rotation
        rotate_pitch: Callback for pitch rotation
        rotate_roll: Callback for roll rotation
        shift_key: Shift key tracker
        control_key: Control key tracker
        
    Returns:
        Tuple of (views, images) where views is an iv.Views object
        and images is a dict of loaded images
    """
    # Load images
    images = load_rotation_images()
    
    # Create PanedWindow structure
    main_paned, left_paned, right_paned = create_paned_structure(root)
    
    # Create view panels
    top_panel = ViewPanel(
        left_paned,
        "Top",
        ViewConfig.DEFAULT_WIDTH,
        ViewConfig.DEFAULT_HEIGHT,
        images['yaw'],
        rotate_yaw,
        ViewConfig.BUTTON_OFFSET_X,
        ViewConfig.BUTTON_OFFSET_Y
    )
    
    front_panel = ViewPanel(
        left_paned,
        "Front",
        ViewConfig.DEFAULT_WIDTH,
        ViewConfig.DEFAULT_HEIGHT,
        images['pitch'],
        rotate_pitch,
        ViewConfig.BUTTON_OFFSET_X,
        ViewConfig.BUTTON_OFFSET_Y
    )
    
    iso_panel = ViewPanel(
        right_paned,
        "Iso",
        ViewConfig.DEFAULT_WIDTH,
        ViewConfig.DEFAULT_HEIGHT,
        None,  # No image for iso button
        None,  # No command for iso button
        ViewConfig.BUTTON_OFFSET_X,
        ViewConfig.BUTTON_OFFSET_Y
    )
    
    side_panel = ViewPanel(
        right_paned,
        "Side",
        ViewConfig.DEFAULT_WIDTH,
        ViewConfig.DEFAULT_HEIGHT,
        images['roll'],
        rotate_roll,
        ViewConfig.BUTTON_OFFSET_X,
        ViewConfig.BUTTON_OFFSET_Y
    )
    
    # Add panels to paned windows
    left_paned.add(top_panel.get_frame(), stretch="always")
    left_paned.add(front_panel.get_frame(), stretch="always")
    right_paned.add(iso_panel.get_frame(), stretch="always")
    right_paned.add(side_panel.get_frame(), stretch="always")
    
    # Create IsoView objects
    ihat, jhat, khat = np.eye(3)
    step_var = sidebar.step_var
    
    initial_offset = [
        ViewConfig.DEFAULT_WIDTH / 2,
        ViewConfig.DEFAULT_HEIGHT / 2
    ]
    
    top = iv.IsoView(
        top_panel.get_canvas(),
        ihat,
        -jhat,
        initial_offset,
        step_var,
        sidebar.x_var,
        sidebar.y_var,
        sidebar.z_var,
        shift_key=shift_key,
        control_key=control_key,
        scale=ViewConfig.DEFAULT_SCALE
    )
    
    front = iv.IsoView(
        front_panel.get_canvas(),
        ihat,
        -khat,
        initial_offset,
        step_var,
        sidebar.x_var,
        sidebar.y_var,
        sidebar.z_var,
        shift_key=shift_key,
        control_key=control_key,
        scale=ViewConfig.DEFAULT_SCALE
    )
    
    side = iv.IsoView(
        side_panel.get_canvas(),
        jhat,
        -khat,
        initial_offset,
        step_var,
        sidebar.x_var,
        sidebar.y_var,
        sidebar.z_var,
        shift_key=shift_key,
        control_key=control_key,
        scale=ViewConfig.DEFAULT_SCALE
    )
    
    # Create iso view with theta/phi angles
    theta = ViewConfig.ISO_THETA * DEG
    phi = ViewConfig.ISO_PHI * DEG
    
    iso = iv.from_theta_phi(
        theta,
        phi,
        iso_panel.get_canvas(),
        initial_offset,
        step_var,
        sidebar.x_var,
        sidebar.y_var,
        sidebar.z_var,
        ViewConfig.DEFAULT_SCALE,
        shift_key=shift_key,
        control_key=control_key
    )
    
    views = iv.Views([top, side, front, iso])
    
    return views, images
