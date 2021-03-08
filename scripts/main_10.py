'''
Refactor with extracted librarries:
-- constants
-- parts_db
-- things
-- wireframes
-- isometric_views
-- util
# -- add control-z undo (complete!)
# -- add look before you leap alighment

scene is a group that has a view (or grouped views) and a "selected" subgroup


###
# TODO
# -- add tool tips
'''

try:
    from stl import mesh
    STL_SUPPORTED = True
except ImportError:
    STL_SUPPORTED = False
    print('''\
numpy-stl required for stl imports
    > pip install numpy-stl # or
    > const install numpy-stl
    ''')
    raise

import sys
import pickle
import argparse
import warnings
warnings.simplefilter("error")

from tkinter import filedialog
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image

import numpy as np
from numpy import sin, cos, sqrt

from packages import quaternion
from packages import interpolate
from packages.constants import mm, inch, DEG, units, bgcolor
from packages import parts_db
from packages import util
from packages import wireframes
from packages import things
from packages import isometric_view as iv


parser = argparse.ArgumentParser(description='ALuminum EXtrusion CAD program.')
parser.add_argument('filename', nargs='?', default=None, type=str)
parser.add_argument('-W', '--width', default=None, type=int)
parser.add_argument('-H', '--height', default=None, type=int)
parser.add_argument('-Z', '--zoom_buttons', nargs='?', default=False, type=util.str2bool)
args = parser.parse_args()

### Global singletons
alex_filename = [] ### use as mutable string
STEP = [5]          ### use as mutable int

selected = things.Selected()

def NumericalEntry(parent, label, onchange, from_=-1e6, to=1e6, values=None, increment=1,
                   var_factory=tk.DoubleVar):
    frame = tk.Frame(parent)
    var = var_factory()
    var.trace("w", onchange)
    if var_factory == tk.BooleanVar:
        entry = tk.Checkbutton(frame, text='', variable=var)
    else:
        if values is None:
            entry = tk.Spinbox(frame, from_=from_, to=to, textvariable=var, increment=increment, width=5)
        else:
            entry = tk.Spinbox(frame, values=values, textvariable=var, increment=increment, width=5)
        
    label = tk.Label(frame, text=label)
    label.grid(row=1, column=1)
    entry.grid(row=1, column=2)
    return frame, entry, var


################################################################################
## Callbacks
################################################################################


def get_view_under_mouse(event):
    x, y = event.x, event.y
    winxy = np.array([root.winfo_rootx(), root.winfo_rooty()])
    for i, view in enumerate(views):
        can = view.can
        x0, y0 = np.array([can.winfo_rootx(), can.winfo_rooty()]) - winxy
        x1 = x0 + can.winfo_width()
        y1 = y0 + can.winfo_height()
        if x0 <= x <= x1 and y0 <= y <= y1:
            out = view
            delta_xy = x - x0, y - y0
            break
    else:
        out = None
        delta_xy = None
    return out, delta_xy

def OnMouseWheel(event):
    view_under_mouse, delta_xy = get_view_under_mouse(event)
    if view_under_mouse:
        delta_xyz = view_under_mouse.invert_2d(delta_xy)
        for i in range(event.delta):
            zoom_in(delta_xyz)
        for i in range(-event.delta):
            zoom_out(delta_xyz)
            
def get_widget_under_mouse(root):
    x,y = root.winfo_pointerxy()
    widget = root.winfo_containing(x,y)
    return widget
    
def OnMouseButton4_5(event):
    if event.num == 4:
        event.delta = 1
    else:
        event.delta = -1
    wid = get_widget_under_mouse(root)
    for view in views:
        if view.can == wid:
            delta_xy = event.x, event.y
            delta_xyz = view.invert_2d(delta_xy)
            for i in range(event.delta):
                zoom_in(delta_xyz)
            for i in range(-event.delta):
                zoom_out(delta_xyz)
            break

def mouse_in_views():
    return str(get_widget_under_mouse(root)) == '.!canvas'

def export(*args):
    scene.export()
def export_cb(*args):
    alex_set_titlebar()
def slew_left(*args):
    if mouse_in_views():
        delta = np.array([-10, 0, 0])
        views.slew(delta)
def slew_right(*args):
    if mouse_in_views():
        delta = np.array([10, 0, 0])
        views.slew(delta)
def slew_up(*args):
    if mouse_in_views():
        delta = np.array([0, 0, 10])
        views.slew(delta)
def slew_down(*args):
    if mouse_in_views():
        delta = np.array([0, 0, -10])
        views.slew(delta)
def slew_back(*args):
    if mouse_in_views():
        delta = np.array([0, 10, 0])
        views.slew(delta)
def slew_forward(*args):
    if mouse_in_views():
        delta = np.array([0, -10, 0])
        views.slew(delta)

def cancel(*args):
    unselect_all()
    sidebar.new_part_button.focus_set()
    #iso_button.focus_set()
    #isocan.focus_set()
    
def toggle_axes(*args):
    views.toggle_axes()
    
def select_all(*args):
    for thing in scene:
        if thing not in scene.selected:
            scene.selected.append(thing)
            thing.render(views, selected=True)
        
def dup_selected(*args):
    if len(selected) > 0:
        util.register_undo()
    for thing in scene.selected.ungroup():
        thing.render(views, selected=False)
        scene.append(thing.dup(), select=True)
    
