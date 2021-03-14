import shutil
import glob
import re
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import colorchooser
from tkinter import messagebox
from tkinter import simpledialog
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
from packages import constants
from packages.util import curry
from packages import things
from packages import wireframes
from packages import database
from packages.database import String, Integer, Float, Table, Column
from packages.constants import DEG, alex_scad, bgcolor, openscad_path, part_libraries_dir
from packages.interpolate import interp1d
from packages.mylistbox import listbox
from packages import piecewise_linear_cost_model as cm

mydir = os.path.split(os.path.abspath(__file__))[0]
db_fn = os.path.join(part_libraries_dir, 'Main', 'Parts.db')

interface_table = {
    "NA": [None] * 6,
    "2020+X":[  10,  0, 10, 1, 0, 0],
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
    "3030-Z":[ 0,  0,  0, 0, 0,-1]
}

def assimilate_stl(lib, part_name, fn, copy_only=False):
    base = os.path.split(fn)[1]
    std_fn = f'{lib.stl_dir}/{base}'
    if os.path.exists(std_fn):
        new_fn = std_fn
    else:
        new_fn = f'{lib.stl_dir}/{part_name}.stl'
    if not os.path.exists(new_fn):
        thing = things.STL(fn)
        pts = thing.mesh.vectors.reshape((-1, 3))
        maxs = np.max(pts, axis=0)
        mins = np.min(pts, axis=0)
        dims = maxs - mins
        mid = (maxs + mins) / 2.
        if copy_only:
            pass
        else:
            thing.mesh.vectors = (thing.mesh.vectors - mid) / dims + [0, 0, .5]
        thing.mesh.save(new_fn)
    return os.path.split(new_fn)[1]
#assimilate_stl(lib, 'junk', 'rattleCAD_road_20150823.stl');here
    
db = sqlite3.connect(db_fn)

piecewise_table = Table("Piecewise",
                        Column("PartName", String()),
                        Column("Length", Integer()),
                        Column("Price", Float()))
piecewise_table.create(db)
try:
    piecewise_table.create_index(db, ("PartName", "Length"), unique=True)
except sqlite3.OperationalError:
    pass
part_table = Table('Part',
                   Column('Name',String(), UNIQUE=True),
                   Column('Wireframe', String()),
                   Column('STL_filename', String()),
                   Column('Price', Float()),
                   Column('URL', String()),
                   Column('Color', String()),
                   Column('Length', Integer()),
                   Column('Dim1', Integer()),
                   Column('Dim2', Integer()),
                   Column('Interface_01', String()),
                   Column('Interface_02', String()),
                   Column('Interface_03', String()),
                   Column('Interface_04', String()),
                   Column('Interface_05', String()),
                   Column('Interface_06', String())
)
part_table.create(db)
@util.cacheable
def lookup_interface(name):
    if name not in interface_table:
        raise ValueError(f"Interface named {name} not found")
    record = interface_table[name]
    hotspot = np.array(record[:3])
    direction = np.array(record[3:])
    return Interface(name, hotspot, direction)

def load_piecewise(csv_fn):
    csv_file = open(csv_fn)
    data = list(csv.reader(csv_file))
    csv_file.close()
    header = data[0]
    data = data[1:]
    data = [l for l in data if len(l) == 3]
    piecewise_table.insert(db, data)
load_piecewise('packages/piecewise.csv')

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
    
    part_table.insert(db, data)


#print(part_table.select(db))

def get(db, name):
    record = part_table.select(db, where=f'Name="{name}"') ## name is unique
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


db_connections = {}
def connect(db_fn):
    if db_fn not in db_connections:
        db = sqlite3.connect(db_fn)
        db_connections[db_fn] = db
    return db_connections[db_fn]
    

class ProxyDB:
    def __init__(self, fn):
        connect(fn)
        self.fn = fn
    def executemany(self, *args, **kw):
        return connect(self.fn).executemany(*args, **kw)
    
    def execute(self, sql):
        return connect(self.fn).execute(sql)

    def commit(self, *args, **kw):
        return connect(self.fn).commit(*args, **kw)
    
    
