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
class Thing:
    def __init__(self):
        self.selected = False

def NumericalEntry(parent, label, onchange, from_=-1e6, to=1e6, values=None, increment=1):
    frame = tk.Frame(parent)
    var = tk.DoubleVar()
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
        self.dim_frame, self.dim_entry, self.dim_var = NumericalEntry(self.frame,
                                                                      'D:',
                                                                      self.dim_change,
                                                                      increment=10)
        self.dim_frame.grid(row=2, column=1)
        self.x_frame, self.x_entry, self.x_var = NumericalEntry(self.frame,
                                                                'x:',
                                                                self.x_change)
        self.x_frame.grid(row=3, column=1)
        self.y_frame, self.y_entry, self.y_var = NumericalEntry(self.frame,
                                                                'y:',
                                                                self.y_change)
        self.y_frame.grid(row=4, column=1)
        self.z_frame, self.z_entry, self.z_var = NumericalEntry(self.frame,
                                                                'z:',
                                                                self.z_change)
        self.z_frame.grid(row=5, column=1)

        self.roll_button = tk.Button(self.frame, command=self.rotate_roll, text='Roll')
        self.roll_button.grid(row=6, column=1)
        self.pitch_button = tk.Button(self.frame, command=self.rotate_pitch, text='Pitch')
        self.pitch_button.grid(row=7, column=1)
        self.yaw_button = tk.Button(self.frame, command=self.rotate_yaw, text='Yaw')
        self.yaw_button.grid(row=8, column=1)
        
        self.new_part_button = tk.Button(self.frame, command=self.new_part, text='New Part')
        self.new_part_button.grid(row=9, column=1)

        self.zoom_in_button = tk.Button(self.frame, command=self.zoom_in, text='Zoom In')
        self.zoom_in_button.grid(row=10, column=1)

        self.zoom_out_button = tk.Button(self.frame, command=self.zoom_out, text='Zoom Out')
        self.zoom_out_button.grid(row=11, column=1)

        #self.export_button = tk.Button(self.frame, command=self.export, text='Export')
        #self.export_button.grid(row=12, column=1)

    def new_part(self):
        views.unselect_all()
        length = max([0, sidebar.length_var.get()])
        w = np.max([20, sidebar.dim_var.get()])
        x = sidebar.x_var.get()
        y = sidebar.x_var.get()
        z = sidebar.x_var.get()
        part = ExAl(length, w)
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
module bar(l, w){
  linear_extrude(l)
    scale(w/30)import(file = "../resources/30-30.dxf");
}\n
'''
        scad = 'Alex_test.scad'
        f = open(scad, 'w')
        f.write(header)
        for key in iso.objs:
            f.write(iso.objs[key].toscad())
            f.write('\n')
        f.close()
            
    def length_change(self, id, text, mode):
        try:
            length = self.length_var.get()
            self.length_entry.config(bg='white')

            for obj in views.get_selected():
                obj.length = length
                views.render(obj)
        except:
            self.length_entry.config(bg='red')
    def dim_change(self, id, text, mode):
        try:
            dim = self.dim_var.get()
            self.dim_entry.config(bg='white')

            for obj in views.get_selected():
                obj.side = dim
                views.render(obj)
        except Exception as e:
            self.dim_entry.config(bg='red')
    def x_change(self, id, text, mode):
        try:
            x = self.x_var.get()
            self.x_entry.config(bg='white')

            for obj in views.get_selected():
                obj.translate([x - obj.pos[0], 0, 0])
                views.render(obj)
        except:
            self.x_entry.config(bg='red')

    def y_change(self, id, text, mode):
        try:
            y = self.y_var.get()
            self.y_entry.config(bg='white')

            for obj in views.get_selected():
                obj.translate([0, y - obj.pos[1], 0])
                views.render(obj)
        except Exception as e:
            self.y_entry.config(bg='red')

    def z_change(self, id, text, mode):
        try:
            z = self.z_var.get()
            self.z_entry.config(bg='white')

            for obj in views.get_selected():
                obj.translate([0, 0, z - obj.pos[2]])
                views.render(obj)
        except:
            self.z_entry.config(bg='red')

    def rotate_roll(self):
        for obj in views.get_selected():
            obj.rotate(roll=1)
            views.render(obj)
    def rotate_pitch(self):
        for obj in views.get_selected():
            obj.rotate(pitch=1)
            views.render(obj)
    def rotate_yaw(self):
        for obj in views.get_selected():
            obj.rotate(yaw=1)
            views.render(obj)
        
        
class ExAl(Thing):
    def __init__(self, length, side):
        Thing.__init__(self)
        self.length = length
        self.side = side
        self.orient = np.eye(3)
        self.pos = np.zeros(3)
        self.ids = [None, None, None]

    def dup(self):
        out = ExAl(self.length, self.side)
        out.orient = self.orient.copy()
        out.pos = self.pos.copy()
        return out
    
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

    def getstartstop(self):
        #start = self.pos + self.orient @ [0, -self.side/2, -self.side/2]
        #stop = self.pos + self.orient @ np.array([self.length,
        #                                          self.side/2,
        #                                          self.side/2])
        start = self.pos + self.orient @ [-self.side/2, -self.side/2, 0]
        stop = self.pos + self.orient @ np.array([self.side/2,
                                                  self.side/2,
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
        out.append(f'bar({self.length}, {self.side});')
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
        self.objs = {}
        self.dragging = False

    def get_selected(self):
        out = []
        for key in self.objs:
            if self.objs[key].selected:
                out.append(self.objs[key])
                return out
        return out
    
    def render(self, obj):
        start, stop = obj.getstartstop()

        remove = []
        for id in self.objs:
            if self.objs[id] == obj:
                self.can.delete(id)
                remove.append(id)
        dragging = False
        for r in remove:
            del self.objs[r]
            dragging = self.dragging
                
        if obj.selected:
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
        self.objs[id] = obj
        return id
    
    def onpress(self, event):
        self.start=event.x, event.y
        clicked = self.can.find_closest(event.x, event.y)
        if len(clicked) > 0:
            dragging = clicked[0]
            if dragging in self.objs:
                self.dragging = dragging
                obj = self.objs[self.dragging]
                last = None
                for key in self.objs:
                    if self.objs[key].selected:
                        last = self.objs[key]

                if last is not None:
                    last.selected = False
                    self.parent.render(last)
                obj.selected = True
                self.render(obj)
        
    def ondrag(self, event):
        if self.dragging:
            delta = np.zeros(3)
            delta[self.x] += (event.x - self.start[0]) / self.scale
            delta[self.y] -= (event.y - self.start[1]) / self.scale

            delta = (delta / 10).astype(int) * 10
            if np.linalg.norm(delta) > 0:
                id = self.dragging
                self.can.delete(id)
                if id in self.objs:
                    obj = self.objs[id]
                    obj.translate(delta)
                    del self.objs[id]
                    self.dragging = self.render(obj)
                    self.start = [event.x, event.y]
            
    def onrelease(self, event):
        stop = event.x, event.y
        if self.dragging in self.objs:
            obj = self.objs[self.dragging]
            self.parent.render(obj)
            self.dragging = False
            sidebar.length_entry.delete(0, tk.END)
            sidebar.length_entry.insert(0, str(obj.length))
            sidebar.dim_entry.delete(0, tk.END)
            sidebar.dim_entry.insert(0, str(obj.side))

            sidebar.x_entry.delete(0, tk.END)
            sidebar.x_entry.insert(0, str(obj.pos[0]))
            sidebar.y_entry.delete(0, tk.END)
            sidebar.y_entry.insert(0, str(obj.pos[1]))
            sidebar.z_entry.delete(0, tk.END)
            sidebar.z_entry.insert(0, str(obj.pos[2]))

    def unselect_all(self):
        unselected = []
        for key in self.objs:
            if self.objs[key].selected:
                unselected.append(self.objs[key])
        for obj in unselected:
            obj.selected = False
            self.parent.render(obj)

    def redraw(self):
        keys = list(self.objs.keys())
        for key in keys:
            obj = self.objs[key]
            self.render(obj)
    def set_scale(self, scale):
        self.scale = scale
        self.redraw()

    def delete_selected(self):
        delete_me = self.get_selected()
        delete_keys = []
        for key in self.objs:
            obj = self.objs[key]
            if obj in delete_me:
                delete_keys.append(key)
                self.can.delete(key)
        for key in delete_keys:
            del self.objs[key]
class IsoView(View):
    def __init__(self, can, x, y, scale=1):
        self.can = can
        self.x = x
        self.y = y
        self.scale=scale
        self.objs = {}

    def redraw(self):
        self.can.delete('all')
        for id in self.objs:
            self.render(self.objs[id])
        
    def set_pov(self, x, y):
        self.x = x
        self.y = y
        self.redraw()
        self.can.delete('all')
        for id in self.objs:
            self.render(self.objs[id])
    def render(self, obj):
        self.can.delete(str(obj))
        for id in self.objs:
            if self.objs[id] == obj:
                self.can.delete(id)
        line = np.array([0, 0, obj.length])
        s = obj.side/2
        if obj.selected:
            color = 'red'
            width = max([1, np.min([2 * self.scale, 3])])
        else:
            color = 'black'
            width = np.max([.5, np.min([1 * self.scale, 1.5])])
        for direction in np.array([[s,   s, 0],
                                   [s,  -s, 0],
                                   [-s,  s, 0],
                                   [-s, -s, 0]]):
            start = obj.pos + obj.orient @ direction
            stop = obj.pos + obj.orient @ (line + direction)
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x, CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x, CANVAS_DIM/2 + self.scale * stop @ self.y,
                tags=(str(obj),),
                fill=color, width=width)

        stop = obj.pos + obj.orient @ [s, -s, 0]
        for i in np.arange(4) * np.pi/2 + np.pi/4:
            start = stop
            stop = obj.pos + obj.orient @ [cos(i), sin(i), 0] * s * sqrt(2)
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x,
                CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x,
                CANVAS_DIM/2 + self.scale * stop @ self.y,
                tags=(str(obj),),
                fill=color, width=width)
        stop = obj.pos + obj.orient @ [s, -s, obj.length]
        for i in np.arange(4) * np.pi/2 + np.pi/4:
            start = stop
            stop = obj.pos + obj.orient @ [cos(i), sin(i), 0] * s * sqrt(2) + obj.orient @ [0, 0, obj.length]
            id = self.can.create_line(
                CANVAS_DIM/2 + self.scale * start @ self.x,
                CANVAS_DIM/2 + self.scale * start @ self.y,
                CANVAS_DIM/2 + self.scale * stop @ self.x,
                CANVAS_DIM/2 + self.scale * stop @ self.y, tags=(str(obj),),
                fill=color, width=width)
        self.objs[id] = obj
        sidebar.export()
        return id
    
    def delete_selected(self):
        delete_me = self.get_selected()
        for obj in delete_me:
            self.can.delete(str(obj))
            
        delete_keys = []
        for key in self.objs:
            obj = self.objs[key]
            if obj in delete_me:
                delete_keys.append(key)
        for key in delete_keys:
            self.can.delete(key)
            del self.objs[key]
    def onpress(self, event):
        print(event)
class MultiView:
    def __init__(self, views):
        self.views = views
        for view in self.views:
            view.parent = self
    def render(self, obj):
        for view in self.views:
            view.render(obj)
    def callback(self, obj):
        for view in self.views:
            view.update()
    def select_all(self, *args):
        print('select_all')
        for key in self.views[0].objs:
            self.views[0].objs[key].selected = True
            self.render(self.views[0].objs[key])
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
    def dup_selected(self, *args):
        for obj in iso.get_selected():
            dup = obj.dup()
            self.render(dup)

def cancel(*args):
    '''
    unselect all
    '''
    views.unselect_all()
    sidebar.length_var.set(100)    
    sidebar.dim_var.set(20)    
    sidebar.x_var.set(0)    
    sidebar.y_var.set(0)    
    sidebar.z_var.set(0)    
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
root.bind('<Control-d>', views.dup_selected)
root.bind('<Control-a>', views.select_all)

length = 100
width = 150
height = 125
w = 20
OFFSET = 0

bb = ExAl(length, w)
views.render(bb);
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

root.mainloop()