def delete_selected(*args):
    if len(selected) > 0:
        util.register_undo()
    for thing in scene.selected.ungroup():
        views.erase(thing)
        scene.remove(thing)
def group_selected(*args):
    if len(scene.selected) < 2:
        pass
    else:
        util.register_undo()
        out = things.Group()
        for thing in scene.selected.ungroup():
            scene.remove(thing)
            out.append(thing)
        scene.append(out)
        scene.selected.append(out)
        out.render(views, selected=True)

def ungroup_selected(*args):
    if len(selected) > 0:
        util.register_undo()
    for thing in scene.selected.ungroup():
        thing.render(views, selected=False)
        if thing.iscontainer():
            group = thing
            scene.remove(group) ## replace group with its constituents
            for thing in group.ungroup():
                scene.append(thing)

def rotate_roll():
    if len(selected) > 0:
        util.register_undo()
    if control_key.pressed():
        rt_angles = .5
    else:
        rt_angles = 1
    selected.rotate(roll=rt_angles)
    selected.render(views, selected=True)
    export()
def rotate_pitch():
    if len(selected) > 0:
        util.register_undo()
    if control_key.pressed():
        rt_angles = .5
    else:
        rt_angles = 1
    selected.rotate(pitch=rt_angles)
    selected.render(views, selected=True)
    export()
def rotate_yaw():
    if len(selected) > 0:
        util.register_undo()
    if control_key.pressed():
        rt_angles = .5
    else:
        rt_angles = 1
    selected.rotate(yaw=rt_angles)
    selected.render(views, selected=True)
    export()
    
def zoom_in(mouse_xyz=None, amt=.9):
    views.set_scale(views.get_scale() / amt, mouse_xyz)
def zoom_out(mouse_xyz=None, amt=.9):
    views.set_scale(views.get_scale() * amt, mouse_xyz)
def zoom_in_lots():
    zoom_in(amt=.8)
def zoom_out_lots():
    zoom_out(amt=.8)

def zoom_fit_selected(ignored=None):
    verts = scene.selected.get_verts()
    if len(verts) > 0:
        window_dims = np.array([top.can.winfo_width(),
                                top.can.winfo_height(),
                                front.can.winfo_height()])
        
        wfxy = top.project_2d(verts)
        wfz = front.project_2d(verts)[:,1]
        wfxyz = np.column_stack([wfxy, wfz])

        d = np.max(wfxyz, axis=0) - np.min(wfxyz, axis=0)
        D = .75 * np.min(window_dims / d)
        views.set_scale(D * top.scale)
        
        m3 = (np.max(verts, axis=0) + np.min(verts, axis=0)) / 2
        c2_top = window_dims[:2] / 2
        c2_front = window_dims[1::2] / 2
        offset_new_top = c2_top - m3 @ top.B * top.scale
        offset_new_front = c2_front - m3 @ front.B * front.scale
        delta_xy = offset_new_top - top.offset
        delta_z = (offset_new_front - front.offset)[1]

        # print(offset_new_top, top.offset, delta_xy)
        views.slew(top.B @ delta_xy + front.B @ [0, delta_z])
def flip_z_selected(ignored=None):
    selected.mirror([0, 0, 1])
    selected.render(views, selected=True)
def select(part):
    scene.selected.append(part)
    part.render(scene.view, selected=True)
def unselect_all():
    if 'scene' in globals():
        for part in scene.selected.ungroup():
            part.render(scene.view, selected=False)
    


def CornerTwoWay(d1):
    name = f"{d1:.0f}{d1:.0f} Corner Two Way"
    return parts_db.Part(name)

def CornerThreeWay(d1):
    name = f"{d1:.0f}{d1:.0f} Corner Three Way"
    return parts_db.Part(name)

@util.undoable
def createCornerTwoWay():
    d1 = sidebar.dim1_var.get()
    part = CornerTwoWay(d1)
    unselect_all()
    scene.append(part, select=True)
    
@util.undoable
def createCornerThreeWay():
    d1 = sidebar.dim1_var.get()
    part = CornerThreeWay(d1)
    unselect_all()
    scene.append(part, select=True)

def parts_db_dialog():
    def select_cb(part):
        part.set_length(sidebar.length_var.get())
        unselect_all()
        scene.append(part, select=True)
    parts_db.PartDialog(root, select_cb)

def new_part_dialog():
    parts_db.new_part_dialog(root)
    
def Alex(length, d1, d2):
    return parts_db.Part(f"{d1:.0f}{d2:.0f} Alex", length)

@util.undoable
def createAlex(*args):
    unselect_all()
    
    try:
        length = max([0, sidebar.length_var.get()])
    except tk.TclError:
        length = 100
        sidebar.length_var.set(length)
    d1 = np.max([20, sidebar.dim1_var.get()])
    d2 = np.max([20, sidebar.dim2_var.get()])

    #x = sidebar.x_var.get()
    #y = sidebar.y_var.get()
    #z = sidebar.z_var.get()
    part = Alex(length, d1, d2)
    #part.translate([x, y, z])
    scene.append(part, select=True)
    print(part.pos)
    
def noop(*args, **kw):
    pass

def render(thing):
    selected = thing in scene.selected
    thing.render(views, selected=selected)
    
################################################################################
## GUI ELEMENTS
################################################################################
def ImageButton(parent, png, command):
    img = ImageTk.PhotoImage(Image.open(png))
    button = tk.Button(parent, image=img, command=command, width=50)
    button.img = img
    return button

