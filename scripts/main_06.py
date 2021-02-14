import sys
sys.path.append('./packages/')
import quaternion
import pickle
from tkinter import filedialog
import tkinter as tk
import numpy as np
from numpy import sin, cos, sqrt
import tkinter.ttk as ttk
from PIL import ImageTk, Image

STEP = 5 ### grid step size in mm

if len(sys.argv) > 1:
    CANVAS_W = int(sys.argv[1])
else:
    CANVAS_W = 550
if len(sys.argv) > 2:
    CANVAS_H = int(sys.argv[2])
else:
    CANVAS_H = CANVAS_W
### dummy selected group for bootstrapping gui
selected_group = []

ROLL = np.array([[1, 0, 0],
                 [0, 0, -1],
                 [0, 1, 0]])
PITCH = np.array([[0, 0, -1],
                  [0, 1, 0],
                  [1, 0, 0]])
YAW = np.array([[0, -1, 0],
                [1, 0, 0],
                [0, 0, 1]])

def snap_to_grid(v, step):
    return (v / step).astype(int) * step
    
    
def get_integer_rotation(roll=0, pitch=0, yaw=0):
    orient = np.eye(3)
    for i in range(roll % 4):
        orient = ROLL @ orient
    for i in range(pitch % 4):
        orient = PITCH @ orient
    for i in range(yaw % 4):
        orient = YAW @ orient
    return orient

def closest_pt_on_segment(p0, p1, p):
    p0 = np.array(p0)
    p1 = np.array(p1)
    p = np.array(p)
    b0 = (p1 - p0).astype(float)
    D = np.linalg.norm(b0)
    if D == 0:
        dist = np.linalg.norm(p - p0)
        out = p0
    else:
        b0 /= D
        b1 = np.array([-b0[1], b0[0]])
        B = np.vstack([b0, b1])
        x,y = B @ (p - p0)
        if x < 0:
            out = p0
            dist = np.linalg.norm(p - p0)
        elif x > D:
            out = p1
            dist = np.linalg.norm(p - p1)
        else:
            out = p0 + x * b0
            dist = np.abs(y)
    return out, dist

def closest_test():
    import pylab as pl
    p0 = np.array([5, 5])
    p1 = np.array([10, 10])
    p2 = np.array([0, 5])
    p3 = np.array([5, 0])
    p4 = np.array([0, -5])
    p5 = np.array([10, 5])
    p6 = np.array([10, 15])
    pl.figure()
    pl.plot([p0[0], p1[0]] ,[p0[1], p1[1]], 'b-')
    for p in [p2, p3, p4, p5, p6]:
        a, d = closest_pt_on_segment(p0, p1, p)
        pl.plot([p[0], a[0]] ,[p[1], a[1]], '--')
    pl.axis('equal')
    pl.show()

#closest_test()

def NumericalEntry(parent, label, onchange, from_=-1e6, to=1e6, values=None, increment=1,
                   var_factory=tk.DoubleVar):
    frame = tk.Frame(parent)
    var = var_factory()
    var.trace("w", onchange)
    if var_factory == tk.BooleanVar:
        entry = tk.Checkbutton(frame, text='', variable=var)
        #entry = tk.Spinbox(frame, from_=from_, to=to, textvariable=var, increment=increment)
    else:
        if values is None:
            entry = tk.Spinbox(frame, from_=from_, to=to, textvariable=var, increment=increment, width=5)
        else:
            entry = tk.Spinbox(frame, values=values, textvariable=var, increment=increment, width=5)
        
    tk.Label(frame, text=label).grid(row=1, column=1)
    entry.grid(row=1, column=2)
    return frame, entry, var

def noop(*args, **kw):
    pass
class Rectangle:
    def __init__(self, c1, c2):
        pts = np.vstack([c1, c2])
        self.left = np.min(pts[:,0])
        self.right = np.max(pts[:,0])
        self.bottom = np.min(pts[:,1])
        self.top = np.max(pts[:,1])
    def contains(self, verts):
        if len(verts.shape) == 1:
            verts = np.array(verts)[np.newaxis]
        out = True
        for v in verts:
            if v[0] < self.left or self.right < v[0]:
                out = False
                break
            if v[1] < self.bottom or self.top < v[1]:
                out = False
                break
        return out
            
def new_2_way(*args):
    unselect_all()
    d1 = np.max([20, sidebar.dim1_var.get()])

    part = CornerTwoWay(d1)
    part.select()
    scene.append(part)
    part.render(views)
    export()

def new_3_way(*args):
    unselect_all()
    d1 = np.max([20, sidebar.dim1_var.get()])

    part = bareCornerThreeWay(d1)
    part.select()
    scene.append(part)
    part.render(views)
    export()
    
def new_part(*args):
    unselect_all()
    length = max([0, sidebar.length_var.get()])
    d1 = np.max([20, sidebar.dim1_var.get()])
    d2 = np.max([20, sidebar.dim2_var.get()])

    x = sidebar.x_var.get()
    y = sidebar.x_var.get()
    z = sidebar.x_var.get()
    part = Alex(length, d1, d2)
    #part.translate([x, y, z])
    part.select()
    scene.append(part)
    part.render(views)
    export()
        
