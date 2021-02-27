import tkinter as tk
import os
import os.path
import numpy as np
import sqlite3
import csv
import webbrowser
from PIL import ImageTk, Image

import sys
if '.' not in sys.path:
    sys.path.append('.')
from packages import util
from packages import things
from packages import database
from packages.database import String, Integer, Float, Table, Column
from packages import wireframes
from packages.constants import DEG, alex_scad, stl_dir

from packages.mylistbox import listbox

mydir = os.path.split(os.path.abspath(__file__))[0]
db_fn = os.path.join(mydir, 'Alex_parts.db')
db = sqlite3.connect(db_fn)


L = 0xdeadbeef
interface_table = {"2020+X":[  10,  0, 10, 1, 0, 0],
                   "2020+Y":[   0, 10, 10, 0, 1, 0],
                   "2020+Z":[   0,  0,  5, 0, 0, 1],
                   "2020-X":[ -10,  0, 10,-1, 0, 0],
                   "2020-Y":[   0,-10, 10, 0,-1, 0],
                   "2020-Z":[   0,  0,  0, 0, 0,-1],
                   
                   "3030+X":[ 15, 0, 15, 1, 0, 0],
                   "3030+Y":[ 0, 15, 15, 0, 1, 0],
                   "3030+Z":[ 15, 15, 6, 0, 0, 1],
                   "3030-X":[-15, 0, 15,-1, 0, 0],
                   "3030-Y":[ 0,-15, 15, 0,-1, 0],
                   "3030-Z":[ 0,  0,  0, 0, 0,-1]}
@util.cacheable
def lookup_interface(name):
    if name not in interface_table:
        raise ValueError(f"Interface named {name} not found")
    record = interface_table[name]
    hotspot = np.array(record[:3])
    direction = np.array(record[3:])
    return Interface(name, hotspot, direction)

part_table = Table('Part', db,
                   Column('Name',String(), UNIQUE=True),
                   Column('Wireframe', Integer()),
                   Column('STL_filename', String()),
                   Column('Price', Float()),
                   Column('URL', String()),
                   Column('Color', String()),
                   Column('Length', Integer()),
                   Column('Dim1', Integer()),
                   Column('Dim2', Integer()),
                   Column('Interface_01', Integer()),
                   Column('Interface_02', Integer()),
                   Column('Interface_03', Integer()),
                   Column('Interface_04', Integer()),
                   Column('Interface_05', Integer()),
                   Column('Interface_06', Integer())
)

part_table.create()

mydir = os.path.split(os.path.abspath(__file__))[0]
csv_fn = os.path.join(mydir, 'parts.csv')
def load_parts(csv_fn):
    csv_file = open(csv_fn)
    data = list(csv.reader(csv_file))
    csv_file.close()
    header = data[0]
    data = data[1:]
    for i, l in enumerate(data):
        for j, c in enumerate(l):
            l[j] = l[j].strip()
        for j in range(9, 15):
            interface_name = l[j]
            if interface_name != "NA":
                interface = lookup_interface(interface_name)
                assert interface
                # print('Interface:', interface.hotspot, interface.direction)
    
    part_table.insert(data)


#print(part_table.select())

def get(name):
    record = part_table.select(where=f'Name="{name}"') ## name is unique
    if len(record) == 0:
        raise ValueError(f"No item named {name}.")
    return record[0]

