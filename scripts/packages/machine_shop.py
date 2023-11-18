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
# -- add example of difference between wireframe and stl (Corner Three Way)
'''
import sys
from stl import mesh
import webbrowser
import os
import os.path
import sys
import pickle
import argparse
import warnings

if '.' not in sys.path:
    sys.path.append('.')

warnings.simplefilter("error")

from tkinter import filedialog
import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image

import numpy as np
from numpy import sin, cos, sqrt

from packages import quaternion
from packages import interpolate
from packages import constants
from packages.constants import mm, inch, DEG, units, bgcolor, alex_scad, openscad_path, fine_rotation_angle
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
parser.add_argument('-M', '--edit_main', nargs='?', default=False, type=util.str2bool)
args = parser.parse_args()

### Global singletons
alex_filename = [] ### use as mutable string
STEP = [5]          ### use as mutable int

selected = things.Selected()

def NumericalEntry(parent, label, onchange, from_=-1e6, to=1e6, values=None, increment=1,
                   var_factory=tk.DoubleVar):
    frame = tk.Frame(parent)
    var = var_factory()
    if onchange != noop:
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
    machine_shop_set_titlebar()
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
        rt_angles = fine_rotation_angle
    else:
        rt_angles = 1
    selected.rotate(roll=rt_angles)
    selected.render(views, selected=True)
    export()
def rotate_pitch():
    if len(selected) > 0:
        util.register_undo()
    if control_key.pressed():
        rt_angles = fine_rotation_angle
    else:
        rt_angles = 1
    selected.rotate(pitch=rt_angles)
    selected.render(views, selected=True)
    export()
def rotate_yaw():
    if len(selected) > 0:
        util.register_undo()
    if control_key.pressed():
        rt_angles = fine_rotation_angle
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
    

class MachinedPart(parts_db.Part):
    '''
    support drilling and mitering
    '''
    def __init__(self, name, length):
        parts_db.Part.__init__(self, parts_db.Main, name, length)
        self.holes = []
        
    def drill(self, diameter, point, dir):
        self.holes.append((diameter, point, dir))

    def toscad(self):
        pos = self.pos
        out = []
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'translate([{pos[0]}, {pos[1]}, {pos[2]}])')
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  color("{self.color}")')
        out.append( '  difference(){')
        out.append(f'    scale([{self.dim1}, {self.dim2}, {self.length}])import("{self.stl_fn}");')
        for d, p, dir in self.holes:
            i = np.argmax(np.abs(dir))
            if i == 0:
                angles = [0, 90, 0]
            elif i == 1:
                angles = [90, 0, 0]
            else:
                angles = [0, 0, 0]
            out.append(f'    translate([{p[0]}, {p[1]}, {p[2]}])rotate({angles})translate([0, 0, -2000])cylinder(d={d}, h=4000, $fn=50);')
        out.append( '  }')
                    
        return '\n'.join(out)
    
def Alex(length, d1, d2):
    if d1 == 30:
        metal = 'HFSL6'
    else:
        metal = 'HFS5'
    out = MachinedPart(f"{d1:.0f}{d2:.0f} {metal}", length)
    out.drill(7, [0, 0, 10], [1, 0, 0])
    out.drill(7, [0, 0, 20], [0, 1, 0])
    return out

def createAlex(*args):
    unselect_all()
    
    try:
        length = max([0, float(sidebar.length_var.get())])
    except tk.TclError:
        length = 100
        sidebar.length_var.set(length)
    d1 = np.max([20, float(sidebar.dim1_var.get())])
    d2 = np.max([20, float(sidebar.dim2_var.get())])

    #x = sidebar.x_var.get()
    #y = sidebar.y_var.get()
    #z = sidebar.z_var.get()
    part = Alex(length, d1, d2)
    #part.translate([x, y, z])
    scene.append(part, select=True)
    
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
    def translate():
        x = float(x_var.get())
        y = float(y_var.get())
        z = float(z_var.get())
        selected.translate([x, y, z])
        selected.render(views, selected=True)
    
    x_frame, x_entry, x_var = NumericalEntry(frame, 'x:', noop, increment=1, var_factory=tk.StringVar)
    y_frame, y_entry, y_var = NumericalEntry(frame, 'y:', noop, increment=1, var_factory=tk.StringVar)
    z_frame, z_entry, z_var = NumericalEntry(frame, 'z:', noop, increment=1, var_factory=tk.StringVar)
    x_var.set(0)
    y_var.set(0)
    z_var.set(0)
    x_var.trace('w', util.numbers_only(x_var, x_entry))
    y_var.trace('w', util.numbers_only(y_var, y_entry))
    z_var.trace('w', util.numbers_only(z_var, z_entry))
    x_frame.grid(row=1, column=1)
    y_frame.grid(row=2, column=1)
    z_frame.grid(row=3, column=1)
    translate_button = tk.Button(frame, text="Translate!", command=translate).grid(row=4, column=1)

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
                                                                                noop,
                                                                                var_factory=tk.StringVar)
        self.length_var.trace('w', util.numbers_only(self.length_var, self.length_entry))
        self.length_entry.bind('<FocusIn>', self.length_enter)
        self.length_entry.bind('<FocusOut>', self.length_exit)
        self.length_frame.grid(row=2, column=1)
        self.dim1_frame, self.dim1_entry, self.dim1_var = NumericalEntry(self.frame,
                                                                         'D1:',
                                                                         noop,
                                                                         values=(20, 30, 40),
                                                                         var_factory=tk.StringVar)
        self.dim1_var.trace('w', util.numbers_only(self.dim1_var, self.dim1_entry))
        self.dim1_frame.grid(row=3, column=1)
        self.dim2_frame, self.dim2_entry, self.dim2_var = NumericalEntry(self.frame,
                                                                         'D2:',
                                                                         noop,
                                                                         values=(20, 30, 40, 60, 80),
                                                                         var_factory=tk.StringVar)
        self.dim2_var.trace('w', util.numbers_only(self.dim2_var, self.dim2_entry))
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
            
        

        self.translate_panel = TranslatePanel(self.frame)
        self.translate_panel.grid(row=17, column=1, pady=5)

        def drill(*args):
            print('drill')
        tk.Button(self.frame, text='Drill', command=drill).grid(row=18, column=1, columnspan=2, pady=20)
        self.d_frame, self.d_entry, self.d_var = NumericalEntry(self.frame, 'Bit [mm]:', noop, from_=1, to=80,
                                                                increment=0.5, var_factory=tk.StringVar)
        self.d_var.set(5.5)
        self.d_frame.grid(row=19, column=1)
        def activate(*args):
            self.active = True

        def disactivate(*args):
            self.active = False

            
        self.frame.bind('<Enter>', activate)
        self.frame.bind('<Leave>', disactivate)

        def save(*args):
            tolib = parts_db.Library('User')
            if len(scene) > 0:
                part = scene[0]
                lib = parts_db.Library('User')
                stl = os.path.join(lib.stl_dir, 'custom_part.stl')
                os.system(f"{openscad_path} {alex_scad} --imgsize=512,512 -o {stl}")
                wireframe = np.array([part.dim_x, part.dim_y, part.dim_z]) * wireframes.cube_frame.copy()
                hole = wireframes.cylinder
                spacer = np.arange(3) * np.nan
                
                part.saveas(tolib, 'custom')
            
        save_button = tk.Button(self.frame, text='Save', command=save)
        save_button.grid(row=20, column=1, pady=50)

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
    def length_enter(self, event):
        lengths = [thing.length for thing in scene.selected if not thing.iscontainer()]
        if len(lengths) and  max(lengths) - min(lengths) < .01:
            self.length_var.set(lengths[0])
            
    def length_exit(self, event):
        try:
            if hasattr(self, 'length_var'):
                length = float(self.length_var.get())
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

def machine_shop_set_titlebar():
    root.winfo_toplevel().title(f"Alex Machine Shop")


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
    ('<Control-a>', select_all),
    ('<Delete>', delete_selected),
    ('<Control-g>', group_selected),
    ('<Control-u>', ungroup_selected),
    ("<MouseWheel>", OnMouseWheel),
    ("f", zoom_fit_selected),
    ("<Button-4>", OnMouseButton4_5),
    ("<Button-5>", OnMouseButton4_5),
]
for event, command in hotkeys:
    root.bind(event, command)


key_tracker = util.KeyboardTracker(root)
shift_key = util.ShiftTracker(key_tracker)
control_key = util.ControlTracker(key_tracker)

menubar = tk.Menu(root)
# create a pulldown menu, and add it to the menu bar

def saw_init(*args):

    views.erase('TOOL')
    views.create_line('TOOL', [500, -500, 0], [-500, 500, 0], 'red', 2, dash=(5,5))
    return
    verts = scene.get_verts()
    mx = np.max(verts, axis=0)
    mn = np.min(verts, axis=0)
    path = np.array([[0, mn[1], mn[2]],
                     [0, mn[1], mx[2]],
                     [0, mx[1], mx[2]],
                     [0, mx[1], mn[2]],
                     [0, mn[1], mn[2]]])
    views.create_path('TOOL', path, 'red', 2, dash=(5,5))
    
    
def drill_init(*args):
    views.erase('TOOL')
    verts = scene.get_verts()
    mx = np.max(verts, axis=0)
    mn = np.min(verts, axis=0)
    
    theta = np.arange(0, 361, 10) * np.pi/180
    d = float(sidebar.d_var.get())
    r = d/2.
    path = np.column_stack([r * np.cos(theta), r * np.sin(theta), np.zeros(len(theta)) + mn[2]])
    views.create_path('TOOL', path, 'red', 2)
    path = np.column_stack([r * np.cos(theta), r * np.sin(theta), np.zeros(len(theta)) + mx[2]])
    views.create_path('TOOL', path, 'red', 2)

    for i in range(8):
        theta = i * 2 * np.pi / 8
        start = np.array([r * np.cos(theta), r * np.sin(theta), mx[2]])
        stop =  np.array([r * np.cos(theta), r * np.sin(theta), mn[2]])
        views.create_line('TOOL', start, stop, 'red', 2, dash=(5, 5))


toolmenu = tk.Menu(menubar, tearoff=0)
toolmenu.add_command(label='Drill', command=drill_init)
toolmenu.add_command(label='Saw', command=saw_init)
menubar.add_cascade(label="Tools", menu=toolmenu)


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

constants.edit_main = args.edit_main



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
topcan.config(bg='#dddddd')
isocan.config(bg='#dddddd')
frontcan.config(bg='#dddddd')
sidecan.config(bg='#dddddd')
root.mainloop()