class Library:
    def __init__(self, library_name):
        self.name = library_name

        self.dir = os.path.join(part_libraries_dir, self.name)
        self.db_filename = os.path.join(self.dir, 'Parts.db')
        self.wireframe_dir = os.path.join(self.dir, 'Wireframes')
        self.thumbnail_dir = os.path.join(self.dir, 'Thumbnails')
        self.wireframes = {}
        self.stl_dir = os.path.join(self.dir, 'STL')
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
            os.mkdir(self.wireframe_dir)
            os.mkdir(self.thumbnail_dir)
            os.mkdir(self.stl_dir)
        if not os.path.exists(self.db_filename):
            self.db = ProxyDB(self.db_filename)
            self.initialize_db()
            copied_part_name = '2020 Corner Two Way'
            example = Main.get_part(copied_part_name)
            example.saveas(self, 'Example Part')
            shutil.copyfile(os.path.join(Main.wireframe_dir, 'Cube.npy'),
                            os.path.join(self.wireframe_dir, 'Cube.npy'))

        else:
            self.db = ProxyDB(self.db_filename)
        
    def delete_part(self, name):
        part_table.delete(self.db, where=f'Name="{name}"')
        
    def initialize_db(self):
        piecewise_table.create(self.db)
        part_table.create(self.db)
        piecewise_table.create_index(self.db, ("PartName", "Length"), unique=True)

    def get_names(self, where=''):
        return [r.Name for r in self.part_list()]
    
    def part_list(self, where=None):
        return part_table.select(self.db, where=where)

    def get_part(self, part_name):
        records = part_table.select(self.db, where=f'Name="{part_name}"')
        if len(records) == 1:
            out = Part(self, records[0])
        else:
            raise ValueError(f"More than one part named {part_name}.")
        return out
    
    def get_wireframe_names(self):
        out = []
        for fn in glob.glob(os.path.join(self.wireframe_dir, '*.npy')):
            name = os.path.split(fn)[1][:-4]
            out.append(name)
        out.sort()
        return out

    def get_wireframe(self, name):
        if name not in self.wireframes:
            self.wireframes[name] = np.load(os.path.join(self.wireframe_dir, name + '.npy'))
        return self.wireframes[name]
    
    def insert(self, values):
        part_table.insert(self.db, values)

    def make_thumbnail(self, part):
        #print('make_thumbnail()::')
        #print('    ', part.name)
        #print('    ', part.toscad())
        f = open(alex_scad, 'w')
        f.write(part.toscad())
        f.close()
        name = ''.join(part.name.split())
        png = f'{part.lib.thumbnail_dir}/{name}.png'
        #print('    ', png)
        os.system(f"{openscad_path} {alex_scad} --imgsize=512,512 -o {png}")

    def make_thumbnails(self):
        import os
        part_records = part_table.select(self.db)
        #print('make_thumbnails()::')
        for part_record in part_records:
            #print('    ', part_record.Name)
            part = Part(part_record.Name)
            make_thumbnail(part)
    #make_thumbnails();here
        
Main = Library('Main')