class SideBar:
    def __init__(self, parent, width, height):
        self.width = width
        self.height = height
        self.parent = parent
        self.frame = tk.Frame(self.parent)
        self.frame.grid(row=1, column=1, rowspan=10, sticky="NW")

        self.length_frame, self.length_entry, self.length_var = NumericalEntry(self.frame,
                                                                               'L:',
                                                                               self.length_change)
        self.length_frame.grid(row=1, column=1)
        self.dim1_frame, self.dim1_entry, self.dim1_var = NumericalEntry(self.frame,
                                                                         'D1:',
                                                                         self.dim1_change,
                                                                         increment=10,
                                                                         var_factory=tk.IntVar)
        self.dim1_frame.grid(row=2, column=1)
        self.dim2_frame, self.dim2_entry, self.dim2_var = NumericalEntry(self.frame,
                                                                         'D2:',
                                                                         self.dim2_change,
                                                                         increment=10,
                                                                         var_factory=tk.IntVar)
        self.dim2_frame.grid(row=3, column=1)

        self.length_var.set(100)
        self.dim1_var.set(20)
        self.dim2_var.set(20)

        self.x_frame, self.x_entry, self.x_var = NumericalEntry(self.frame,
                                                                'x:',
                                                                self.x_change)
        #self.x_frame.grid(row=4, column=1)
        self.y_frame, self.y_entry, self.y_var = NumericalEntry(self.frame,
                                                                'y:',
                                                                self.y_change)
        #self.y_frame.grid(row=5, column=1)
        self.z_frame, self.z_entry, self.z_var = NumericalEntry(self.frame,
                                                                'z:',
                                                                self.z_change)
        #self.z_frame.grid(row=6, column=1)

        #self.roll_button = tk.Button(self.frame, command=rotate_roll, text='Roll')
        #self.roll_button.grid(row=7, column=1)
        #self.pitch_button = tk.Button(self.frame, command=rotate_pitch, text='Pitch')
        #self.pitch_button.grid(row=8, column=1)
        #self.yaw_button = tk.Button(self.frame, command=rotate_yaw, text='Yaw')
        #self.yaw_button.grid(row=9, column=1)
        
        self.new_part_button = tk.Button(self.frame, command=new_part, text='New Alex')
        self.new_part_button.grid(row=10, column=1)

        self.zoom_in_button = tk.Button(self.frame, command=self.zoom_in, text='Zoom In')
        self.zoom_in_button.grid(row=11, column=1)

        self.zoom_out_button = tk.Button(self.frame, command=self.zoom_out, text='Zoom Out')
        self.zoom_out_button.grid(row=12, column=1)

        #self.export_button = tk.Button(self.frame, command=export, text='Export')
        #self.export_button.grid(row=13, column=1)

    def zoom_in(self):
        views.set_scale(views.get_scale() / .8)
        views.redraw()

    def zoom_out(self):
        views.set_scale(views.get_scale() * .8)

    def length_change(self, id, text, mode):
        try:
            if hasattr(self, 'length_var'):
                length = self.length_var.get()
                self.length_entry.config(bg=bgcolor)
                
                for thing in selected_group:
                    thing.length = length
                    thing.render(views)
        except tk.TclError:
            self.length_entry.config(bg='red')
    def dim1_change(self, id, text, mode):
        try:
            if hasattr(self, 'dim1_var'):
                dim1 = self.dim1_var.get()
                dim2 = self.dim2_var.get()
                if dim2 < dim1 or (dim2 / dim1) % 1 != 0:
                    self.dim2_entry.config(bg='yellow')
                else:
                    self.dim2_entry.config(bg=bgcolor)
                self.dim1_entry.config(bg=bgcolor)

                for thing in selected_group:
                    thing.dim1 = dim1
                    thing.render(views)
        except Exception as e:
            self.dim1_entry.config(bg='red')

    def dim2_change(self, id, text, mode):
        try:
            if hasattr(self, 'dim2_var'):
                dim1 = self.dim1_var.get()
                dim2 = self.dim2_var.get()
                if dim2 < dim1 or (dim2 / dim1) % 1 != 0:
                    self.dim2_entry.config(bg='yellow')
                else:
                    self.dim2_entry.config(bg=bgcolor)

                for thing in selected_group:
                    thing.dim2 = dim2
                    thing.render(views)
        except Exception as e:
            self.dim2_entry.config(bg='red')
    def x_change(self, id, text, mode):
        try:
            if hasattr(self, 'x_var'):
                x = self.x_var.get()
                self.x_entry.config(bg=bgcolor)

                selected_group.translate([x - selected_group.pos[0], 0, 0])
                selected_group.render(views)
        except:
            self.x_entry.config(bg='red')

    def y_change(self, id, text, mode):
        try:
            if hasattr(self, 'y_var'):
                y = self.y_var.get()
                self.y_entry.config(bg=bgcolor)

                for thing in selected_group:
                    thing.translate([0, y - thing.pos[1], 0])
                    thing.render(views)
        except Exception as e:
            self.y_entry.config(bg='red')

    def z_change(self, id, text, mode):
        try:
            if hasattr(self, 'z_var'):
                z = self.z_var.get()
                self.z_entry.config(bg=bgcolor)

                for thing in selected_group:
                    thing.translate([0, 0, z - thing.pos[2]])
                    thing.render(views)
        except:
            self.z_entry.config(bg='red')

def rotate_roll():
    selected_group.rotate(roll=1)
    selected_group.render(views)
    export()

def rotate_pitch():
    selected_group.rotate(pitch=1)
    selected_group.render(views)
    export()

def rotate_yaw():
    selected_group.rotate(yaw=1)
    selected_group.render(views)
    #for thing in selected_group:
    #    thing.rotate(yaw=1)
    #    thing.render(views)
    export()
        
def export(*args):
        header = '''\
include <../resources/components.scad>
'''
        scad = 'Alex_test.scad'
        f = open(scad, 'w')
        f.write(header)
        complete = set() ### prevent multiple outputs (why are there dups in output???)
        for thing in scene:
            if thing in complete:
                print('where did dup come from??')
                pass
            else:
                f.write(thing.toscad())
                f.write('\n')
                complete.add(thing)
        f.close()
            
