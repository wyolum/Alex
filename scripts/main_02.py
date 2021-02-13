import pickle
from tkinter import filedialog
import quaternion
import tkinter as tk
import numpy as np
from numpy import sin, cos, sqrt


CANVAS_DIM = 400
ROLL = np.array([[1, 0, 0],
                 [0, 0, -1],
                 [0, 1, 0]])
PITCH = np.array([[0, 0, -1],
                  [0, 1, 0],
                  [1, 0, 0]])
YAW = np.array([[0, -1, 0],
                [1, 0, 0],
                [0, 0, 1]])

class ShiftTracker:
    '''
    Track when shift is press or released.
    '''
    def __init__(self, parent):
        self.parent = parent
        #self.parent.bind('<Shift_L>', self.pressed)
        self.parent.bind("<KeyPress>", self.keydown)
        self.parent.bind("<KeyRelease>", self.keyup)
        self.pressed = False
        self.released = True
        
    def keyup(self, event):
        if event.keysym == 'Shift_L':
            self.pressed = False
            self.released = True
    def keydown(self, event):
        if event.keysym == 'Shift_L':
            self.pressed = True
            self.released = False
class Thing:
    def __init__(self):
        self.selected = False
    
    def rotate(self, roll=0, pitch=0, yaw=0):
        '''
        rotate in right angles
        x, y, z -- integer number of right angles (nominally between 0 and 3)
        '''
        for i in range(roll % 4):
            self.orient = ROLL @ self.orient
        for i in range(pitch % 4):
            self.orient = PITCH @ self.orient
        for i in range(yaw % 4):
            self.orient = YAW @ self.orient

    def translate(self, v):
        self.pos += v

class Group(Thing):
    def __init__(self, things):
        self.things = things
    def translate(self, *args, **kw):
        for thing in self.things:
            thing.translate(*args, **kw)
    def rotate(self, *args, **kw):
        for thing in self.things:
            thing.rotate(*args, **kw)
    
def NumericalEntry(parent, label, onchange, from_=-1e6, to=1e6, values=None, increment=1,
                   var_factory=tk.DoubleVar):
    frame = tk.Frame(parent)
    var = var_factory()
    var.trace("w", onchange)
    if values is None:
        entry = tk.Spinbox(frame, from_=from_, to=to, textvariable=var, increment=increment)
    else:
        entry = tk.Spinbox(frame, values=values, textvariable=var, increment=increment)
        
    tk.Label(frame, text=label).grid(row=1, column=1)
    entry.grid(row=1, column=2)
    return frame, entry, var

def noop(*args, **kw):
    pass