class Part(things.Thing):
    def price_function(self, x):
        return interp1d(self.lengths, self.prices, float(x))
        
    def __init__(self, lib, name_or_record, length=1):
        self.lib = lib
        if type(name_or_record) == type(''):
            name = name_or_record
            records = part_table.select(lib.db, where=f'Name="{name}"')
            assert len(records) == 1
            record = records[0]
            assert record
        else:
            record = name_or_record
            name = record.Name
        if record:
            things.Thing.__init__(self)
            self.name = name
            self.price = record.Price
            if self.price == '{piecewise}':
                result = piecewise_table.select(lib.db, where=f"PartName='{name}'")
                if len(result) == 0:
                    self.lengths = np.array([300, 5000])
                    self.prices = np.array([0, 0])
                else:
                    self.lengths = np.array([(r.Length) for r in result])
                    self.prices = np.array([(r.Price) for r in result])
                
                self.min_len = np.min(self.lengths)
                self.max_len = np.max(self.lengths)
            else:
                self.lengths = []
                self.prices = []
                #self.price_function = lambda x: interp1d(self.lengths, self.prices, x)
            self.dim1 = float(record.Dim1)
            self.dim2 = float(record.Dim2)
            if record.Length == 'NA':
                self.length = float(length)
            else:
                self.length = float(record.Length)
            try:
                wf = self.lib.get_wireframe(record.Wireframe)
            except KeyError:
                wf = self.lib.get_wireframe.get('Cube')
            #print('wf, self.dim1, self.dim2, self.length', wf, self.dim1, self.dim2, self.length)
            self.wireframe = wf * [self.dim1, self.dim2, self.length]
            self.stl_fn = os.path.join(lib.stl_dir, record.STL_filename)
            self.color = record.Color
            self.url = record.URL
            self.record = record
            
            self.interfaces = []
            for i in range(1, 7):
                k = f'Interface_{i:02d}'
                name = self.record[k]
                if name != 'NA':
                    interface = lookup_interface(name)
                    self.interfaces.append(interface)
    def saveas(self, tolib, name):
        wireframe = self.record.Wireframe
        values = self.get_db_values()
        values[0] = name
        stl_fn = values[2]
        shutil.copyfile(os.path.join(self.lib.stl_dir, stl_fn),
                        os.path.join(tolib.stl_dir, stl_fn))
        shutil.copyfile(os.path.join(self.lib.wireframe_dir, wireframe + '.npy'),
                        os.path.join(tolib.wireframe_dir, wireframe + '.npy'))
        shutil.copyfile(os.path.join(self.lib.thumbnail_dir, 'unknown.png'),
                        os.path.join(tolib.thumbnail_dir, 'unknown.png'))
        from_thumbnail = f"{''.join(self.name.split())}.png"
        to_thumbnail = f"{''.join(name.split())}.png"
        shutil.copyfile(os.path.join(self.lib.thumbnail_dir, from_thumbnail),
                        os.path.join(tolib.thumbnail_dir, to_thumbnail))

        tolib.insert([values])
        if self.price == '{piecewise}':
            result = piecewise_table.select(self.lib.db, where=f"PartName='{self.name}'")
            if len(result) == 0:
                raise ValueError('Expected example part to be complete!')
            values = [(r.Name, r.Length, r.Price) for r in records]
            piecewise_table.insert(tolib.db, values)
        
    def get_db_values(self):
        values = [self.name,      # 0
                  self.record.Wireframe, # 1
                  os.path.split(self.stl_fn)[-1],    # 2 STL 
                  self.price,     # 3 
                  self.url,       # 4 
                  self.color,     # 5 
                  self.length,    # 6 
                  self.dim1,      # 7 
                  self.dim2] + [face.name for face in self.interfaces] + ['NA' for i in range(6 - len(self.interfaces))]
        return values
    
    def __rescale_wireframe(self):
        self.wireframe = self.lib.get_wireframe(self.record.Wireframe) * [float(self.dim1),
                                                                          float(self.dim2),
                                                                          float(self.length)]
        
    def set_length(self, length):
        if self.record.Length == 'NA':
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

        #T = np.zeros((4, 4))
        #T[:3,:3] = self.orient @ np.diag([self.dim1, self.dim2, self.length])
        #T[:3,3] = self.pos
        #T[3,:3] = np.zeros(3)
        #T[3, 3] = 1
        #v = self.get_verts()
        #n = len(v)
        #wf = np.hstack([wireframes.get('Cube'), np.ones((n, 1))])
        ##print(T, np.linalg.norm(v - (T @ wf.T)[:3].T))
        #def format_T(T):
        #    lines =  [','.join(map(str, l)) for l in T]
        #    lines = [f'  [{l}]' for l in lines]
        #    linefeed = '\n'
        #    linesep = ',\n  '
        #    return f"[{linefeed}  {linesep.join(lines)}{linefeed}]"
        #out.append('')
        #out.append(f'color("{self.color}")')
        #out.append((f'  multmatrix(m={format_T(T)})import("{self.stl_fn}");'))
        return '\n'.join(out)

    def dup(self):
        out = Part(self.lib, self.name, self.length)
        out.translate(self.pos)
        out.orient = self.orient.copy()
        return out
    def cost(self):
        if self.price == '{piecewise}':
            out = self.price_function(self.length)
        else:
            out = self.price
        return out
    def tobom(self):
        return [f'{self.name},{self.dim1},{self.dim2},{self.length},${self.cost():.2f},{self.url}']

imgs = [None]
def url_shortener(url, max_len=40):
    url = url.strip()
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    if len(url)> max_len:
        url = url[:max_len - 3] + '...'
    return url

