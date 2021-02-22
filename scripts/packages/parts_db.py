import tkinter as tk
import things
import os
import os.path
import numpy as np
import sqlite3
import database
from database import String, Integer, Float, Table, Column
import csv
import wireframes
from constants import DEG, alex_scad, stl_dir
import webbrowser

from PIL import ImageTk, Image
#import MyTable
from mylistbox import listbox

mydir = os.path.split(os.path.abspath(__file__))[0]
db_fn = os.path.join(mydir, 'Alex_parts.db')
db = sqlite3.connect(db_fn)

interface_table = Table("Interface", db,
                        Column("Name", String(), UNIQUE=True),
                        Column("Hotspot_x", Float()),
                        Column("Hotspot_y", Float()),
                        Column("Hotspot_z", Float()),
                        Column("Direction_x", Float()),
                        Column("Direction_y", Float()),
                        Column("Direction_z", Float()))
interface_table.create()
L = 0xdeadbeef
interface_table.insert([
    ["2020+X", 10,  0, 10, 1, 0, 0],
    ["2020+Y",  0, 10, 10, 0, 1, 0],
    ["2020+Z",  0,  0,  L, 0, 0, 1],
    ["2020-X",-10,  0,-10,-1, 0, 0],
    ["2020-Y",  0,-10,-10, 0,-1, 0],
    ["2020-Z",  0,  0,  0, 0, 0,-1],
    
    ["3030+X", 15, 0, 15, 1, 0, 0],
    ["3030+Y", 0, 15, 15, 0, 1, 0],
    ["3030+Z", 15, 15, L, 0, 0, 1],
    ["3030-X",-15, 0, 15,-1, 0, 0],
    ["3030-Y", 0,-15, 15, 0,-1, 0],
    ["3030-Z", 0,  0,  0, 0, 0,-1]])

def lookup_interface(name):
    interfaces = interface_table.select(where=f'name="{name}"')
    if len(interfaces) == 0:
        raise ValueError(f"Interface named {name} not found")
    record = interfaces[0]
    record.hotspot = np.array([record.Hotspot_x,record.Hotspot_y,record.Hotspot_z])
    record.direction = np.array([record.Direction_x,record.Direction_y,record.Direction_z])
    return record

part_table = Table('Part', db,
                   Column('Name',String(), UNIQUE=True),
                   Column('Wireframe', Integer()),
                   Column('STL_filename', String()),
                   Column('Price', Float()),
                   Column('URL', String()),
                   Column('Color', String()),
                   Column('Length', Integer()),
                   Column('Width', Integer()),
                   Column('Height', Integer()),
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


class Part(things.Thing):
    def __init__(self, name, length=1):
        record = get(name)
        if record:
            things.Thing.__init__(self)
            self.name = name
            self.dim1 = record.Length
            self.dim2 = record.Width
            if record.Height == '0xdeadbeef':
                self.length = length
            else:
                self.length = record.Height
            self.wireframe = wireframes.get(record.Wireframe) * [self.dim1, self.dim2, self.length]
            self.stl_fn = os.path.join(mydir, 'STL', record.STL_filename)
            self.color = record.Color
            self.record = record
            
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
    
def test():
    load_parts(csv_fn)
    f = open('../Alex_test.scad', 'w')
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

if __name__ == '__main__':
    test()