class Interface:
    def __init__(self, name, hotspot, direction):
        self.name = name
        self.hotspot = hotspot
        self.direction = direction
    def __repr__(self):
        return f'Interface("{self.name}", {self.hotspot}, {self.direction})'
    def get_pos_dir(self, owner):
        p = owner.pos + owner.orient @ self.hotspot
        d = owner.orient @ self.direction
        return p, d

    def engaged_with(self, proj, p2, owner_bb, owner, thing):
        wf = thing.get_wireframe()
        wf2d = wf @ proj
        hull = util.convexhull(wf2d)[0][:-1]
        mn = np.min(hull, axis=0)
        mx = np.max(hull, axis=0)
        midpoint = (mx + mn) / 2
        if np.linalg.norm(midpoint - p2) < .01:
            ## check flush with owner
            if np.min(np.abs(np.roll(owner_bb, 3) - np.hstack(thing.get_boundingbox()))) < .01:
                return True
        return False
    
    def engaged(self, owner, group=None):
        '''
        self.direction is in line with another part
        part not overlapping
        -- cant be engages with a Group... unless part of that same group
        '''
        if group is None:
            group = things.TheScene
            
        p, d = self.get_pos_dir(owner)
        i = np.argmin(abs(d)) ### most orthongonal axis
        u0 = np.zeros(3)
        u0[i] = 1
        u0 = u0 - (d @ u0) * d
        u0 /= np.linalg.norm(u0)
        u1 = np.cross(d, u0)
        U = np.column_stack([u0, u1])

        # projection orthognal to direction
        proj = U
        p2 = p @ U
        
        owner_bb = np.hstack(owner.get_boundingbox())

        for thing in group:
            if thing.iscontainer():
                continue ### cant interface w/ a group
                gp = thing
                if self.engaged(owner, gp):
                    return True
            elif thing is not owner:
                if self.engaged_with(proj, p2, owner_bb, owner, thing):
                    return True
        return False
    
class Part(things.Thing):
    def __init__(self, name, length=1):
        record = get(name)
        print(record)
        if record:
            things.Thing.__init__(self)
            self.name = name
            self.dim1 = record.Dim1
            self.dim2 = record.Dim2
            if record.Length == '0xdeadbeef':
                self.length = length
            else:
                self.length = record.Length
            print(name, self.dim1, self.dim2, self.length)
            self.wireframe = wireframes.get(record.Wireframe) * [self.dim1, self.dim2, self.length]
            self.stl_fn = os.path.join(mydir, 'STL', record.STL_filename)
            self.color = record.Color
            self.record = record
            
            self.interfaces = []
            for i in range(1, 7):
                k = f'Interface_{i:02d}'
                name = self.record[k]
                if name != 'NA':
                    interface = lookup_interface(name)
                    self.interfaces.append(interface)
    def __rescale_wireframe(self):
        self.wireframe = wireframes.get(self.record.Wireframe) * [self.dim1, self.dim2, self.length]
        
    def set_length(self, length):
        if self.record.Height == '0xdeadbeef':
            things.Thing.set_length(self, length)
            self.__rescale_wireframe()
        
    def get_wireframe(self):
        return self.wireframe @ self.orient.T + self.pos

    def get_verts(self):
        wf = self.get_wireframe()
        keep = np.where(np.logical_not(np.isnan(wf[:,0])))
        return wf[keep]
    
    def render(self, view, selected=False):
        view.erase(self)
        if selected:
            color = self.select_color
            width = max([1, np.min([view.get_scale(), 3])])
        else:
            color = self.normal_color
            width = max([1, np.min([view.get_scale(), 1.5])])
        wireframe = self.get_wireframe()
        view.create_path(self, wireframe, color, width)
        return ### interfaces are too slow to render on every render :-(
        for interface in self.interfaces:
            if not interface.engaged(self): ## too slow
                p, d = interface.get_pos_dir(self)
                r = int(abs(d[0] * 255))
                g = int(abs(d[1] * 255))
                b = int(abs(d[2] * 255))
                color = f'#{r:02x}{g:02x}{b:02x}'
                view.create_line(self, p, p + 5 * d, color, width)
    
    def toscad(self):
        pos = self.pos
        out = []
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'translate([{pos[0]}, {pos[1]}, {pos[2]}])')
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  color("{self.color}")scale([{self.dim1}, {self.dim2}, {self.length}])import("{self.stl_fn}");')
        return '\n'.join(out)

    def dup(self):
        out = Part(self.name, self.length)
        out.translate(self.pos)
        out.orient = self.orient.copy()
        return out
    def cost(self):
        return 0
    def tobom(self):
        return [f'{self.name},{self.dim1},{self.dim2},{self.length},{self.cost()}']

def curry(f, arg):
    def out(event):
        f(arg)
    return out
imgs = [None]
def url_shortener(url, max_len=40):
    url = url.strip()
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    if len(url)> max_len:
        url = url[:max_len - 3] + '...'
    return url