def PartDialog(parent, select_cb, lib=None):
    if lib is None:
        lib = Main
    PartDialog.lib = lib
    
    def get_parts():
        parts = PartDialog.lib.part_list()
        if len(parts) > 0:
            columns = list(parts[0].keys())[:9]
            data = [[getattr(line, name) for name in columns] for line in parts]
            names = [l[0] for l in data]
            idx = np.argsort(names)
            parts = [parts[i] for i in idx]
            names = [names[i] for i in idx]
            data = [data[i] for i in idx]
            data = dict(zip(names, data))
        else:
            names = []
            columns = []
            data = {}
        return parts, names, columns, data
    parts, names, columns, data = get_parts()
    
    
    n_col = len(columns)
    tl = tk.Toplevel(parent)

    url_col = 4

    def browseto(*args):
        part = item_clicked.part
        if part:
            url = part.record.URL
            if url.startswith('"') and url.endswith('"'):
                url = url[1:-1]
            webbrowser.open_new(url)
    
    def item_clicked(name):
        try:
            part = Part(PartDialog.lib, name)
        except ValueError:
            raise
            return
        png = ''.join(name.split())
        png = os.path.join(PartDialog.lib.thumbnail_dir, f'{png}.png')
        if not os.path.exists(png):
            png = os.path.join(PartDialog.lib.thumbnail_dir, 'unknown.png')
        img = ImageTk.PhotoImage(Image.open(png))

        display.configure(image=img)
        display.image = img
        #url.configure(text=url_shortener(data[idx][url_col], max_len=50))
        url.configure(text=url_shortener(data[name][url_col], max_len=50))
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
    def edit(*args):
        name = item_clicked.part.name
        new_part_dialog(parent, lib=PartDialog.lib, name=name, onclose=relist, copy=False)
    def copy(*args):
        name = item_clicked.part.name
        new_part_dialog(parent, lib=PartDialog.lib, name=name, onclose=relist, copy=True)
    def on_new_part(*args):
        new_part_dialog(parent, lib=PartDialog.lib, name=None, onclose=relist)

    def item_selected(idx, name):
        item_clicked(name)
        select()

    def relist(lib, name=None):
        PartDialog.lib = lib
        tl.winfo_toplevel().title(f"Library: {lib.name}")
        lb.delete(0, tk.END);
        new_parts, new_names, new_columns, new_data = get_parts()
        for i, item in enumerate(new_names):
            lb.insert(i, item);
        for k in list(data.keys()):
            if k not in new_data:
                del data[k]
        for k in list(new_data.keys()):
            if k not in data:
                data[k] = new_data[k]
        if name and name in data:
            item_clicked(name)
        else:
            if len(new_names) > 0:
                item_clicked(new_names[0])

    name_var = tk.StringVar()
    menubar = tk.Menu(tl)
    libmenu = tk.Menu(menubar, tearoff=0)
    libmenu.add_command(label="Main", command=lambda *args: relist(Main))
    for full_name in glob.glob(f'{part_libraries_dir}/*'):
        if os.path.isdir(full_name):
            if os.path.isfile(os.path.join(f'{full_name}/Parts.db')):
                name = os.path.split(full_name)[1]
                if name != 'Main':
                    _lib = Library(name)
                    libmenu.add_command(label=name, command=curry(relist, (_lib,)))
    def create_new_library():
        new_library_name = simpledialog.askstring("Input", "Library name:",
                                                  parent=tl)
        if new_library_name:
            lib = Library(new_library_name)
            PartDialog.lib = lib
            relist(lib)

    libmenu.add_separator()
    libmenu.add_command(label="New", command=lambda *args: create_new_library())
    menubar.add_cascade(label="Library", menu=libmenu)
    tl.config(menu=menubar)
    tl.winfo_toplevel().title(f"Library: Main")


    lb = listbox(tl, names, item_clicked, item_selected, n_row=50)
    lb.grid(row=0, column=0, rowspan=10)

    img = ImageTk.PhotoImage(Image.open(os.path.join(PartDialog.lib.thumbnail_dir, f'unknown.png')))
    imgs[0] = img
    display = tk.Label(tl, image=img)
    display.grid(row=0, column=2, sticky='N', columnspan=10)

    url = tk.Label(tl)
    url.configure(fg='blue')
    url.grid(row=0, column=2, sticky='NW', columnspan=4)
    url.bind('<Button-1>', browseto)

    cancel_button = tk.Button(tl, text="Cancel", command=cancel)
    cancel_button.grid(row=2, column=3, sticky='E')
    select_button = tk.Button(tl, text="Select", command=select)
    select_button.grid(row=2, column=4, sticky='EW')
    edit_button = tk.Button(tl, text="Edit", command=edit)
    edit_button.grid(row=2, column=5, sticky='EW')
    copy_button = tk.Button(tl, text="Copy", command=copy)
    copy_button.grid(row=2, column=6, sticky='EW')
    new_button = tk.Button(tl, text="New", command=on_new_part)
    new_button.grid(row=2, column=7, sticky='W')
    
    item_clicked(names[0])
    return tl

    
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
    PartDialog(db, r, select_cb)
    r.mainloop()

def validate_lib(*args):
    return True

def validate_name(lib, label, var, entry, commit_button):
    name = var.get().strip()
    matches = lib.part_list(where=f'name = "{name}"')
    if name == '':
        entry.config(bg="red")
        out = False
        commit_button.config(state="disabled")
    elif  len(matches) == 0:
        entry.config(bg=bgcolor)
        out = True
    elif len(matches) == 1:
        ### populate fields
        record = matches[0]
        part = Part(lib, record)
        with open(alex_scad, 'w') as f:
            f.write(part.toscad())
        out = True
    return out