class SideBar:
    def __init__(self, parent, width, height):
        self.width = width
        self.height = height
        self.parent = parent
        self.frame = tk.Frame(self.parent)
        self.frame.grid(row=1, column=1, rowspan=2)

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
        self.x_frame, self.x_entry, self.x_var = NumericalEntry(self.frame,
                                                                'x:',
                                                                self.x_change)
        self.x_frame.grid(row=4, column=1)
        self.y_frame, self.y_entry, self.y_var = NumericalEntry(self.frame,
                                                                'y:',
                                                                self.y_change)
        self.y_frame.grid(row=5, column=1)
        self.z_frame, self.z_entry, self.z_var = NumericalEntry(self.frame,
                                                                'z:',
                                                                self.z_change)
        self.z_frame.grid(row=6, column=1)

        self.roll_button = tk.Button(self.frame, command=self.rotate_roll, text='Roll')
        self.roll_button.grid(row=7, column=1)
        self.pitch_button = tk.Button(self.frame, command=self.rotate_pitch, text='Pitch')
        self.pitch_button.grid(row=8, column=1)
        self.yaw_button = tk.Button(self.frame, command=self.rotate_yaw, text='Yaw')
        self.yaw_button.grid(row=9, column=1)
        
        self.new_part_button = tk.Button(self.frame, command=self.new_part, text='New Part')
        self.new_part_button.grid(row=10, column=1)

        self.zoom_in_button = tk.Button(self.frame, command=self.zoom_in, text='Zoom In')
        self.zoom_in_button.grid(row=11, column=1)

        self.zoom_out_button = tk.Button(self.frame, command=self.zoom_out, text='Zoom Out')
        self.zoom_out_button.grid(row=12, column=1)

        #self.export_button = tk.Button(self.frame, command=self.export, text='Export')
        #self.export_button.grid(row=13, column=1)

    def new_part(self, *args):
        views.unselect_all()
        length = max([0, sidebar.length_var.get()])
        d1 = np.max([20, sidebar.dim1_var.get()])
        d2 = np.max([20, sidebar.dim2_var.get()])

        x = sidebar.x_var.get()
        y = sidebar.x_var.get()
        z = sidebar.x_var.get()
        part = ExAl(length, d1, d2)
        #part.translate([x, y, z])
        part.selected = True
        views.render(part)
        
    def zoom_in(self):
        views.set_scale(top.scale / .8)
    def zoom_out(self):
        views.set_scale(top.scale * .8)
        pass
    def export(self):
        header = '''\
module square_bar(l, d1){
  linear_extrude(l)
    scale(d1/30)import(file = "../resources/30-30.dxf");
}

module bar(l, d1, d2){
  translate([0, d1/2 - d2/2, 0])
  for (i = [0:d2/d1-1]){
    translate([0, i * d1, 0])square_bar(l, d1);
  }
}

'''
        scad = 'Alex_test.scad'
        f = open(scad, 'w')
        f.write(header)
        complete = set() ### prevent multiple outputs (why are there dups in output???)
        for key in top.things:
            thing = top.things[key]
            if thing in complete:
                print('where did dup come from??')
                pass
            else:
                f.write(thing.toscad())
                f.write('\n')
                complete.add(thing)
        f.close()
            
    def length_change(self, id, text, mode):
        try:
            if hasattr(self, 'length_var'):
                length = self.length_var.get()
                self.length_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.length = length
                    views.render(thing)
        except:
            self.length_entry.config(bg='red')
    def dim1_change(self, id, text, mode):
        try:
            if hasattr(self, 'dim1_var'):
                dim1 = self.dim1_var.get()
                dim2 = self.dim2_var.get()
                if dim2 < dim1 or (dim2 / dim1) % 1 != 0:
                    self.dim2_entry.config(bg='yellow')
                else:
                    self.dim2_entry.config(bg='white')
                self.dim1_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.dim1 = dim1
                    views.render(thing)
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
                    self.dim2_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.dim2 = dim2
                    views.render(thing)
        except Exception as e:
            self.dim2_entry.config(bg='red')
    def x_change(self, id, text, mode):
        try:
            if hasattr(self, 'x_var'):
                x = self.x_var.get()
                self.x_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.translate([x - thing.pos[0], 0, 0])
                    views.render(thing)
        except:
            self.x_entry.config(bg='red')

    def y_change(self, id, text, mode):
        try:
            if hasattr(self, 'y_var'):
                y = self.y_var.get()
                self.y_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.translate([0, y - thing.pos[1], 0])
                    views.render(thing)
        except Exception as e:
            self.y_entry.config(bg='red')

    def z_change(self, id, text, mode):
        try:
            if hasattr(self, 'z_var'):
                z = self.z_var.get()
                self.z_entry.config(bg='white')

                for thing in views.get_selected():
                    thing.translate([0, 0, z - thing.pos[2]])
                    views.render(thing)
        except:
            self.z_entry.config(bg='red')

    def rotate_roll(self):
        for thing in views.get_selected():
            thing.rotate(roll=1)
            views.render(thing)
    def rotate_pitch(self):
        for thing in views.get_selected():
            thing.rotate(pitch=1)
            views.render(thing)
    def rotate_yaw(self):
        for thing in views.get_selected():
            thing.rotate(yaw=1)
            views.render(thing)
        
        