class KeyTracker:
    '''
    Track when shift is press or released.
    '''
    def __init__(self, parent):
        self.parent = parent
        #self.parent.bind('<Shift_L>', self.pressed)
        self.parent.bind("<KeyPress>", self.keydown)
        self.parent.bind("<KeyRelease>", self.keyup)
        self.state = {}
        
    def keyup(self, event):
        if event.keysym not in self.state:
            self.state[event.keysym] = False
        self.state[event.keysym] = False

    def keydown(self, event):
        if event.keysym not in self.state:
            self.state[event.keysym] = True
        self.state[event.keysym] = True
              
    def released(self, keysym):
        if keysym not in self.state:
            self.state[keysym] = False
        return self.state[keysym]
        
class ShiftTracker:
    def __init__(self, key_tracker):
        self.key_tracker = key_tracker
    def pressed(self):
        return self.key_tracker.released('Shift_L')
    def released(self):
        out = not self.pressed()
        return out

class Thing:
    total = 0
    def __init__(self):
        Thing.total += 1
        self.pos = np.array([0, 0, 0])
        self.orient = np.eye(3)
    def __del__(self):
        try:
            views.delete(self)
        except:
            pass
    def iscontainer(self):
        return False

    def contains(self, other):
        return self is other

    def rotate(self, roll=0, pitch=0, yaw=0):
        '''
        rotate in right angles
        x, y, z -- integer number of right angles (nominally between 0 and 3)
        '''
        self.orient = get_integer_rotation(roll, pitch, yaw) @ self.orient
        return self
    
    def translate(self, v):
        self.pos += v
        return self
    
    def select(self):
        if not selected_group.contains(self):
            selected_group.append(self)
            self.render(views)

    def unselect(self):
        selected_group.remove(self)
        self.render(views)
        
    def render(self, view):
        raise NotImplemented('Abstract base class')

    def dup(self):
        out = []
        for thing in self:
            out.append(thing.dup())
        return Group(out)
    def toscad(self):
        raise NotImplemented("Abstract Base Class")
    def tobom(self):
        raise NotImplemented("Abstract Base Class")
    def get_orientation_angle_and_vec(self):
        #q = quaternion.from_rotation_matrix(self.orient) ## numpy-quaternion
        q = quaternion.Quaternion(matrix=self.orient)## pyquaternion
        angle = q.angle
        # vec = q.vec ## numpy-quaternion
        vec = q.vector ## pyquaternion
        return angle, vec
def indent(s, n):
    '''
    Indent each line of s n spaces
    '''
    indent = ' ' * n
    return ('\n%s' % indent).join(s.splitlines())
    
class Group(Thing):
    def __init__(self, things=None):
        Thing.__init__(self)
        if things is None:
            things = []
        self.things = things
        if len(things) > 0:
            self.pos = np.mean(self.get_verts(), axis=0)

    def iscontainer(self):
        return True

    def __getitem__(self, idx):
        return self.things[idx]

    def __str__(self):
        out = ['Group([']
        for thing in self:
            out.append('   ' + str(thing) + ',')
        out.append('])')
        return '\n'.join(out)

    def get_verts(self):
        out = []
        for thing in self:
            out.append(thing.get_verts())
        return np.vstack(out)
            
    def contains(self, thing):
        out = thing in self.things
        if not out:
            for t in self:
                if t.contains(thing):
                    out = True
                    break
        return out

    def append(self, thing):
        if thing not in self.things:
            self.things.append(thing)
        thing.group = self

    def remove(self, thing):
        if thing in self.things:
            idx = self.things.index(thing)
            self.things.pop(idx)

    def ungroup(self):
        out = self.things
        self.things = []
        export()
        return out

    def translate(self, *args, **kw):
        for thing in self.things:
            thing.translate(*args, **kw)
        self.pos = np.mean(self.get_verts(), axis=0)
        return self

    def rotate(self, *args, **kw):
        if len(self.things) == 1:
            center_of_rotation = self.things[0].pos
        else:
            center_of_rotation = np.mean(self.get_verts(), axis=0)
            center_of_rotation = snap_to_grid(center_of_rotation, STEP)
            #center_of_rotation = np.zeros(3)
        c = center_of_rotation

        R = get_integer_rotation(*args, **kw)
        for thing in self.things:
            thing.rotate(*args, **kw)
            p0 = thing.pos.copy()
            p1 = R @ (p0 - c) + c
            thing.translate(p1 - p0)

    def render(self, view):
        for thing in self:
            thing.render(view)

    def toscad(self):
        out = ['union(){']
        for thing in self:
            out.append('  ' + indent(thing.toscad(), 2))
        out.append('}')
        return '\n'.join(out)
    
    def tobom(self):
        lines = []
        for thing in self.things:
            lines.extend(thing.tobom())
        return lines