def validate_wireframe(lib, label, var, option, commit_button, view):
    name = var.get()
    if name in lib.get_wireframe_names():
        wf = lib.get_wireframe(name)
        view.can.delete('all')
        view.draw_axes()
        view.create_path('wireframe', wf, "black", 1)
        out = True
        option.config(bg=bgcolor)
    else:
        out = False
        option.config(bg="red")
        commit_button.config(state="disabled")
    return out
    
def validate_stl(lib, label, var, entry, commit_button):
    stl = var.get().strip()
    if not os.path.exists(stl): ### see if it is in the library already
        stl = os.path.join(lib.stl_dir, stl)
    if os.path.exists(stl) and os.path.isfile(stl):
        thing = things.STL(stl)
        #with open(alex_scad, 'w') as f:
        #    f.write(thing.toscad())
        entry.config(bg=bgcolor)
        out = True
    else:
        entry.config(bg="red")
        out = False
        commit_button.config(state="disabled")
    return out
def validate_price(label, var, entry, commit_button, len_vars, cost_vars):
    out = False
    #print('validate', label, var.get())
    s = var.get()
    if len(s) == 0:
        out = True
        var.set('0.00')
    else:
        if s == '{piecewise}':
            out = len(cm.get_table(len_vars, cost_vars)) > 0
            #print('table:', len(cm.get_table(len_vars, cost_vars)) > 0, out)
            if out:
                entry.config(bg=bgcolor)
            else:
                entry.config(bg="red")
        else:
            try:
                v = float(s)
                entry.config(bg=bgcolor)
                out = True
            except ValueError:
                entry.config(bg=bgcolor)
                var.set('0.00')
                out = True
    #print('validate_price::out', out)
    return out

def url_open(label, var, entry):
    url = var.get()
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    webbrowser.open_new(url)

def validate_url(label, var, entry, commit_button):
    #print('validate', label)
    url = var.get().strip()
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    if url.startswith("http") or url.startswith('www'):
        entry.config(bg=bgcolor)
    else:
        entry.config(bg="yellow")
    return True
def validate_color(label, var, entry, commit_button):
    #print('validate', label)
    color = var.get()
    return True
def validate_length(label, var, entry, commit_button):
    #print('validate', label)
    s = var.get()
    try:
        len = float(s)
    except ValueError:
        var.set("NA")
    return True
    
def validate_dim(label, var, entry, commit_button):
    #print('validate', label)
    s = var.get()
    try:
        len = float(s)
        entry.config(bg=bgcolor)
    except ValueError:
        commit_button.config(state="disabled")
        entry.config(bg="red")
    return True
def validate_interface(label, var, entry, commit_button):
    #print('validate', label)
    return True

def ask_stl_filename(lib, label, entry):
    filename = filedialog.askopenfilename(initialdir = lib.stl_dir,
                                          title = f"Select {label}",
                                          filetypes = (("Mesh", "*.stl"),
                                                       ("all files","*.*")))
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)
        if os.path.exists(filename):
            entry.config(bg=bgcolor)
        else:
            entry.confi(bg="red")
            
def ask_wireframe(lib, label, option, var):
    filename = filedialog.askopenfilename(title = f"Select {label}",
                                          filetypes = (("Mesh", "*.stl"),
                                                       ("all files","*.*")))
    if filename:
        if os.path.exists(filename):
            name = os.path.split(filename)[1].title()
            if name.lower().endswith('.stl'):
                name = name[:-4]
            wf = wireframes.from_stl(filename)
            wireframes.add_wf(lib, name, wf)
            option.config(bg=bgcolor)
            option['menu'].add_command(label=name)
            var.set(name)
        else:
            option.confi(bg="red")
            
def ask_color(label, entry):
    a, color = colorchooser.askcolor(title =f"Choose {label}")
    if color is not None:
        entry.delete(0, tk.END)
        entry.insert(0, color)
        entry.config(bg=color)

def get_library_names():
    full_names = glob.glob(f'{part_libraries_dir}/*')
    names = ['Main'] ## put main first!
    for full_name in full_names:
        if os.path.isdir(full_name):
            name = os.path.split(full_name)[-1]
            if name != 'Main':
                if os.path.exists(os.path.join(full_name, 'Parts.db')):
                    ### looks like a lib dir
                    names.append(name)
    return names
    