class ExAl(Thing):
    def __init__(self, length, dim1, dim2):
        Thing.__init__(self)
        self.length = length
        self.dim1 = dim1
        self.dim2 = dim2
        self.orient = np.eye(3)
        self.pos = np.zeros(3)
        self.ids = [None, None, None]

    def dup(self):
        out = ExAl(self.length, self.dim1, self.dim2)
        out.orient = self.orient.copy()
        out.pos = self.pos.copy()
        return out

    def getstartstop(self):
        start = self.pos + self.orient @ [-self.dim1/2, -self.dim2/2, 0]
        stop = self.pos + self.orient @ np.array([self.dim1/2,
                                                  self.dim2/2,
                                                  self.length])
        return start, stop

    def toscad(self):
        q = quaternion.from_rotation_matrix(self.orient)
        angle = q.angle()
        out = [
            f'translate([{self.pos[0]:.4f}, {self.pos[1]:.4f}, {self.pos[2]:.4f}])',
            ]
        if self.selected:
            out[0] = '#' + out[0]
        if abs(angle) > 1e-8:
            vec = q.vec
            vec /= np.linalg.norm(vec)
            out.append(f'rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'bar({self.length}, {self.dim1}, {self.dim2});')
        return '\n'.join(out)
    
class View:
    def __init__(self, can, x=0, y=1, scale=1):
        self.can = can
        self.can.bind('<ButtonPress-1>', self.onpress)
        self.can.bind('<ButtonRelease-1>', self.onrelease)
        self.can.bind('<Motion>', self.ondrag)
        self.x = x
        self.y = y
        self.scale = scale
        self.things = {}
        self.dragging = False

    def get_selected(self):
        out = []
        for key in self.things:
            if self.things[key].selected:
                out.append(self.things[key])
        return out
    
    def render(self, thing):
        start, stop = thing.getstartstop()

        remove = []
        for id in self.things:
            if self.things[id] == thing:
                self.can.delete(id)
                remove.append(id)
        dragging = False
        for r in remove:
            del self.things[r]
            dragging = self.dragging
                
        if thing.selected:
            color = 'red'
            width = np.max([1, np.min([2 * self.scale, 3])])
        else:
            color = 'black'
            width = np.max([.5, np.min([1 * self.scale, 1.5])])

        ihat = np.eye(3)[self.x % 3]
        if self.x > 2:
            ihat *= -1
        jhat = np.eye(3)[self.y % 3]
        if self.y > 2:
            ihat *= -1
            
        id = self.can.create_rectangle(
            CANVAS_DIM/2 + self.scale * start[self.x], CANVAS_DIM/2 - self.scale * start[self.y],
            CANVAS_DIM/2 + self.scale * stop[self.x], CANVAS_DIM/2 - self.scale * stop[self.y],
            outline=color, width=width)
        if dragging:
            self.dragging = id
        self.things[id] = thing
        if thing.selected:
            self.can.tag_raise(id)
        else:
            self.can.tag_lower(id)
            
        return id
    
    def onpress(self, event):
        self.start=event.x, event.y
        clicked = self.can.find_closest(event.x, event.y)
        if len(clicked) > 0:
            dragging = clicked[0]
            if dragging in self.things:
                self.dragging = dragging
                thing = self.things[self.dragging]
                previously_selected = self.get_selected()

                for last in previously_selected:
                    last.selected = False
                    self.parent.render(last)
                thing.selected = True
                self.render(thing)
        
    def ondrag(self, event):
        if self.dragging:
            delta = np.zeros(3)
            delta[self.x] += (event.x - self.start[0]) / self.scale
            delta[self.y] -= (event.y - self.start[1]) / self.scale

            delta = (delta / 10).astype(int) * 10
            if np.linalg.norm(delta) > 0:
                id = self.dragging
                self.can.delete(id)
                if id in self.things:
                    thing = self.things[id]
                    thing.translate(delta)
                    del self.things[id]
                    self.dragging = self.render(thing)
                    self.start = [event.x, event.y]
            
    def onrelease(self, event):
        stop = event.x, event.y
        if self.dragging in self.things:
            thing = self.things[self.dragging]
            self.parent.render(thing)
            self.dragging = False
            sidebar.length_entry.delete(0, tk.END)
            sidebar.length_entry.insert(100, str(thing.length))
            sidebar.dim1_entry.delete(0, tk.END)
            sidebar.dim1_entry.insert(0, str(thing.dim1))
            sidebar.dim2_entry.delete(0, tk.END)
            sidebar.dim2_entry.insert(0, str(thing.dim2))

            sidebar.x_entry.delete(0, tk.END)
            sidebar.x_entry.insert(0, str(thing.pos[0]))
            sidebar.y_entry.delete(0, tk.END)
            sidebar.y_entry.insert(0, str(thing.pos[1]))
            sidebar.z_entry.delete(0, tk.END)
            sidebar.z_entry.insert(0, str(thing.pos[2]))

    def unselect_all(self):
        unselected = []
        for key in self.things:
            if self.things[key].selected:
                unselected.append(self.things[key])
        for thing in unselected:
            thing.selected = False
            self.parent.render(thing)

    def redraw(self):
        keys = list(self.things.keys())
        for key in keys:
            thing = self.things[key]
            self.render(thing)
    def set_scale(self, scale):
        self.scale = scale
        self.redraw()

    def delete_selected(self):
        delete_me = self.get_selected()
        delete_keys = []
        for key in self.things:
            thing = self.things[key]
            if thing in delete_me:
                delete_keys.append(key)
                self.can.delete(key)
        for key in delete_keys:
            del self.things[key]
class IsoView(View):
    def __init__(self, can, x, y, scale=1):
        self.can = can
        self.x = x
        self.y = y
        self.scale=scale
        self.things = {}

    def redraw(self):
        self.can.delete('all')
        for id in self.things:
            self.render(self.things[id])
        
    def render(self, thing):
        self.can.delete(str(thing))

        remove = []
        for id in self.things:
            if self.things[id] == thing:
                self.can.delete(id)
                remove.append(id)
        for id in remove:
            del self.things[id]
        line = np.array([0, 0, thing.length])
        s1 = thing.dim1/2
        s2 = thing.dim2/2
        if thing.selected:
            color = 'red'
            width = max([1, np.min([2 * self.scale, 3])])
        else:
            color = 'black'
            width = np.max([.5, np.min([1 * self.scale, 1.5])])
        for direction in np.array([[s1,   s2, 0],
                                   [s1,  -s2, 0],
                                   [-s1,  s2, 0],
                                   [-s1, -s2, 0]]):
            start = thing.pos + thing.orient @ direction
            stop = thing.pos + thing.orient @ (line + direction)
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x, CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x, CANVAS_DIM/2 + self.scale * stop @ self.y,
                tags=(str(thing),),
                fill=color, width=width)

        stop = thing.pos + thing.orient @ [-s1, -s2, 0]
        verts = np.array([[s1, -s2, 0],
                          [s1,  s2, 0],
                          [-s1, s2, 0],
                          [-s1, -s2, 0]])
        for v in verts:
            start = stop
            stop = thing.pos + thing.orient @ v
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x,
                CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x,
                CANVAS_DIM/2 + self.scale * stop @ self.y,
                tags=(str(thing),),
                fill=color, width=width)
        stop = thing.pos + thing.orient @ [-s1, -s2, thing.length]
        for v in verts:
            start = stop
            stop = thing.pos + thing.orient @ v + thing.orient @ [0, 0, thing.length]
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x,
                CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x,
                CANVAS_DIM/2 + self.scale * stop @ self.y, tags=(str(thing),),
                fill=color, width=width)
        self.things[id] = thing
        sidebar.export()
        if thing.selected:
            self.can.tag_raise(str(thing))
        else:
            self.can.tag_lower(str(thing))
        return id
    
    def delete_selected(self):
        delete_me = self.get_selected()
        for thing in delete_me:
            self.can.delete(str(thing))
            
        delete_keys = []
        for key in self.things:
            thing = self.things[key]
            if thing in delete_me:
                delete_keys.append(key)
        for key in delete_keys:
            self.can.delete(key)
            del self.things[key]
    def onpress(self, event):
        print(event)