class Alex(Thing):
    def __init__(self, length, dim1, dim2):
        Thing.__init__(self)
        self.length = length
        self.dim1 = dim1
        self.dim2 = dim2
        self.orient = np.eye(3)
        self.pos = np.zeros(3)
        self.ids = [None, None, None]

    def get_verts(self):
        '''
        provide 3D corners of bounding box
        '''
        start, stop = self.getstartstop()
        s1 = self.dim1/2
        s2 = self.dim2/2
        verts = np.array([[ s1, -s2, 0],
                          [ s1,  s2, 0],
                          [-s1,  s2, 0],
                          [-s1, -s2, 0]])
        
        verts = np.vstack([verts, verts + [0, 0, self.length]])
        verts = (self.orient @ verts.T).T
        return self.pos + verts
    
    def render(self, view):
        view.erase(self)

        start, stop = self.getstartstop()

        line = np.array([0, 0, self.length])
        s1 = self.dim1/2
        s2 = self.dim2/2
        if selected_group.contains(self):
            color = 'red'
            width = max([1, np.min([2 * view.get_scale(), 3])])
        else:
            color = 'black'
            width = np.max([.5, np.min([1 * view.get_scale(), 1.5])])
        for direction in np.array([[s1,   s2, 0],
                                   [s1,  -s2, 0],
                                   [-s1,  s2, 0],
                                   [-s1, -s2, 0]]):
            start = self.pos + self.orient @ direction
            stop = self.pos + self.orient @ (line + direction)
            view.create_line(self, start, stop, color, width)

        stop = self.pos + self.orient @ [-s1, -s2, 0]
        verts = np.array([[ s1, -s2, 0],
                          [ s1,  s2, 0],
                          [-s1,  s2, 0],
                          [-s1, -s2, 0]])
        for v in verts:
            start = stop
            stop = self.pos + self.orient @ v
            view.create_line(self, start, stop, color, width)

        stop = self.pos + self.orient @ [-s1, -s2, self.length]
        for v in verts:
            start = stop
            stop = self.pos + self.orient @ v + self.orient @ [0, 0, self.length]
            view.create_line(self, start, stop, color, width)
        view.things[str(self)] = self
        return id
    
    def dup(self):
        out = Alex(self.length, self.dim1, self.dim2)
        out.orient = self.orient.copy()
        out.pos = self.pos.copy()
        return out

    def getstartstop(self):
        start = self.pos# + self.orient @ [-self.dim1/2, -self.dim2/2, 0]
        stop = self.pos + self.orient @ np.array([self.dim1/2 * 0,
                                                  self.dim2/2 * 0,
                                                  self.length])
        return start, stop

    def toscad(self):
        out = [
            f'translate([{self.pos[0]:.4f}, {self.pos[1]:.4f}, {self.pos[2]:.4f}])',
            ]
        if selected_group.contains(self):
            out[0] = '#' + out[0]
        #q = quaternion.from_rotation_matrix(self.orient) ## numpy-quaternion
        #q = quaternion.Quaternion(matrix=self.orient)## pyquaternion
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  bar({self.length}, {self.dim1}, {self.dim2});')
        return '\n'.join(out)

    def tobom(self):
        return [f'Extrude AL, {self.dim1:.0f}X{self.dim2:.0f}, {self.length:.0f}']
    
    def __del__(self):
        try:
            views.delete (self)
        except:
            pass

class CornerTwoWay(Alex):
    def __init__(self, dim1):
        Alex.__init__(self, dim1, dim1, dim1)

    def render(self, view):
        view.erase(self)

        start, stop = self.getstartstop()

        line = np.array([0, 0, self.length])
        s1 = self.dim1 / 2
        s2 = self.dim2 / 2
        if selected_group.contains(self):
            color = 'red'
            width = max([1, np.min([2 * view.get_scale(), 3])])
        else:
            color = 'black'
            width = np.max([.5, np.min([1 * view.get_scale(), 1.5])])
        for direction in np.array([[s1,   s2, 0],
                                   [s1,  -s2, 0],
                                   [-s1,  s2, 0],
                                   [-s1, -s2, 0]])[:2]:
            start = self.pos + self.orient @ direction
            stop = self.pos + self.orient @ (line + direction)
            view.create_line(self, start, stop, color, width)

        ### diags!!
        start = self.pos + self.orient @ [-s1, s2, 0]
        stop = self.pos + self.orient @ [s1, s2, self.length]
        view.create_line(self, start, stop, color, width)
        start = self.pos + self.orient @ [-s1, -s2, 0]
        stop = self.pos + self.orient @ [s1, -s2, self.length]
        view.create_line(self, start, stop, color, width)

        stop = self.pos + self.orient @ [-s1, -s2, 0]
        verts = np.array([[ s1, -s2, 0],
                          [ s1,  s2, 0],
                          [-s1,  s2, 0],
                          [-s1, -s2, 0]])
        for v in verts:
            start = stop
            stop = self.pos + self.orient @ v
            view.create_line(self, start, stop, color, width)

        stop = self.pos + self.orient @ [s1, -s2, self.length]
        for v in verts[1:2]:
            start = stop
            stop = self.pos + self.orient @ v + self.orient @ [0, 0, self.length]
            view.create_line(self, start, stop, color, width)
        view.things[str(self)] = self
        return id
    
    def toscad(self):
        out = [
            f'translate([{self.pos[0]:.4f}, {self.pos[1]:.4f}, {self.pos[2]:.4f}])',
            ]
        if selected_group.contains(self):
            out[0] = '#' + out[0]
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  corner_two_way({self.dim1});')
        return '\n'.join(out)

    def tobom(self):
        return [f'Angle Corner Connector, {self.dim1:.0f}X{self.dim1:.0f}',
                'Screw M5x8',
                'Screw M5x8',
                'Drop In Tee Nut',
                'Drop In Tee Nut',
        ]
        
        
    def dup(self):
        out = CornerTwoWay(self.dim1)
        out.orient = self.orient.copy()
        out.pos = self.pos.copy()
        return out