def AlignmentButton(parent, png, command):
    button = ImageButton(parent, png, command)
    return button

def center_selected(axis):
    sel = scene.selected
    if len(sel) > 1:
        util.register_undo()
        verts = sel[-1].get_verts()
        ref = (np.max(verts[:,axis], axis=0) + np.min(verts[:,axis], axis=0))/2
        for part in sel[:-1]:
            verts = part.get_verts()
            center = (np.max(verts[:,axis], axis=0) + np.min(verts[:,axis], axis=0)) / 2
            v = np.zeros(3)
            v[axis] = ref - center
            part.translate(v)
            part.render(views, selected=True)
        export()
    
def abut_selected(axis, dir=1):
    sel = scene.selected
    if dir == 1:
        max = np.max
        min = np.min
    else:
        min = np.max
        max = np.min
        
    if len(sel) > 1:
        util.register_undo()
        ref = max(sel[-1].get_verts()[:,axis], axis=0)
        for part in sel[:-1]:
            verts = part.get_verts()
            left = min(verts[:,axis], axis=0)
            v = np.zeros(3)
            v[axis] = ref - left
            part.translate(v)
            part.render(views, selected=True)
        export()

def flush_selected(axis, dir):
    if dir == 1:
        min = np.min
    else:
        min = np.max
    sel = scene.selected
    if len(sel) > 1:
        util.register_undo()
        ref = min(sel[-1].get_verts()[:,axis], axis=0)
        for part in sel[:-1]:
            verts = part.get_verts()
            left = min(verts[:,axis], axis=0)
            v = np.zeros(3)
            v[axis] = ref - left
            part.translate(v)
            part.render(views, selected=True)
        export()
            
def x_abut_selected():
    abut_selected(0, 1)
def x_abut_right_selected():
    abut_selected(0, -1)
def x_center_selected():
    center_selected(0)
def x_flush_selected():
    flush_selected(0, 1)
def x_flush_left_selected():
    flush_selected(0, -1)

def y_abut_selected():
    abut_selected(1, 1)
def y_abut_back_selected():
    abut_selected(1, -1)
def y_center_selected():
    center_selected(1)
def y_flush_selected():
    flush_selected(1, 1)
def y_flush_back_selected():
    flush_selected(1, -1)
    
def z_abut_selected():
    abut_selected(2, 1)
def z_abut_top_selected():
    abut_selected(2, -1)
def z_center_selected():
    center_selected(2)
def z_flush_selected():
    flush_selected(2, 1)
def z_flush_top_selected():
    flush_selected(2, -1)

def highlight_last_selected(event):
    #print("len(scene.selected)", len(scene.selected))
    if len(scene.selected) > 0:
        scene.view.highlight_part(scene.selected[-1], 'red')

def unhighlight_last_selected(event):
    scene.view.erase("highlight")

def TranslatePanel(parent):
    frame = tk.Frame(parent)
    @util.undoable
    def translate():
        x = x_var.get()
        y = y_var.get()
        z = z_var.get()
        selected.translate([x, y, z])
        selected.render(views, selected=True)
    
    x_frame, x_entry, x_var = NumericalEntry(frame, 'x:', noop, increment=1, var_factory=tk.IntVar)
    y_frame, y_entry, y_var = NumericalEntry(frame, 'y:', noop, increment=1, var_factory=tk.IntVar)
    z_frame, z_entry, z_var = NumericalEntry(frame, 'z:', noop, increment=1, var_factory=tk.IntVar)
    x_frame.grid(row=1, column=1)
    y_frame.grid(row=2, column=1)
    z_frame.grid(row=3, column=1)
    translate_button = tk.Button(frame, text="Translate!", command=translate).grid(row=4, column=1)
    return frame

def AlignmentPanel(parent):
    frame = tk.Frame(parent)
    frame.bind('<Enter>', highlight_last_selected)
    frame.bind('<Leave>', unhighlight_last_selected)
    
    x_abut_button = AlignmentButton(frame, '../resources/x_abut.png', x_abut_selected)
    x_abut_right_button = AlignmentButton(frame, '../resources/x_abut_right.png', x_abut_right_selected)
    x_center_button = AlignmentButton(frame, '../resources/x_center.png', x_center_selected)
    x_flush_button = AlignmentButton(frame, '../resources/x_flush.png', x_flush_selected)
    x_flush_left_button = AlignmentButton(frame, '../resources/x_flush_left.png', x_flush_left_selected)
    x_abut_button.bind('<Motion>', highlight_last_selected)
    
    x_abut_button.grid      (row=6, column=1)
    x_abut_right_button.grid(row=2, column=1)
    x_center_button.grid    (row=4, column=1)
    x_flush_button.grid     (row=3, column=1)
    x_flush_left_button.grid(row=5, column=1)

    y_abut_button = AlignmentButton(frame, '../resources/y_abut.png', y_abut_selected)
    y_abut_back_button = AlignmentButton(frame, '../resources/y_abut_back.png', y_abut_back_selected)
    y_center_button = AlignmentButton(frame, '../resources/y_center.png', y_center_selected)
    y_flush_button = AlignmentButton(frame, '../resources/y_flush.png', y_flush_selected)
    y_flush_back_button = AlignmentButton(frame, '../resources/y_flush_back.png', y_flush_back_selected)

    y_abut_button.grid      (row=6, column=2)
    y_abut_back_button.grid (row=2, column=2)
    y_center_button.grid    (row=4, column=2)
    y_flush_button.grid     (row=3, column=2)
    y_flush_back_button.grid(row=5, column=2)

    z_abut_button = AlignmentButton(frame, '../resources/z_abut.png', z_abut_selected)
    z_abut_top_button = AlignmentButton(frame, '../resources/z_abut_top.png', z_abut_top_selected)
    z_center_button = AlignmentButton(frame, '../resources/z_center.png', z_center_selected)
    z_flush_button = AlignmentButton(frame, '../resources/z_flush.png', z_flush_selected)
    z_flush_top_button = AlignmentButton(frame, '../resources/z_flush_top.png', z_flush_top_selected)

    z_abut_button.grid     (row=6, column=3)
    z_abut_top_button.grid (row=2, column=3)
    z_center_button.grid   (row=4, column=3)
    z_flush_button.grid    (row=3, column=3)
    z_flush_top_button.grid(row=5, column=3)

    tk.Label(frame, text="Alignment").grid(row=0, column=1, columnspan=3)
    tk.Label(frame, text='x').grid(row=1, column=1)
    tk.Label(frame, text='y').grid(row=1, column=2)
    tk.Label(frame, text='z').grid(row=1, column=3)
    return frame
    