class MultiView:
    def __init__(self, views):
        self.views = views
        for view in self.views:
            view.parent = self
    def render(self, thing):
        for view in self.views:
            view.render(thing)
    def callback(self, thing):
        for view in self.views:
            view.update()
    def select_all(self, *args):
        for key in self.views[0].things:
            self.views[0].things[key].selected = True
            self.render(self.views[0].things[key])
    def unselect_all(self):
        for view in self.views:
            view.unselect_all()
    def get_selected(self):
        return self.views[0].get_selected()
    def set_scale(self, scale):
        for view in self.views:
            view.set_scale(scale)
    def delete_selected(self, *args):
        for view in self.views:
            view.delete_selected()
        sidebar.export()
    def delete_all(self, *args):
        self.select_all()
        self.delete_selected()
        self.select_all()
        self.delete_selected()
    def delete(self, thing):
        for view in self.views:
            view.delete(thing)
        sidebar.export()
    def dup_selected(self, *args):
        for thing in iso.get_selected():
            dup = thing.dup()
            self.render(dup)

def cancel(*args):
    '''
    unselect all
    '''
    views.unselect_all()
    sidebar.length_var.set(100)    
    sidebar.dim1_var.set(20)    
    sidebar.dim2_var.set(20)    
    sidebar.x_var.set(0)    
    sidebar.y_var.set(0)    
    sidebar.z_var.set(0)
    