class Interface(Alex):
    def __init__(self, thing, hotspot, dir):
        '''
        thing -- owner of interface
        hotspot -- relative offset of thing pos to interface position in un-rotated coords (3-vector)
        direction -- required direction for proper engagement (unit 3-vector)

        a thing is engaged if one end or the other is in the hotspot with the proper orientaton
        '''
        Alex.__init__(self, 1, thing.dim1, thing.dim1)
        self.thing = thing
        self.hotspot = np.array(hotspot)
        self.dir = np.array(dir, float)
        self.dir /= np.linalg.norm(self.dir)
        self.engaged = False

    def get_color(self):
        dir = self.thing.orient @ self.dir
        r = int(abs(dir[0]))
        g = int(abs(dir[1]))
        b = int(abs(dir[2]))
        return (r, g, b)
    def get_hex_color(self):
        r, g, b = self.get_color()
        return f'#{8*r:1x}{8*g:1x}{8*b:1x}'
    def render(self, view):
        #Alex.render(self, view)
        if not self.is_engaged_with(scene):
            hotspot = self.thing.pos + self.thing.orient @ self.hotspot
            dir = self.thing.orient @ self.dir
            
            color = self.get_hex_color()
            view.create_line(self.thing, hotspot, hotspot + 10 * dir, color, 2)
                         
    def is_engaged_with(self, thing):
        if isinstance(thing, Group):
            group = thing
            out = False
            for thing in group:
                if self.is_engaged_with(thing):
                    out = True
                    break
        else:
            out = False
            start, stop = thing.getstartstop()

            v =   (stop - start)
            vhat = v / np.linalg.norm(v) ### direction of thing
            dir = self.thing.orient @ self.dir
            hotspot = self.thing.pos + self.thing.orient @ self.hotspot
            if np.abs(dir @ vhat - 1) < 0.001: ### positive orientation
                if np.linalg.norm(start - hotspot) < .001:
                    out = True
            if np.abs(dir @ vhat + 1) < 0.001: ### negative orientation
                if np.linalg.norm(stop - hotspot) < .001:
                    out = True
        return out
    def toscad(self):
        if not self.is_engaged_with(scene):
            x, y, z = self.thing.pos + self.thing.orient @ self.hotspot
            dir = self.thing.orient @ self.dir
            a = np.arccos(dir[2]) / DEG ## arccos( dir @ [0, 0, 1] )
            if np.abs(a) < .001:
                v = [0, 0, 1]
            else:
                v = np.cross([0, 0, 1], dir)
                l = np.linalg.norm(v)
                if l > .001:
                    v /= l

            color = self.get_hex_color()
            out = f'color("{color}")translate([{x},{y},{z}])rotate(a={a}, v=[{v[0]}, {v[1]}, {v[2]}])cylinder(r1=1, r2=0, h=10);'
        else:
            out = ''
        return out

class bareCornerThreeWay(Alex):
    def __init__(self, dim1):
        if dim1 < 30:
            h = 5
        else:
            h = 6
        Alex.__init__(self, h, dim1, dim1)

    def toscad(self):
        # q = quaternion.from_rotation_matrix(self.orient)
        out = [
            f'translate([{self.pos[0]:.4f}, {self.pos[1]:.4f}, {self.pos[2]:.4f}])',
            ]
        if selected_group.contains(self):
            out[0] = '#' + out[0]
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  corner_three_way({self.dim1});')
        return '\n'.join(out)

    def tobom(self):
        return [f'3 Way End Corner Bracket, {self.dim1:.0f}X{self.dim2:.0f}']
        
        
    def dup(self):
        out = bareCornerThreeWay(self.dim1)
        out.orient = self.orient.copy()
        out.pos = self.pos.copy()
        return out

class InterfacedThing(Group):
    def __init__(self, thing, interfaces):
        Group.__init__(self, [thing] + [i for i in interfaces])
        self.thing = thing
        self.interfaces = interfaces

    @property
    def position(self):
        return self.thing.pos
    @position.setter
    def set_position(self, v):
        self.thing.translate(v - self.thing.pos)
    def toscad(self):
        color = 'black'
        for i in self.interfaces: 
            i.engaged = True
            if not i.is_engaged_with(scene):
                color = 'darkred'
                i.engaged = False
                break
        self.render(views)

        out = ['union(){']
        out.append('  ' + indent(('color("%s")' % color) + self.thing.toscad(), 2))
        for i in self.interfaces:
            out.append('  ' + indent('  ' + i.toscad(), 2))
        out.append('}')
        return '\n'.join(out)
        
        return ('color("%s")' % color) + Group.toscad(self)
    def get_verts(self):
        out = self.thing.get_verts()
        return out

    def rotate(self, *args, **kw):
        self.thing.rotate(*args, **kw)

    
class CornerThreeWay(InterfacedThing):
    def __init__(self, d1):
        thing = bareCornerThreeWay(d1)
        yinterface = Interface(thing, [0, 10, 10], [0, 1, 0])
        negxinterface = Interface(thing, [-10, 0, 10], [-1, 0, 0])
        zinterface = Interface(thing, [0, 0, 5], [0, 0, 1])
        interfaces = [yinterface, negxinterface, zinterface]
        InterfacedThing.__init__(self, thing, interfaces)
        self.length = self.thing.length
        self.dim1 = self.thing.dim1

    def dup(self):
        out = CornerThreeWay(self.dim1)
        out.thing.translate(self.thing.pos)
        out.thing.orient = self.thing.orient.copy()
        return out
    def rotate(self, *args, **kw):
        self.thing.rotate(*args, **kw)
    def get_verts(self):
        verts = self.thing.get_verts()
        print(verts)
        return verts