def new_part_dialog(parent, lib=Main, name=None, onclose=None, copy=False):
    tl = tk.Toplevel(parent)
    
    dialog_parent = tk.Frame(tl)
    cost_frame, can, len_vars, cost_vars, plot_cb = cm.piecewise_linear_cost_model(dialog_parent)
    part_frame = tk.Frame(dialog_parent)

    #### 3d render of wireframe
    from packages import isometric_view as iv
    scale = 100
    theta = 240 * DEG
    phi =  35 * DEG

    offset = [200, 300]
    can_frame = tk.Frame(part_frame)
    wire_view = iv.get_view(can_frame, theta, phi, offset, scale=scale)
    can_frame.grid(row=40, column=1, columnspan=10)

    ################################################################################


    piecewise_dialog_visible = [False]
    def enable_piecewise_dialog():
        price_entry.delete(0, tk.END)
        price_entry.insert(0, '{piecewise}')
        cost_frame.grid(row=1, column=4, padx=20)
        piecewise_dialog_visible[0] = True
    def disable_piecewise_dialog():
        price_entry.delete(0, tk.END)
        if price_var.get() == '{piecewise}':
            price_entry.delete(0, tk.END)
        cost_frame.grid_remove()
        
    def toggle_piecewise_dialog():
        piecewise_dialog_visible[0] = not piecewise_dialog_visible[0]
        if piecewise_dialog_visible[0]:
            enable_piecewise_dialog()
        else:
            disable_piecewise_dialog()

    ttk.Separator(dialog_parent, orient=tk.VERTICAL).grid(column=2, row=0, rowspan=100, sticky='ns', padx=20)

    validators = [validate_lib,
                  validate_name,
                  validate_wireframe,
                  validate_stl,
                  validate_price,
                  validate_url,
                  validate_color,
                  validate_dim,
                  validate_dim,
                  validate_length,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
    ]
    def validate_all():
        out = True
        for i, v in enumerate(validates):
            if not v():
                print(f"Failed {i}th validator")
                out = False
        return out
    
    validates = [] ### store no argment functions
    variables = [] ### store variables for commit

    def delete_part(*args):
        name = name_var.get()
        if name:
            result = messagebox.askquestion("Overwrite", f"Delete {name}", icon='warning')
            if result == 'yes':
                part_table.delete(lib.db, where=f'Name="{name}"')
                piecewise_table.delete(lib.db, where=f'PartName="{name}"')
                #print("Deleted")
        
    def commit_new_part():
        values = [name_var.get(),   # 0
                  wire_var.get(),   # 1
                  stl_var.get(),    # 2 STL 
                  price_var.get(),  # 3 
                  url_var.get(),    # 4 
                  color_var.get(),  # 5
                  length_var.get(), # 6
                  dim1_var.get(),   # 7 
                  dim2_var.get(),   # 8
        ] + [var.get() for var in interface_vars]
        lib_name = lib_var.get()
        if values[2] == os.path.abspath(values[2]):
            stl_fn = values[2]
            values[2] = os.path.split(values[2])[1]
            copy_only = False
        else:
            stl_fn = os.path.join(os.path.join(lib.stl_dir, values[2]))
            copy_only = True
        to_lib = Library(lib_name)
        prev_records = part_table.select(to_lib.db, where=f'Name="{values[0]}"')
        if prev_records:
            result = messagebox.askquestion("Overwrite", f"Overwrite {values[0]}", icon='warning')
            if result == 'yes':
                part_table.delete(to_lib.db, where=f'Name="{values[0]}"')
            else:      
                return
        ### import stl file into library
        print('commit_new_part()::', to_lib.name, values[0], values[2])
        values[2] = assimilate_stl(to_lib, values[0], stl_fn, copy_only=copy_only)

        to_lib.insert([values])

        ### import wireframe to library
        npy = os.path.join(to_lib.wireframe_dir, values[1] + '.npy')
        if not os.path.exists(npy):
            shutil.copyfile(os.path.join(lib.wireframe_dir, values[1] + '.npy'),
                            npy)
            
        if price_var.get() == '{piecewise}':
            price_list = cm.get_table(len_vars, cost_vars)
            name = name_var.get()
            prices = [(name, l, p) for l, p in price_list]

            piecewise_table.delete(to_lib.db, where=f'PartName="{name}"')
            piecewise_table.insert(to_lib.db, prices)
            
        part = Part(to_lib, name_var.get())
        to_lib.make_thumbnail(part)
        close_new_part_dialog()
        
    commit_button = tk.Button(part_frame, text="Commit", command=commit_new_part)
    commit_button.grid(row=31, column=2, sticky='e')
    commit_button.config(state='disabled')
    delete_button = tk.Button(part_frame, text="Delete", command=delete_part)
    delete_button.grid(row=30, column=3, sticky='e')
    
    def close_new_part_dialog():
        if(onclose):
            lib_name = lib_var.get()
            to_lib = Library(lib_name)
            onclose(to_lib, name_var.get())
        tl.destroy()
        
    close_button = tk.Button(part_frame, text="Close", command=close_new_part_dialog)
    close_button.grid(row=31, column=3, sticky='e')


    row = 0
    lib_names = [n for n in get_library_names() if n != 'Main']
    if constants.edit_main:
        lib_names.insert(0, 'Main')
    lib_var = tk.StringVar()
    if lib == Main:
        lib_var.set("User")
    else:
        lib_var.set(lib.name)
    #variables.append(lib_var) ##???
    tk.Label(part_frame, text="Save to library:").grid(row=row+1, column=1, sticky='e')
    lib_opt = tk.OptionMenu(part_frame, lib_var, *lib_names)
    lib_opt.grid(row=row+1, column=2, sticky='w')
    validate = curry(validators[row], (lib, 'Library', lib_var, lib_opt, commit_button))
    validates.append(validate)
    row += 1
    
    name_var = tk.StringVar()
    variables.append(name_var)
    tk.Label(part_frame, text="Name").grid(row=row+1, column=1, sticky='e')
    name_entry = tk.Entry(part_frame, textvariable=name_var)
    name_entry.grid(row=row+1, column=2)
    populate_button = tk.Button(part_frame, text="Lookup")
    populate_button.grid(row=row+1, column=3, sticky='w')
    ### validate created below after other entries are created.
    row += 1

    wireframe_names = lib.get_wireframe_names()
    wire_var = tk.StringVar()
    wire_var.set("Cube")
    variables.append(wire_var)
    tk.Label(part_frame, text="Wireframe").grid(row=row+1, column=1, sticky='e')
    wire_opt = tk.OptionMenu(part_frame, wire_var, *wireframe_names)
    wire_opt.grid(row=row+1, column=2, sticky='w')
    
    validate = curry(validators[row], (lib, 'Wireframe', wire_var, wire_opt, commit_button, wire_view))
    validates.append(validate)
    wire_opt.bind('<FocusOut>', validate)
    browse_button = tk.Button(part_frame, text="New", command=curry(ask_wireframe, (lib, 'Wireframe', wire_opt, wire_var)))
    browse_button.grid(row=row+1, column=3, sticky='w')
    wire_var.trace('w', validate)
    validate()
    row += 1

    stl_var = tk.StringVar()
    variables.append(stl_var)
    tk.Label(part_frame, text="STL").grid(row=row+1, column=1, sticky='e')
    stl_entry = tk.Entry(part_frame, textvariable=stl_var)
    stl_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], (lib, 'STL', stl_var, stl_entry, commit_button))
    validates.append(validate)
    stl_entry.bind('<FocusOut>', validate)
    browse_button = tk.Button(part_frame, text="Browse", command=curry(ask_stl_filename, (lib, 'STL', stl_entry)))
    browse_button.grid(row=row+1, column=3, sticky='w')
    row += 1

    price_var = tk.StringVar()
    variables.append(price_var)
    tk.Label(part_frame, text="Price").grid(row=row+1, column=1, sticky='e')
    price_entry = tk.Entry(part_frame, textvariable=price_var)
    price_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Price', price_var, price_entry, commit_button, len_vars, cost_vars))
    validates.append(validate)
    price_entry.bind('<FocusOut>', validate)
    tk.Button(part_frame, text="Piecewise Linear", command=toggle_piecewise_dialog).grid(row=row+1, column=3)

    row += 1

    url_var = tk.StringVar()
    variables.append(url_var)
    tk.Label(part_frame, text="URL").grid(row=row+1, column=1, sticky='e')
    url_entry = tk.Entry(part_frame, textvariable=url_var)
    url_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('URL', url_var, url_entry, commit_button))
    validates.append(validate)
    url_entry.bind('<FocusOut>', validate)
    tk.Button(part_frame, text="Open", command=curry(url_open, ('URL', url_var, url_entry))).grid(
        row=row+1, column=3,
        sticky='w')
    row += 1

    color_var = tk.StringVar()
    variables.append(color_var)
    tk.Label(part_frame, text="Color").grid(row=row+1, column=1, sticky='e')
    color_entry = tk.Entry(part_frame, textvariable=color_var)
    color_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Color', color_var, color_entry, commit_button))
    validates.append(validate)
    color_entry.bind('<FocusOut>', validate)
    color_button = tk.Button(part_frame, text="Choose", command=curry(ask_color, ('Color', color_entry)))
    color_button.grid(row=row+1, column=3, sticky='w')
    row += 1

    dim1_var = tk.StringVar()
    variables.append(dim1_var)
    tk.Label(part_frame, text="Dim X").grid(row=row+1, column=1, sticky='e')
    dim1_entry = tk.Entry(part_frame, textvariable=dim1_var)
    dim1_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Dim X', dim1_var, dim1_entry, commit_button))
    validates.append(validate)
    dim1_entry.bind('<FocusOut>', validate)
    row += 1
    
    dim2_var = tk.StringVar()
    variables.append(dim2_var)
    tk.Label(part_frame, text="Dim Y").grid(row=row+1, column=1, sticky='e')
    dim2_entry = tk.Entry(part_frame, textvariable=dim2_var)
    dim2_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Dim Y', dim2_var, dim2_entry, commit_button))
    validates.append(validate)
    dim2_entry.bind('<FocusOut>', validate)
    row += 1

    length_var = tk.StringVar()
    variables.append(length_var)
    tk.Label(part_frame, text="Dim Z").grid(row=row+1, column=1, sticky='e')
    length_entry = tk.Entry(part_frame, textvariable=length_var)
    length_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Dim Z', length_var, length_entry, commit_button))
    validates.append(validate)
    length_entry.bind('<FocusOut>', validate)
    length_var.set("NA")
    row += 1
    
    interface_names = list(interface_table.keys())
    interface_vars = [tk.StringVar() for i in range(6)]
    variables.extend(interface_vars)
    
    for i in range(6):
        interface_var = tk.StringVar()
        label = f"Interface_{i+1:02d}"
        #tk.Label(part_frame, text=label).grid(row=row+1, column=1, sticky='e')
        
        interface_vars[i].set('NA')
        interface_opt_menu = tk.OptionMenu(part_frame, interface_vars[i], *interface_names)        
        #interface_opt_menu.grid(row=row+1, column=2, stick='w')
        #validate = curry(validators[row], (label, interface_var, interface_opt_menu, commit_button))
        #validates.append(validate)
        #interface_opt_menu.bind('<FocusOut>', validate)
        row += 1

    def validate_new_part():
        #print('validate new part!')
        if validate_all():
            commit_button.config(state='normal')
        else:
            commit_button.config(state='disabled')

    validate_button = tk.Button(part_frame, text="Validate", command=validate_new_part)
    validate_button.grid(row=30, column=2, sticky='e')
    row += 1

    def populate_cb(event):
        name = name_var.get()
        record = part_table.select(lib.db, where=f'Name="{name}"')
        if len(record) > 0:
            record = record[0]
        else:
            #print("No record found for", name)
            return
        wire_var.set(record.Wireframe)
        stl_var.set(record.STL_filename)
        price_var.set(record.Price)
        if record.Price == '{piecewise}': ### from DB, should not have spaces
           prices = piecewise_table.select(lib.db, where=f'PartName = "{record.Name}"')
           for i, price_record in enumerate(prices[:len(len_vars)]):
               len_vars[i].set(price_record.Length)
               cost_vars[i].set(price_record.Price)
           for i in range(len(prices), len(len_vars)):
               len_vars[i].set("")
               cost_vars[i].set("")
           plot_cb()
           enable_piecewise_dialog()
        else:
            price_var.set(record.Price)
            # disable_piecewise_dialog()
        url_var.set(record.URL)
        color_var.set(record.Color)
        length_var.set(record.Length)
        dim1_var.set(record.Dim1)
        dim2_var.set(record.Dim2)
        for i in range(6):
            interface_vars[i].set(record[f"Interface_{i+1:02d}"])
    validate = curry(validate_name, (lib, 'Name', name_var, name_entry, commit_button))
    if name is not None:
        name_var.set(name)
        populate_cb(None)
        if copy:
            copy_matcher = re.compile(r'(.*) x\d\d\d')
            match = copy_matcher.search(name)
            if match:
                name = match.group(1)
            similar_names = [l.Name for l in part_table.select(lib.db, where=f'name like "{name} x___"')]
            copy_num = len([n for n in similar_names if copy_matcher.search(n)]) + 1
            copy_name = f'{name} x{copy_num:03d}'
            name_var.set(copy_name)
            name_entry.focus_set()
            name_entry.select_range(len(copy_name)-5, tk.END)
            name_entry.icursor(tk.END)
    validates.insert(1, validate)
    name_entry.bind('<FocusOut>', validate)
    populate_button.bind('<Button-1>', populate_cb)
    part_frame.grid(row=1, column=1)
    dialog_parent.grid()
    #print("Table:")
    #print(cm.get_table(len_vars, cost_vars))
    return dialog_parent, can, len_vars, cost_vars

def test_new_part_dialog():
    from packages import piecewise_linear_cost_model as cm

    root = tk.Tk()
    new_part_dialog(root)
    root.mainloop()

    
if __name__ == '__main__':
    load_parts(csv_fn)
    #test_part_select()
    test_new_part_dialog()