def clear_all(*args):
    views.delete_all()

        
root = tk.Tk()
root.bind('<Escape>', cancel)
sidebar = SideBar(root, 10, 800)


topcan = tk.Canvas(root, width = CANVAS_DIM, height=CANVAS_DIM)
topcan.create_rectangle(5, 5, 399, 399)
topcan.grid(row=1, column=2);


sidecan = tk.Canvas(root, width = CANVAS_DIM, height=CANVAS_DIM)
sidecan.create_rectangle(5, 5, 399, 399)
sidecan.grid(row=1, column=3);

frontcan = tk.Canvas(root, width = CANVAS_DIM, height=CANVAS_DIM)
frontcan.create_rectangle(5, 5, 399, 399)
frontcan.grid(row=2, column=2);

isocan = tk.Canvas(root, width = CANVAS_DIM, height=CANVAS_DIM)
isocan.create_rectangle(5, 5, 399, 399)
isocan.grid(row=2, column=3);

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

print('pov', pov)
iso_z  = np.array([0, 0, 1])
iso_z = iso_z - (iso_z @ pov) * pov
iso_z /= np.linalg.norm(iso_z)
print(iso_z)
iso_x = np.cross(pov, iso_z)
iso_y = np.cross(iso_z, iso_x)

top = View(topcan, 0, 1, scale)
side = View(sidecan, 2, 1, scale)
front = View(frontcan, 0, 2, scale)
iso = IsoView(isocan, -iso_x , iso_y , scale=scale)
views = MultiView([top, side, front, iso])
root.bind('<Delete>', views.delete_selected)
#oroot.bind('<BackSpace>', views.delete_selected)
root.bind('<Control-d>', views.dup_selected)
root.bind('<Control-n>', sidebar.new_part)
root.bind('<Control-a>', views.select_all)


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
        
        part = ExAl(h - 2 * d1, d1, d2); part.translate([-l/2 + d1/2, -w/2 + d2/2, d1]);views.render(part)
        part = ExAl(h - 2 * d1, d1, d2); part.translate([-l/2 + d1/2,  w/2 - d2/2, d1]);views.render(part)
        part = ExAl(h - 2 * d1, d1, d2); part.translate([ l/2 - d1/2, -w/2 + d2/2, d1]);views.render(part)
        part = ExAl(h - 2 * d1, d1, d2); part.translate([ l/2 - d1/2,  w/2 - d2/2, d1]);views.render(part)

        part = ExAl(l, d1, d2)
        part.rotate(pitch=-1)
        part.translate([-l/2, -w/2 + d2/2, d1/2])
        views.render(part)
        part = part.dup()
        part.translate([0, w - d2, 0])
        views.render(part)
        part = part.dup()
        part.translate([0, 0, h - d1])
        views.render(part)
        part = part.dup()
        part.translate([0, -w + d2, 0])
        views.render(part)
        
        part = ExAl(w - 2 * d2, d1, d2)
        part.rotate(roll=1)
        part.translate([l/2-d1/2, w/2 - d2, d2/2])
        views.render(part)

        part = part.dup()
        part.translate([0, 0, h - d2])
        views.render(part)

        part = part.dup()
        part.translate([-l + d1, 0, 0])
        views.render(part)

        part = part.dup()
        part.translate([0, 0, -h + d2])
        views.render(part)

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
                                                noop)
    d1_frame.grid(row=4, column=1)
    d2_frame, d2_entry, d2_var = NumericalEntry(frame,
                                                'D2:',
                                                noop)
    d2_frame.grid(row=5, column=1)
    
    
    
    l_var.set(200);
    w_var.set(150);
    h_var.set(300);
    d1_var.set(20);
    d2_var.set(20);
    frame.grid(row=1, column=1)

    button_f = tk.Frame(frame)
    button_f.grid(row=6, column=1)
    tk.Button(button_f, text="Ok", command=on_submit).grid(row=1, column=1)
    tk.Button(button_f, text="Cancel", command=on_cancel).grid(row=1, column=2)