class IsoView:
    def __init__(self, can, x, y, offset_x, offset_y, scale=1):
        self.can = can
        self.can.config(bg=bgcolor)
        self.x = x
        self.y = y
        self.scale=scale
        self.things = {}
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.can.bind('<ButtonPress-1>', self.onpress)
        self.can.bind('<ButtonRelease-1>', self.onrelease)
        self.can.bind('<Motion>', self.ondrag)
        self.dragging = None
        self.tags = {}
        self.basis = np.vstack([self.x, self.y])
        self.origin = np.array([self.offset_x, self.offset_y])
        self.button1_down = False
        
    def erase_all(self):
        self.can.delete('all')
        
    def delete(self, thing):
        self.can.delete(str(thing))
    def set_scale(self, scale):
        self.scale = scale
    def get_scale(self):
        return self.scale
    def create_line(self, thing, start, stop, color, width):
        startx = start @ self.x
        starty = start @ self.y
        stopx = stop @ self.x
        stopy = stop @ self.y
        id = self.can.create_line(
            self.offset_x + self.get_scale() * startx,
            self.offset_y + self.get_scale() * starty,
            self.offset_x + self.get_scale() * stopx,
            self.offset_y + self.get_scale() * stopy,
            tags=(str(thing),),
            fill=color, width=width)
        self.tags[id] = thing
    def erase(self, thing):
        remove = []
        self.can.delete(str(thing))
        if isinstance(thing, Group):
            for subthing in thing:
                self.erase(subthing)

    def onpress(self, event):
        self.start = np.array([event.x, event.y])
        self.button1_down = True
        
        clicked = self.can.find_closest(event.x, event.y)
        if len(clicked) > 0:
            closest = clicked[0]
            min_dist = 5
            coords = self.can.coords(closest)
            # if len(coords) == 4:
            x0, y0, x1, y1 = coords
            p0 = [x0, y0]
            p1 = [x1, y1]
            p = self.start
            p, d = closest_pt_on_segment(p0, p1, p)
            if d < min_dist:
                dragging = self.tags[closest]
                for thing in scene.things:
                    if thing.contains(dragging):
                        dragging = thing
                if not selected_group.contains(dragging):
                    if shift_key.released():
                        for thing in selected_group.ungroup():
                            thing.render(views)

                dragging.select()
                dragging.render(views)
                if dragging in self.things:
                    self.dragging = dragging
                    thing = self.things[self.dragging]
                    previously_selected = scene.get_selected()

                    for last in previously_selected:
                        last.unselect()
                        self.parent.render(last)
                    thing.select()
                    self.render(thing)
                self.dragging = dragging
            else:
                if shift_key.released():
                    unselect_all()
                    self.dragging = None
                
    def ondrag(self, event):
        if self.dragging:
            delta = np.zeros(3)
            delta += self.x * (event.x - self.start[0]) / self.get_scale()
            delta += self.y * (event.y - self.start[1]) / self.get_scale()
            delta = snap_to_grid(delta, STEP)
            if np.linalg.norm(delta) > 0:
                selected_group.translate(delta)
                selected_group.render(views)
                self.start = np.array([event.x, event.y])
        else:
            if self.button1_down:
                self.can.delete('selection_box')
                self.can.create_rectangle(self.start[0], self.start[1],
                                            event.x, event.y,
                                            tag=('selection_box',),
                                            outline='lightgrey')
            
    def onrelease(self, event):
        self.button1_down = False
        self.can.delete('selection_box')
        if self.dragging:
            thing = self.dragging
            self.dragging = None
            thing.render(views)
        else:
            corner_1 = (np.array([event.x, event.y]) - self.origin) / self.scale
            corner_2 = (self.start - self.origin) / self.scale
            selection_box = Rectangle(corner_1, corner_2)
            for thing in scene:
                verts = thing.get_verts()
                verts = (self.basis @ verts.T).T
                if selection_box.contains(verts):
                    thing.select()
        if len(selected_group.things) == 1 and isinstance(selected_group.things[0], Alex):
            thing = selected_group.things[0]
            sidebar.length_entry.config(state="normal")
            sidebar.dim1_entry.config(state="normal")
            sidebar.dim2_entry.config(state="normal")
            sidebar.length_entry.delete(0, tk.END)
            sidebar.length_entry.insert(0, str(thing.length))
            sidebar.dim1_entry.delete(0, tk.END)
            sidebar.dim1_entry.insert(0, str(thing.dim1))
            sidebar.dim2_entry.delete(0, tk.END)
            sidebar.dim2_entry.insert(0, str(thing.dim2))
        else:
            if False:
                sidebar.length_entry.config(state="disabled")
                sidebar.dim1_entry.config(state="disabled")
                sidebar.dim2_entry.config(state="disabled")
        if len(selected_group.things) > 0:
            x, y, z = selected_group.pos
            #sidebar.x_var.set(x)
            #sidebar.y_var.set(y)
            #sidebar.z_var.set(z)
        else:
            pass
            #sidebar.x_var.set(0)
            #sidebar.y_var.set(0)
            #sidebar.z_var.set(0)
        export()
            
    def redraw(self):
        self.can.delete('all')
        for thing in scene:
            thing.render(self)
    def set_scale(self, scale):
        self.scale = scale
        self.redraw()

class MultiView:
    def __init__(self, views):
        self.things = {}
        self.views = views
        for view in self.views:
            view.parent = self
    def erase_all(self):
        for view in self.views:
            view.erase_all()
            
    def create_line(self, *args, **kw):
        for view in self.views:
            view.create_line(*args, **kw)
            
    def erase(self, *args, **kw):
        for view in self.views:
            view.erase(*args, **kw)
    def get_scale(self):
        return self.views[0].get_scale()
    def callback(self, thing):
        pass
    def select_all(self, *args):
        pass
    def set_scale(self, scale):
        for view in self.views:
            view.set_scale(scale)
    def delete_all(self, *args):
        pass
    def delete(self, thing):
        pass
    def dup_selected(self, *args):
        for thing in selected_group:
            dup = thing.dup()
            scene.append(dup)
            dup.render(views)
    def redraw(self):
        for view in self.views:
            view.redraw()
            