def PartDialog(parent, select_cb):
    parts = part_table.select()
    columns = list(parts[0].keys())[:9]
    
    
    n_col = len(columns)
    tl = tk.Toplevel(parent)
    
    data = [[getattr(line, name) for name in columns] for line in parts]
    names = [l[0] for l in data]
    idx = np.argsort(names)
    parts = [parts[i] for i in idx]
    names = [names[i] for i in idx]
    url_col = 4

    def browseto(*args):
        part = item_clicked.part
        if part:
            url = part.record.URL
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]
            webbrowser.open_new(url)
    
    def item_clicked(idx, name):
        part = Part(name)
        name = ''.join(name.split())
        img = ImageTk.PhotoImage(Image.open(os.path.join(stl_dir, f'{name}.png')))
        display.configure(image=img)
        display.image = img

        url.configure(text=url_shortener(data[idx][url_col], max_len=70))
        url.bind("<Button-1>", browseto)
        f = open(alex_scad, 'w')
        f.write(part.toscad())
        f.close()
        item_clicked.part = part
    def cancel(*args):
        tl.destroy()
    def select():
        part = item_clicked.part
        select_cb(part)
        cancel()
    def item_selected(idx, name):
        item_clicked(idx, name)
        select()
        
        
    lb = listbox(tl, names, item_clicked, item_selected, n_row=50)
    lb.grid(row=0, column=0, rowspan=10)

    img = ImageTk.PhotoImage(Image.open(os.path.join(stl_dir, f'2020CornerTwoWay.png')))
    imgs[0] = img
    display = tk.Label(tl, image=img)
    display.grid(row=0, column=2, sticky='N', columnspan=4)

    url = tk.Label(tl)
    url.configure(fg='blue')
    url.grid(row=1, column=2, sticky='NW', columnspan=4)
    url.bind('<Button-1>', browseto)

    cancel_button = tk.Button(tl, text="Cancel", command=cancel)
    cancel_button.grid(row=2, column=4, sticky='NE')
    select_button = tk.Button(tl, text="Select", command=select)
    select_button.grid(row=2, column=5, sticky='NW')
    
    item_clicked(0, names[0])
    return tl

def make_thumbnails():
    import os
    load_parts(csv_fn)
    parts = part_table.select()
    for part in parts:
        print(part.Name)
        print(Part(part.Name).toscad())
        f = open('../Alex_test.scad', 'w')
        f.write(Part(part.Name).toscad())
        f.close()
        name = ''.join(part.Name.split())
        os.system(f"/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD ../Alex_test.scad --imgsize=512,512 -o STL/{name}.png")
#make_thumbnails();here
    
def test_part_select():
    load_parts(csv_fn)
    f = open(alex_scad, 'w')
    #f.write(Part("2020 Alex", 80).toscad())
    #f.write(Part("2040 Alex", 60).translate([20, 0, 0]).toscad())
    #f.write(Part("2060 Alex", 40).toscad())
    #f.write(Part("2080 Alex", 20).toscad())
    #f.write(Part("3060 Alex", 10).toscad())
    part = Part("2020 Corner Two Way")
    f.write(part.toscad())
    f.write(Part("3030 Corner Three Way").translate([30, 0, 0]).toscad())
    f.close()

    r = tk.Tk()
    def select_cb(part):
        print(part)
    PartDialog(r, select_cb)
    r.mainloop()

def new_part_dialog(parent):
    from packages import piecewise_linear_cost_model as cm
    '''
    Entry: Column('Name',String(), UNIQUE=True)
    FileDialog: Column('Wireframe', Integer())
    FileDialog: Column('STL_filename', String())
    Entry: Column('Price', Float())
    Entry: Column('URL', String())
    Entry: Column('Color', String())
    Entry: Column('Length', Integer())
    Column('Dim1', Integer())
    Column('Dim2', Integer())
    Column('Interface_01', Integer())
    Column('Interface_02', Integer())
    Column('Interface_03', Integer())
    Column('Interface_04', Integer())
    Column('Interface_05', Integer())
    Column('Interface_06', Integer())
    '''
    frame, can, len_vars, cost_vars = cm.piecewise_linear_cost_model(parent)
    frame.grid()
    return frame, can, len_vars, cost_vars

def test_new_part_dialog():
    from packages import piecewise_linear_cost_model as cm

    root = tk.Tk()
    frame, can, len_vars, cost_vars = new_part_dialog(root)
    root.mainloop()
    print("Table:")
    print(cm.get_table(len_vars, cost_vars))

    
if __name__ == '__main__':
    #test_part_select()
    test_new_part_dialog()