exal_filename = [] ### use as mutable string
def exal_save():
    if len(exal_filename) == 0:
        filename = filedialog.asksaveasfilename(#initialdir = "/",
            title = "Select file",
            filetypes = (("Extruded AL","*.exal"),
                         ("all files","*.*")))
    else:
        filename = exal_filename[0]
    f = open(filename, 'wb')
    pickle.dump(list(top.things.items()), f)

def exal_save_as():
    filename = filedialog.asksaveasfilename(#initialdir = "/",
                                            title = "Select file",
                                            filetypes = (("Extruded AL","*.exal"),
                                                         ("all files","*.*")))
    while len(exal_filename) > 0:
        exal_filename.pop()
    exal_filename.append(filename)
    f = open(filename, 'wb')
    pickle.dump(list(top.things.items()), f)

def exal_new():
    while len(exal_filename) > 0:
        exal_filename.pop()
    clear_all()
    
def exal_import():
    filename = filedialog.askopenfilename(#initialdir = "/",
                                          title = "Select file",
                                          filetypes = (("Extruded AL","*.exal"),
                                                       ("all files","*.*")))
    f = open(filename, 'rb')
    things = pickle.load(f)
    for key, thing in things:
        views.render(thing)
    views.unselect_all()
def exal_open():
    filename = filedialog.askopenfilename(#initialdir = "/",
                                          title = "Select file",
                                          filetypes = (("Extruded AL","*.exal"),
                                                       ("all files","*.*")))
    while len(exal_filename) > 0:
        exal_filename.pop()
    exal_filename.append(filename)
    f = open(filename, 'rb')
    things = pickle.load(f)
    clear_all()
    for key, thing in things:
        views.render(thing)
    views.unselect_all()

menubar = tk.Menu(root)
# create a pulldown menu, and add it to the menu bar
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="New", command=exal_new)
filemenu.add_command(label="Open", command=exal_open)
filemenu.add_command(label="Import", command=exal_import)
filemenu.add_command(label="Save", command=exal_save)
filemenu.add_command(label="Save As", command=exal_save_as)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

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

#bb = ExAl(length, d1,d2)
#views.render(bb);
if False:
    base = [ExAl(length, w),
            ExAl(width, w),
            ExAl(length, w),
            ExAl(width, w),
    ]
    base[0].translate([OFFSET, OFFSET, OFFSET])
    base[1].rotate(pitch=-1)
    base[1].translate([OFFSET + w/2,  OFFSET, OFFSET + w/2])
    base[2].translate([OFFSET + width + w, OFFSET, OFFSET])
    base[3].rotate(pitch=-1)
    base[3].translate([OFFSET + w / 2, OFFSET, OFFSET + length - w / 2])
    for b in base:
        views.render(b)
if False:
    sides = []
    for i in range(4):
        side = ExAl(height, w)
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
    top = [ExAl(length, w),
            ExAl(width, w),
            ExAl(length, w),
            ExAl(width, w),
    ]
    top[0].translate([OFFSET, OFFSET, OFFSET + w + height])
    top[1].rotate(yaw=1)
    top[1].translate([length + OFFSET + w/2, OFFSET - w/2, height + OFFSET + w])
    top[2].translate([OFFSET, width + OFFSET - w, height + OFFSET + w])
    top[3].rotate(yaw=1)
    top[3].translate([OFFSET - w/2, OFFSET - w/2, height + OFFSET + w])
    for t in top:
        views.render(t)


#exal.render(topview, sideview, frontview, .5)
#exal.rotate(pitch=1)
#exal.translate([OFFSET, OFFSET, OFFSET])
#exal.render(topview, sideview, frontview, .5)
#topview.create_line(15, 25, 200, 25)
# print(top[0].toscad())

shift_tracker = ShiftTracker(root)
import os

root.mainloop()