class SideBar:
    def __init__(self, parent):
        self.parent = parent
        self.last_length = 100
        self.last_dim1 = 20
        self.last_dim2 = 20
        self.step = 5
        self.frame = tk.Frame(self.parent)
        self.frame.grid(row=1, column=1, rowspan=10, sticky="NW")

        self.new_part_button = tk.Button(self.frame, command=createAlex, text='New Alex')
        self.new_part_button.grid(row=1, column=1)

        self.length_frame, self.length_entry, self.length_var = NumericalEntry(self.frame,
                                                                               'L:',
                                                                               self.length_change,
                                                                               var_factory=tk.IntVar)
        self.length_frame.grid(row=2, column=1)
        self.dim1_frame, self.dim1_entry, self.dim1_var = NumericalEntry(self.frame,
                                                                         'D1:',
                                                                         self.dim1_change,
                                                                         values=(20, 30, 40),
                                                                         var_factory=tk.IntVar)
        self.dim1_frame.grid(row=3, column=1)
        self.dim2_frame, self.dim2_entry, self.dim2_var = NumericalEntry(self.frame,
                                                                         'D2:',
                                                                         self.dim2_change,
                                                                         values=(20, 30, 40, 60, 80),
                                                                         var_factory=tk.IntVar)
        self.dim2_frame.grid(row=4, column=1)

        self.length_var.set(100)
        self.dim1_var.set(20)
        self.dim2_var.set(20)

        self.x_frame, self.x_entry, self.x_var = NumericalEntry(self.frame,
                                                                'x:',
                                                                self.x_change)
        self.y_frame, self.y_entry, self.y_var = NumericalEntry(self.frame,
                                                                'y:',
                                                                self.y_change)
        self.z_frame, self.z_entry, self.z_var = NumericalEntry(self.frame,
                                                                'z:',
                                                                self.z_change)
        #self.x_frame.grid(row=4, column=1)
        #self.y_frame.grid(row=5, column=1)
        #self.z_frame.grid(row=6, column=1)
        
        #self.export_button = tk.Button(self.frame, command=export, text='Export')
        #self.export_button.grid(row=13, column=1)
        self.step_frame, self.step_entry, self.step_var = NumericalEntry(self.frame,
                                                                         'STEP:',
                                                                         self.step_change,
                                                                         from_=1,
                                                                         increment=1,
                                                                         var_factory=tk.IntVar)
        self.step_frame.grid(row=11, column=1, pady=10)
        self.step_var.set(5)
        if args.zoom_buttons:
            self.zoom_panel = tk.Frame(self.frame)
            self.zoom_panel.grid(row=12, column=1)
            
            self.zoom_in_button = tk.Button(self.zoom_panel, command=zoom_in_lots, text='Zoom In')
            self.zoom_out_button = tk.Button(self.zoom_panel, command=zoom_out_lots, text='Zoom Out')
            self.zoom_fit_button = tk.Button(self.zoom_panel, text="Zoom Fit", command=zoom_fit_selected)
            self.flip_z_button = tk.Button(self.zoom_panel, text="Mirror Z", command=flip_z_selected)
            self.zoom_in_button.grid(row=1, column=1)
            self.zoom_out_button.grid(row=2, column=1)
            self.zoom_fit_button.grid(row=3, column=1)
            self.flip_z_button.grid(row=4, column=1)
            
        

        ## why does this not take its own column
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).grid(row=17, column=1, rowspan=10, sticky='ew')

        self.translate_panel = TranslatePanel(self.frame)
        self.translate_panel.grid(row=17, column=1, pady=5)
        self.ap = AlignmentPanel(self.frame)
        self.ap.grid(row=18, column=1, pady=50)
        

    def step_change(self, id, text, mode):
        try:
            step = self.step_var.get()
            if step < 1:
                step = 1
                self.step_var.set(1)
            STEP[0] = step
            self.last_step = step
        except tk.TclError:
            self.step_var.set(self.last_step)
            pass
        except AttributeError:
            pass
        
    def length_change(self, id, text, mode):
        try:
            if hasattr(self, 'length_var'):
                length = self.length_var.get()
                self.length_entry.config(bg=bgcolor)
                for thing in selected:
                    thing.set_length(length)
                    render(thing)
                if 'scene' in globals():
                    export()
                self.last_length = length
        except tk.TclError as e:
            if str(e) == 'expected floating-point number but got ""':
                pass
            else:
                self.length_var.set(self.last_length)
                #self.length_entry.config(bg='red')

    def dim1_change(self, id, text, mode):
        try:
            if hasattr(self, 'dim1_var'):
                unselect_all()
                dim1 = self.dim1_var.get()
                dim2 = self.dim2_var.get()
                if dim2 < dim1 or (dim2 / dim1) % 1 != 0:
                    self.dim2_entry.config(bg='yellow')
                    if hasattr(self, 'new_part_button'):
                        self.new_part_button.config(state="disabled")
                else:
                    self.dim2_entry.config(bg=bgcolor)
                    if hasattr(self, 'new_part_button'):
                        self.new_part_button.config(state="normal")
                self.dim1_entry.config(bg=bgcolor)
                self.last_dim1 = dim1
        except Exception as e:
            self.dim1_var.set(self.last_dim1)
            #self.dim1_entry.config(bg='red')
            #raise
    def dim2_change(self, id, text, mode):
        try:
            if hasattr(self, 'dim2_var'):
                unselect_all()
                dim1 = self.dim1_var.get()
                dim2 = self.dim2_var.get()
                if dim2 < dim1 or (dim2 / dim1) % 1 != 0:
                    self.dim2_entry.config(bg='yellow')
                    if hasattr(self, 'new_part_button'):
                        self.new_part_button.config(state="disabled")
                else:
                    self.dim2_entry.config(bg=bgcolor)
                    if hasattr(self, 'new_part_button'):
                        self.new_part_button.config(state="normal")

                self.last_dim1 = dim1
        except Exception as e:
            self.dim2_var.set(self.last_dim2)
            #self.dim2_entry.config(bg='red')
    def x_change(self, id, text, mode):
        try:
            if hasattr(self, 'x_var'):
                x = self.x_var.get()
                self.x_entry.config(bg=bgcolor)

                selected.translate([x - selected.pos[0], 0, 0])
                selected.render(views, selected=True)
        except:
            self.x_entry.config(bg='red')

    def y_change(self, id, text, mode):
        try:
            if hasattr(self, 'y_var'):
                y = self.y_var.get()
                self.y_entry.config(bg=bgcolor)

                selected.translate([0, y - selected.pos[1], 0])
                selected.render(views, selected=True)
        except Exception as e:
            self.y_entry.config(bg='red')

    def z_change(self, id, text, mode):
        try:
            if hasattr(self, 'z_var'):
                z = self.z_var.get()
                self.z_entry.config(bg=bgcolor)

                selected.translate([0, 0, z - selected.pos[2]])
                selected.render(views, selected=True)
        except:
            raise
            self.z_entry.config(bg='red')