def unselect_all():
    for thing in selected_group.ungroup():
        thing.render(views)

def cancel(*args):
    '''
    unselect all
    '''
    sidebar.length_var.set(100)    
    sidebar.dim1_var.set(20)    
    sidebar.dim2_var.set(20)    
    sidebar.x_var.set(0)    
    sidebar.y_var.set(0)    
    sidebar.z_var.set(0)
    
def delete_selected(*args):
    for thing in selected_group.ungroup():
        #thing.render(views)
        scene.remove(thing)
        views.erase(thing)
        del thing
    export()
def clear_all(*args):
    pass

def group_selected(*args):
    out = Group()
    for thing in selected_group:
        out.append(thing)
        scene.remove(thing)
    scene.append(out)
    return out
def ungroup_selected(*args):
    for thing in selected_group:
        if isinstance(thing, Group):
            scene.remove(thing)
            for sub in thing.ungroup():
                scene.append(sub)
                sub.unselect()
    export()
root = tk.Tk()
bgcolor = "white"
root.bind('<Escape>', cancel)
sidebar = SideBar(root, 10, 800)


topcan = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H)
topcan.grid(row=2, column=3);
#tk.Button(root, text="Top").grid(row=2, column=3, sticky="NW")
#rt_angle_image = tk.PhotoImage(file = '../resources/rt_angle.png')
#rt_angle_yaw_image = tk.PhotoImage(file = '../resources/rt_angle_yaw.png')
#rt_angle_pitch_image = tk.PhotoImage(file = '../resources/rt_angle_pitch.png')
#rt_angle_roll_image = tk.PhotoImage(file = '../resources/rt_angle_roll.png')
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
tk.Button(root, text="Iso", bg=bgcolor).grid(row=2, column=5, sticky="NW")

ttk.Separator(root, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=10, sticky='ns')
ttk.Separator(root, orient=tk.VERTICAL).grid(column=4, row=0, rowspan=10, sticky='ns')
ttk.Separator(root, orient=tk.VERTICAL).grid(row=3, column=2, columnspan=10, sticky='ew')


DEG = np.pi / 180
scale = 1.
theta = 240 * DEG
phi =  35 * DEG

pov = -np.array([np.sin(phi),
                0,
                np.cos(phi)])

pov = np.array([[cos(theta), sin(theta), 0],
                [-sin(theta),  cos(theta), 0],
                [         0,           0, 1]]) @ pov

iso_z  = np.array([0, 0, 1])
iso_z = iso_z - (iso_z @ pov) * pov
iso_z /= np.linalg.norm(iso_z)
iso_x = np.cross(pov, iso_z)
iso_y = np.cross(iso_z, iso_x)

ihat, jhat, khat = np.eye(3)

top = IsoView(topcan, ihat , -jhat , CANVAS_W/2, CANVAS_H/2, scale=scale)
side = IsoView(sidecan, jhat , -khat , CANVAS_W/2, CANVAS_H - 50, scale=scale)
front = IsoView(frontcan, ihat , -khat, CANVAS_W/2, CANVAS_H - 50, scale=scale)
iso = IsoView(isocan, -iso_x , iso_y , CANVAS_W/2, CANVAS_H - 50, scale=scale)
views = MultiView([top, side, front, iso])
root.bind('<Delete>', delete_selected)
#root.bind('<BackSpace>', delete_selected)
root.bind('<Control-d>', views.dup_selected)
root.bind('<Control-n>', new_part)
root.bind('<Control-a>', views.select_all)
root.bind('<Control-g>', group_selected)
root.bind('<Control-u>', ungroup_selected)


################################################################################
### MENU
def cube_dialog(*args):
    def on_cancel(*args):
        tl.destroy()
    def on_submit(*args):
        l = l_var.get()
        w = w_var.get()
        h = h_var.get()
        d1 = d1_var.get()
        d2 = d2_var.get()
        hidden_corners = hidden_2020_corners_var.get()
        group = Group()
        group.append(Alex(h - 2 * d1, d1, d2).translate([-l/2 + d1/2, -w/2 + d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([-l/2 + d1/2,  w/2 - d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([ l/2 - d1/2, -w/2 + d2/2, d1]))
        group.append(Alex(h - 2 * d1, d1, d2).translate([ l/2 - d1/2,  w/2 - d2/2, d1]))

        cornerFactory = bareCornerThreeWay
        if hidden_corners:
            corner = bareCornerThreeWay(d1)
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
        group.select()
        scene.append(group)
        group.render(views)
        
        
        on_cancel()
        export()

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
                                                noop)
    d1_frame.grid(row=4, column=1)
    d2_frame, d2_entry, d2_var = NumericalEntry(frame,
                                                'D2:',
                                                noop)
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

alex_filename = [] ### use as mutable string
def alex_save():
    if len(alex_filename) == 0:
        filename = filedialog.asksaveasfilename(#initialdir = "/",
            title = "Select file",
            filetypes = (("Extruded AL","*.alex"),
                         ("all files","*.*")))
        alex_filename.append(filename)
    else:
        filename = alex_filename[0]
    f = open(filename, 'wb')
    pickle.dump(scene, f)
    alex_set_titlebar()

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
        if base.endswith('.alex'):
            open(alex_filename[0][:-4] + 'csv', 'w').write(out)
    print(out)
        
    
def alex_save_as():
    filename = filedialog.asksaveasfilename(#initialdir = "/",
                                            title = "Select file",
                                            filetypes = (("Extruded AL","*.alex"),
                                                         ("all files","*.*")))
    if filename:
        while len(alex_filename) > 0:
            alex_filename.pop()
        alex_filename.append(filename)
        f = open(filename, 'wb')
        pickle.dump(scene, f)
        alex_set_titlebar()

def alex_clear_all():
    selected_group.ungroup()
    for thing in scene.ungroup():
        views.erase(thing)
        del thing
    
def alex_new():
    while len(alex_filename) > 0:
        alex_filename.pop()
    alex_set_titlebar()
    alex_clear_all()

def alex_set_titlebar():
    if alex_filename:
        fn = alex_filename[0]
    else:
        fn = ''
    root.winfo_toplevel().title(f"Alex {fn}")    
def alex_import():
    filename = filedialog.askopenfilename(#initialdir = "/",
                                          title = "Select file",
                                          filetypes = (("Extruded AL","*.alex"),
                                                       ("all files","*.*")))
    if filename:
        f = open(filename, 'rb')
        things = pickle.load(f)
        for thing in things:
            scene.append(thing)
            thing.render(views)
        export()

def alex_open(filename):
    while len(alex_filename) > 0:
        alex_filename.pop()
    alex_filename.append(filename)
    f = open(filename, 'rb')
    things = pickle.load(f)
    alex_clear_all()
    for thing in things:
        scene.append(thing)
        thing.render(views)
    export()
    alex_set_titlebar()
    
def alex_open_dialog():
    filename = filedialog.askopenfilename(#initialdir = "/",
                                          title = "Select file",
                                          filetypes = (("Extruded AL","*.alex"),
                                                       ("all files","*.*")))
    if filename:
        alex_open(filename)
menubar = tk.Menu(root)
# create a pulldown menu, and add it to the menu bar
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="New", command=alex_new)
filemenu.add_command(label="Open", command=alex_open_dialog)
filemenu.add_command(label="Import", command=alex_import)
filemenu.add_command(label="Save", command=alex_save)
filemenu.add_command(label="Save As", command=alex_save_as)
filemenu.add_command(label="Generate BoM", command=alex_bom)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

partmenu = tk.Menu(menubar, tearoff=0)
partmenu.add_command(label='Extruded Al', command=new_part)
partmenu.add_command(label='2-Way Corner', command=new_2_way)
partmenu.add_command(label='3-Way Corner', command=new_3_way)
menubar.add_cascade(label="Part", menu=partmenu)


wizardmenu = tk.Menu(menubar, tearoff=0)
wizardmenu.add_command(label="Cube", command=cube_dialog)
menubar.add_cascade(label="Wizard", menu=wizardmenu)
root.config(menu=menubar)
################################################################################

length = 100
width = 150
height = 125
d1 = 20
d2 = 20
OFFSET = 0

### global groups!
scene = Group()
scene.render(views)
selected_group = Group()

if False: ## add some test parts?
    alex = Alex(100, 20, 20)
    alex.rotate(roll=-1)
    alex.translate([0, 10, 10])
    bb = CornerThreeWay(d1)

    scene.append(alex)
    scene.append(bb)
    scene.render(views)

if False:
    base = [Alex(length, w),
            Alex(width, w),
            Alex(length, w),
            Alex(width, w),
    ]
    base[0].translate([OFFSET, OFFSET, OFFSET])
    base[1].rotate(pitch=-1)
    base[1].translate([OFFSET + w/2,  OFFSET, OFFSET + w/2])
    base[2].translate([OFFSET + width + w, OFFSET, OFFSET])
    base[3].rotate(pitch=-1)
    base[3].translate([OFFSET + w / 2, OFFSET, OFFSET + length - w / 2])
    for b in base:
        b.render(views)
if False:
    sides = []
    for i in range(4):
        side = Alex(height, w)
        side.translate([OFFSET, OFFSET, OFFSET])
        side.rotate(roll=1)
        sides.append(side)
    sides[0].translate([0, 0, w])
    sides[1].translate([length + w/2, 0, w/2])
    sides[2].translate([length + w/2, width - w, w/2])
    sides[3].translate([-w/2, width - w, w/2])
    for s in sides[:2]:
        views.render(s)

if False:
    top = [Alex(length, w),
            Alex(width, w),
            Alex(length, w),
            Alex(width, w),
    ]
    top[0].translate([OFFSET, OFFSET, OFFSET + w + height])
    top[1].rotate(yaw=1)
    top[1].translate([length + OFFSET + w/2, OFFSET - w/2, height + OFFSET + w])
    top[2].translate([OFFSET, width + OFFSET - w, height + OFFSET + w])
    top[3].rotate(yaw=1)
    top[3].translate([OFFSET - w/2, OFFSET - w/2, height + OFFSET + w])
    for t in top:
        views.render(t)


#alex.render(topview, sideview, frontview, .5)
#alex.rotate(pitch=1)
#alex.translate([OFFSET, OFFSET, OFFSET])
#alex.render(topview, sideview, frontview, .5)
#topview.create_line(15, 25, 200, 25)
# print(top[0].toscad())

key_tracker = KeyTracker(root)
shift_key = ShiftTracker(key_tracker)
import os
import sys
if len(sys.argv) > 1:
    fn = sys.argv[1]
    if os.path.exists(fn):
        alex_open(fn)
alex_set_titlebar()
root.mainloop()