def cube_dialog(*args):
    def on_cancel(*args):
        tl.destroy()
    @util.undoable
    def on_submit(*args):
        l = l_var.get()
        w = w_var.get()
        h = h_var.get()
        d1 = d1_var.get()
        d2 = d2_var.get()
        hidden_corners = hidden_2020_corners_var.get()
        group = things.Group()
        group.append(Alex(h - 2 * d1, d1, d2).translate([-l/2 + d1/2, -w/2 + d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([-l/2 + d1/2,  w/2 - d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([ l/2 - d1/2, -w/2 + d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([ l/2 - d1/2,  w/2 - d2/2, d1]))

        if hidden_corners:
            cornerFactory = CornerThreeWay
            corner = cornerFactory(d1)
            part = Alex(l-2 * corner.length, d1, d2).rotate(pitch=-1).translate([corner.length - l/2, -w/2 + d2/2, d1/2])
        else:
            part = Alex(l, d1, d2).rotate(pitch=-1).translate([-l/2, -w/2 + d2/2, d1/2])
        group.append(part)

        part = part.dup().translate([0, w - d2, 0])
        group.append(part)
        
        part = part.dup().translate([0, 0, h - d1])
        group.append(part)
        
        part = part.dup().translate([0, -w + d2, 0])
        group.append(part)
        
        part = Alex(w - 2 * d2, d1, d2).rotate(roll=1).translate([l/2-d1/2, w/2 - d2, d2/2])
        group.append(part)

        part = part.dup().translate([0, 0, h - d2])
        group.append(part)

        part = part.dup().translate([-l + d1, 0, 0])
        group.append(part)

        part = part.dup().translate([0, 0, -h + d2])
        group.append(part)

        if hidden_corners:
            corner = cornerFactory(d1);
            corner.rotate(roll=1)
            corner.rotate(yaw=-1)
            corner.translate([l/2, d1/2-w/2, d1/2])
            group.append(corner)

            corner = corner.dup()
            corner.rotate(roll=1)
            corner.translate([0, w-d1, 0])
            group.append(corner)

            corner = corner.dup()
            corner.rotate(roll=1)
            corner.translate([0, 0, h - d1])
            group.append(corner)

            corner = corner.dup()
            corner.rotate(roll=1)
            corner.translate([0, d1 - w, 0])
            group.append(corner)

            ### left corners
            corner = cornerFactory(d1);
            corner.rotate(pitch=1)
            corner.rotate(roll=1)
            corner.rotate(yaw=2)
            corner.rotate(roll=-1)
            corner.translate([-l/2, d1/2-w/2, d1/2])
            group.append(corner)

            corner = cornerFactory(d1);
            corner.rotate(pitch=3)
            corner.rotate(roll=-1)
            corner.translate([-l/2, d1/2-w/2, h - d1/2])
            group.append(corner)

            corner = cornerFactory(d1);
            corner.rotate(pitch=1)
            corner.rotate(roll=-1)
            corner.rotate(yaw=2)
            corner.rotate(roll=-1)
            corner.translate([-l/2, w/2 - d1/2, h - d1/2])
            group.append(corner)

            corner = cornerFactory(d1);
            corner.rotate(pitch=1)
            corner.rotate(roll=2)
            corner.rotate(pitch=2)
            corner.rotate(roll=-1)
            corner.translate([-l/2, w/2 - d1/2, d1/2])
            group.append(corner)
        if False:
            pass
        
        unselect_all()
        #scene.selected.ungroup()
        scene.append(group, select=True)
        on_cancel()

    tl = tk.Toplevel(root)
    frame = tk.Frame(tl)
    l_frame, l_entry, l_var = NumericalEntry(frame,
                                             'L:',
                                             noop)
    l_frame.grid(row=1, column=1)
    w_frame, w_entry, w_var = NumericalEntry(frame,
                                             'W:',
                                             noop)
    w_frame.grid(row=2, column=1)
    h_frame, h_entry, h_var = NumericalEntry(frame,
                                             'H:',
                                             noop)
    h_frame.grid(row=3, column=1)
    d1_frame, d1_entry, d1_var = NumericalEntry(frame,
                                                'D1:',
                                                noop,
                                                increment=10)                                                
    d1_frame.grid(row=4, column=1)
    d2_frame, d2_entry, d2_var = NumericalEntry(frame,
                                                'D2:',
                                                noop,
                                                increment=10)                                                
    d2_frame.grid(row=5, column=1)
    
    hidden_2020_corners_frame, hidden_2020_corners_entry, hidden_2020_corners_var = NumericalEntry(
        frame,
        'Hidden 20x20 Corners?:',
        noop,
        var_factory=tk.BooleanVar)
    hidden_2020_corners_var.set(True)
    hidden_2020_corners_frame.grid(row=6, column=1)
    
    
    l_var.set(100);
    w_var.set(110);
    h_var.set(120);
    d1_var.set(20);
    d2_var.set(20);
    frame.grid(row=1, column=1)

    button_f = tk.Frame(frame)
    button_f.grid(row=7, column=1)
    tk.Button(button_f, text="Ok", command=on_submit).grid(row=1, column=1)
    tk.Button(button_f, text="Cancel", command=on_cancel).grid(row=1, column=2)

def help_dialog(*args):
    def on_cancel(*args):
        tl.destroy()
    def on_ok(*args):
        pass
    tl = tk.Toplevel(root)
    frame = tk.Frame(tl)


    row = 1
    for hotkey in hotkeys:
        tk.Label(frame, text=hotkey[0]).grid(row=row, column=1, sticky='e')
        tk.Label(frame, text=hotkey[1]).grid(row=row, column=2, sticky='w')
        row += 1
    button_f = tk.Frame(frame)
    button_f.grid(row=row, column=1, columnspan=2)
    tk.Button(button_f, text="Ok", command=on_ok).grid(row=1, column=1)
    button_f.grid()
    frame.grid()
def alex_save():
    if len(alex_filename) == 0:
        filename = filedialog.asksaveasfilename(
            title = "Select file",
            filetypes = (("Extruded AL","*.xcad"),
                         ("all files","*.*")))
        if alex_filename.endswith('.xcad.xcad'):
            alex_filename = alexfilename[:,-5]
        alex_filename.append(filename)
    else:
        filename = alex_filename[0]
    if filename:
        group = things.Group()
        for i in range(len(scene)):
            group.append(scene[i])

        with open(filename, 'wb') as f:
            pickle.dump(group.things, f)
        alex_set_titlebar()

def alex_save_as():
    filename = filedialog.asksaveasfilename(
                                            title = "Select file",
                                            filetypes = (("Extruded AL","*.xcad"),
                                                         ("all files","*.*")))
    if filename:
        while len(alex_filename) > 0:
            alex_filename.pop()
        alex_filename.append(filename)
        alex_save()
        
def alex_bom():
    lines = scene.tobom()
    out = []
    counts = []
    for line in lines:
        if line in out:
            i = out.index(line)
            counts[i] += 1
        else:
            out.append(line)
            counts.append(1)
    out = [f'{c},{l}' for c, l in zip(counts, out)]
    out = ['QTY,DESC,DIM'] + out
    out = '\n'.join(out)
    if alex_filename:
        base = alex_filename[0]
        if base.endswith('.xcad'):
            with open(alex_filename[0][:-4] + 'csv', 'w') as f:
                f.write(out)
    print(out)
        
def alex_clear_all():
    util.clear_all()
    
def alex_new():
    while len(alex_filename) > 0:
        alex_filename.pop()
    alex_set_titlebar()
    alex_clear_all()
    util.reset_undo_history()
    
def alex_set_titlebar():
    if alex_filename:
        fn = alex_filename[0]
    else:
        fn = ''
    cost = scene.cost()
    selected_cost = selected.cost()
    #print(cost, selected_cost)
    root.winfo_toplevel().title(f"Alex {fn} ${cost:.2f} (${selected_cost:.2f})")

def stl_import_dialog():
    def ask_filename():
        filename = filedialog.askopenfilename(title = "Select STL file",
                                            filetypes = (("Mesh", "*.stl"),
                                                         ("all files","*.*")))
        if filename:
            filename_entry.delete(0, tk.END)
            filename_entry.insert(0, filename)
            on_submit()
            
    def on_submit():
        stl = things.STL(filename_var.get(), cost_var.get(), unit_var.get())
        scene.append(stl)
        stl.render(views)
        export()
        tl.destroy()
    def on_cancel():
        tl.destroy()
    tl = tk.Toplevel(root)
    frame = tk.Frame(tl)

    filename_var = tk.StringVar()
    tk.Label(frame, text="Filename").grid(row=5, column=1)
    filename_entry = tk.Entry(frame, textvariable=filename_var)
    filename_entry.grid(row=5, column=2, columnspan=2)
    tk.Button(frame, text="Browse", command=ask_filename).grid(row=5, column=4)

    unit_var = tk.StringVar()
    unit_var.set('mm')
    tk.Label(frame, text="Unit:").grid(row=2, column=1)
    unit_entry = tk.Spinbox(frame, values=list(units.keys()), textvariable=unit_var, width=5)
    unit_entry.grid(row=2, column=2, sticky="NW")

    tk.Label(frame, text='Cost $').grid(row=3, column=1)
    cost_var = tk.DoubleVar()
    cost_entry = tk.Spinbox(frame, from_=0, to=1e6, textvariable=cost_var, increment=1, width=5)
    cost_entry.grid(row=3, column=2, sticky="NW")

    
    
    tk.Button(frame, text="Submit", command=on_submit).grid(row=6, column=3, sticky="E")
    tk.Button(frame, text="Cancel", command=on_cancel).grid(row=6, column=4, sticky="W")
    
    frame.grid(row=1, column=1)
    
def alex_import():
    filetypes = (("Extruded AL","*.xcad"),
                 ("Mesh", "*.stl"),
                 ("all files","*.*"))
    if not STL_SUPPORTED:
        filetypes = (("Extruded AL","*.xcad"),
                     ("all files","*.*"))
    filename = filedialog.askopenfilename(
        #initialdir = "/",
        title = "Select file",
        filetypes=filetypes
    )
    if filename.endswith('.xcad'):
        f = open(filename, 'rb')
        group = pickle.load(f)
        f.close()
        if len(group) > 0:
            util.register_undo()
        for thing in group:
            scene.append(thing)
            thing.render(views)
        export()
    if filename.endswith('.stl'):
        util.register_undo()
        scene.append(things.STL(filename))
        export()

def alex_open(filename):
    while len(alex_filename) > 0:
        alex_filename.pop() ### ditch old filename
    alex_filename.append(filename)
    f = open(filename, 'rb')
    things = pickle.load(f)
    f.close()
    
    alex_clear_all()
    for thing in things:
        scene.append(thing)
        thing.render(views)
    alex_set_titlebar()
    
def alex_open_dialog():
    filename = filedialog.askopenfilename(
                                          title = "Select file",
                                          filetypes = (("Extruded AL","*.xcad"),
                                                       ("all files","*.*")))
    if filename:
        alex_open(filename)

################################################################################

root = tk.Tk()

hotkeys = [
    ('<Escape>', cancel),
    ('<Right>', slew_right),
    ('<Left>', slew_left),
    ('<Up>', slew_up),
    ('<Down>', slew_down),
    ('i', slew_back),
    ('j', slew_forward),
    ('a', toggle_axes),
    ('<Control-d>', dup_selected),
    ('<Control-n>', createAlex),
    ('<Control-a>', select_all),
    ('<Delete>', delete_selected),
    ('<Control-g>', group_selected),
    ('<Control-u>', ungroup_selected),
    ("<MouseWheel>", OnMouseWheel),
    ("f", zoom_fit_selected),
    ("<Button-4>", OnMouseButton4_5),
    ("<Button-5>", OnMouseButton4_5),
    ('<Control-z>', util.undo),
    ('<Control-y>', util.redo),
]
for event, command in hotkeys:
    root.bind(event, command)


key_tracker = util.KeyboardTracker(root)
shift_key = util.ShiftTracker(key_tracker)
control_key = util.ControlTracker(key_tracker)

menubar = tk.Menu(root)
# create a pulldown menu, and add it to the menu bar
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="New", command=alex_new)
filemenu.add_command(label="Open", command=alex_open_dialog)
filemenu.add_command(label="Import", command=alex_import)
if STL_SUPPORTED:
    filemenu.add_command(label="Import STL", command=stl_import_dialog)
filemenu.add_command(label="Save", command=alex_save)
filemenu.add_command(label="Save As", command=alex_save_as)
filemenu.add_command(label="Generate BoM", command=alex_bom)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

partmenu = tk.Menu(menubar, tearoff=0)
partmenu.add_command(label='Extruded Al', command=createAlex)
partmenu.add_command(label='2-Way Corner', command=createCornerTwoWay)
partmenu.add_command(label='3-Way Corner', command=createCornerThreeWay)
partmenu.add_separator()
partmenu.add_command(label='Part Library', command=parts_db_dialog)
# partmenu.add_command(label='Add New Part', command=new_part_dialog)
menubar.add_cascade(label="Part", menu=partmenu)


wizardmenu = tk.Menu(menubar, tearoff=0)
wizardmenu.add_command(label="Cube", command=cube_dialog)
menubar.add_cascade(label="Wizard", menu=wizardmenu)

helpmenu = tk.Menu(menubar, tearoff=0)
for event, command in hotkeys:
    helpmenu.add_command(label=f'{str(command).split()[1]} {event}', command=command)
menubar.add_cascade(label="Hotkeys", menu=helpmenu)


root.config(menu=menubar)
################################################################################

window_w = args.width
window_h = args.height
if window_w is None:
    window_w = root.winfo_screenwidth()
if window_h is None:
    window_h = root.winfo_screenheight()
    
CANVAS_W = (window_w - 100) / 3
CANVAS_H = (window_h - 75) / 2




sidebar = SideBar(root)

topcan = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H)
topcan.grid(row=2, column=3);
rt_angle_image = ImageTk.PhotoImage(Image.open('../resources/rt_angle.png')) 
rt_angle_yaw_image = ImageTk.PhotoImage(Image.open('../resources/rt_angle_yaw.png'))
rt_angle_pitch_image = ImageTk.PhotoImage(Image.open('../resources/rt_angle_pitch.png'))
rt_angle_roll_image = ImageTk.PhotoImage(Image.open('../resources/rt_angle_roll.png'))
tk.Button(root, text="Top", image=rt_angle_yaw_image, compound=tk.RIGHT, command=rotate_yaw,
          bg=bgcolor).grid(row=2, column=3, sticky="NW")

sidecan = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H)
sidecan.grid(row=4, column=5);
tk.Button(root, text="Side", image=rt_angle_roll_image, compound=tk.RIGHT,
          command=rotate_roll, bg=bgcolor).grid(row=4, column=5, sticky="NW")

frontcan = tk.Canvas(root, width = CANVAS_W, height=CANVAS_H)
frontcan.grid(row=4, column=3);
tk.Button(root, text="Front", image=rt_angle_pitch_image, compound=tk.RIGHT,
          command=rotate_pitch, bg=bgcolor).grid(row=4, column=3, sticky="NW")

isocan = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H)
isocan.grid(row=2, column=5);
iso_button = tk.Button(root, text="Iso", bg=bgcolor)
iso_button.grid(row=2, column=5, sticky="NW")

scale = 1.
theta = 240 * DEG
phi =  35 * DEG

ihat, jhat, khat = np.eye(3)

step_var = sidebar.step_var
top = iv.IsoView(topcan, ihat , -jhat , [CANVAS_W/2, CANVAS_H/2], step_var, sidebar.x_var, sidebar.y_var, sidebar.z_var,
                 shift_key=shift_key, control_key=control_key, scale=scale)
side = iv.IsoView(sidecan, jhat , -khat , [CANVAS_W/2, CANVAS_H - 50], step_var, sidebar.x_var, sidebar.y_var, sidebar.z_var,
                  shift_key=shift_key, control_key=control_key, scale=scale)
front = iv.IsoView(frontcan, ihat , -khat, [CANVAS_W/2, CANVAS_H - 50], step_var, sidebar.x_var, sidebar.y_var, sidebar.z_var,
                   shift_key=shift_key, control_key=control_key, scale=scale)
iso = iv.from_theta_phi(theta, phi, isocan, [CANVAS_W/2, CANVAS_H - 50], step_var, sidebar.x_var, sidebar.y_var, sidebar.z_var,
                        shift_key=shift_key, control_key=control_key, scale=scale)
views = iv.Views([top, side, front, iso])


scene = things.Scene(views, selected, export_cb=export_cb)

ttk.Separator(root, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=10, sticky='ns')
ttk.Separator(root, orient=tk.VERTICAL).grid(column=4, row=0, rowspan=10, sticky='ns')
ttk.Separator(root, orient=tk.VERTICAL).grid(row=3, column=2, columnspan=10, sticky='ew')


if args.filename is not None:
    alex_open(args.filename)


if False:
    root.bind('<Escape>', cancel)
    root.bind('<Right>', slew_right)
    root.bind('<Left>', slew_left)
    root.bind('<Up>', slew_up)
    root.bind('<Down>', slew_down)
    root.bind('i', slew_back)
    root.bind('j', slew_forward)
    root.bind('a', toggle_axes)
    root.bind('<Control-d>', dup_selected)
    root.bind('<Control-n>', createAlex)
    root.bind('<Control-a>', select_all)
    root.bind('<Delete>', delete_selected)
    root.bind('<Control-g>', group_selected)
    root.bind('<Control-u>', ungroup_selected)
    root.bind("<MouseWheel>", OnMouseWheel)
    root.bind("f", zoom_fit_selected)
    root.bind("<Button-4>", OnMouseButton4_5)
    root.bind("<Button-5>", OnMouseButton4_5)
    root.bind('<Control-z>', util.undo)
    root.bind('<Control-y>', util.redo)
export()
icon_image = ImageTk.PhotoImage(Image.open('../resources/icon.png'))
root.iconphoto(False, icon_image)
root.mainloop()
