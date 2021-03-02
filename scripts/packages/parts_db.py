import re
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import colorchooser
from tkinter import messagebox
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
from packages.util import curry
from packages import things
from packages import wireframes
from packages import database
from packages.database import String, Integer, Float, Table, Column
from packages.constants import DEG, alex_scad, stl_dir, bgcolor
from packages.interpolate import interp1d
from packages.mylistbox import listbox
from packages import piecewise_linear_cost_model as cm

mydir = os.path.split(os.path.abspath(__file__))[0]
db_fn = os.path.join(mydir, 'Alex_parts.db')
db = sqlite3.connect(db_fn)


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

def assimilate_stl(part_name, fn):
    base = os.path.split(fn)[1]
    std_fn = f'{stl_dir}/{base}'
    if os.path.exists(std_fn):
        new_fn = std_fn
    else:
        new_fn = f'{stl_dir}/{part_name}.stl'
    if not os.path.exists(new_fn):
        thing = things.STL(fn)
        pts = thing.mesh.vectors.reshape((-1, 3))
        maxs = np.max(pts, axis=0)
        mins = np.min(pts, axis=0)
        dims = maxs - mins
        mid = (maxs + mins) / 2.
        print(np.amax(thing.mesh.vectors, axis=0))
        thing.mesh.vectors = (thing.mesh.vectors - mid) / dims + [0, 0, .5]
        thing.mesh.save(new_fn)
    return os.path.split(new_fn)[1]
#assimilate_stl('junk', 'rattleCAD_road_20150823.stl');here
    
@util.cacheable
def lookup_interface(name):
    if name not in interface_table:
        raise ValueError(f"Interface named {name} not found")
    record = interface_table[name]
    hotspot = np.array(record[:3])
    direction = np.array(record[3:])
    return Interface(name, hotspot, direction)

piecewise_table = Table("Piecewise", db,
                        Column("PartName", String()),
                        Column("Length", Integer()),
                        Column("Price", Float()))
piecewise_table.create()
try:
    piecewise_table.create_index(("PartName", "Length"), unique=True)
except sqlite3.OperationalError:
    pass
def load_piecewise(csv_fn):
    csv_file = open(csv_fn)
    data = list(csv.reader(csv_file))
    csv_file.close()
    header = data[0]
    data = data[1:]
    data = [l for l in data if len(l) == 3]
    piecewise_table.insert(data)
load_piecewise('packages/piecewise.csv')


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
    def __init__(self, name_or_record, length=1):
        if type(name_or_record) == type(''):
            name = name_or_record
            record = get(name)
            assert record
        else:
            record = name_or_record
            name = record.Name
        if record:
            things.Thing.__init__(self)
            self.name = name
            self.price = record.Price
            if self.price == '{piecewise}':
                result = piecewise_table.select(where=f"PartName='{name}'")
                if len(result) == 0:
                    self.lengths = np.array([300, 5000])
                    self.prices = np.array([0, 0])
                else:
                    self.lengths = np.array([(r.Length) for r in result])
                    self.prices = np.array([(r.Price) for r in result])
                
                self.min_len = np.min(self.lengths)
                self.max_len = np.max(self.lengths)
                self.price_function = lambda x: interp1d(self.lengths, self.prices, x)
            
            self.dim1 = record.Dim1
            self.dim2 = record.Dim2
            if record.Length == 'NA':
                self.length = length
            else:
                self.length = record.Length
            try:
                wf = wireframes.get(record.Wireframe)
            except KeyError:
                wf = wireframes.get('Cube')
            self.wireframe = wf * [self.dim1, self.dim2, self.length]
            self.stl_fn = os.path.join(stl_dir, record.STL_filename)
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
        return '\n'.join(out)

    def dup(self):
        out = Part(self.name, self.length)
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
        return [f'{self.name},{self.dim1},{self.dim2},{self.length},{self.cost()}']

imgs = [None]
def url_shortener(url, max_len=40):
    url = url.strip()
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    if len(url)> max_len:
        url = url[:max_len - 3] + '...'
    return url

def PartDialog(parent, select_cb):
    def get_parts():
        parts = part_table.select()
        columns = list(parts[0].keys())[:9]
        data = [[getattr(line, name) for name in columns] for line in parts]
        names = [l[0] for l in data]
        idx = np.argsort(names)
        parts = [parts[i] for i in idx]
        names = [names[i] for i in idx]
        data = [data[i] for i in idx]
        data = dict(zip(names, data))
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
            part = Part(name)
        except ValueError:
            raise
            return
        png = ''.join(name.split())
        png = os.path.join(stl_dir, f'{png}.png')
        if not os.path.exists(png):
            png = os.path.join(stl_dir, 'unknown.png')
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
        new_part_dialog(parent, name=name, onclose=relist, copy=False)
    def copy(*args):
        name = item_clicked.part.name
        new_part_dialog(parent, name=name, onclose=relist, copy=True)

    def item_selected(idx, name):
        item_clicked(name)
        select()

    def relist(name):
        lb.delete(0, len(names));
        new_parts, new_names, new_columns, new_data = get_parts()        
        for i, item in enumerate(new_names):
            lb.insert(i, item);
        for k in list(data.keys()):
            if k not in new_data:
                del data[k]
        for k in list(new_data.keys()):
            if k not in data:
                data[k] = new_data[k]
        if name in data:
            item_clicked(name)
    name_var = tk.StringVar()
    lb = listbox(tl, names, item_clicked, item_selected, n_row=50)
    lb.grid(row=0, column=0, rowspan=10)

    img = ImageTk.PhotoImage(Image.open(os.path.join(stl_dir, f'2020CornerTwoWay.png')))
    imgs[0] = img
    display = tk.Label(tl, image=img)
    display.grid(row=1, column=2, sticky='N', columnspan=10)

    url = tk.Label(tl)
    url.configure(fg='blue')
    url.grid(row=1, column=2, sticky='NW', columnspan=4)
    url.bind('<Button-1>', browseto)

    cancel_button = tk.Button(tl, text="Cancel", command=cancel)
    cancel_button.grid(row=2, column=3, sticky='E')
    select_button = tk.Button(tl, text="Select", command=select)
    select_button.grid(row=2, column=4, sticky='EW')
    edit_button = tk.Button(tl, text="Edit", command=edit)
    edit_button.grid(row=2, column=5, sticky='EW')
    copy_button = tk.Button(tl, text="Copy", command=copy)
    copy_button.grid(row=2, column=6, sticky='W')
    
    item_clicked(names[0])
    return tl

def make_thumbnail(part):
    import os
    load_parts(csv_fn)
    print(part.name)
    print(part.toscad())
    f = open('../Alex_test.scad', 'w')
    f.write(part.toscad())
    f.close()
    name = ''.join(part.name.split())
    png = f'{stl_dir}/{name}.png'
    print(png)
    os.system(f"/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD ../Alex_test.scad --imgsize=512,512 -o {png}")
    
def make_thumbnails():
    import os
    load_parts(csv_fn)
    part_records = part_table.select()
    for part_record in part_records:
        print(part_record.Name)
        part = Part(part_record.Name)
        make_thumbnail(part)
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

def validate_name(label, var, entry, commit_button):
    name = var.get().strip()
    matches = part_table.select(where=f'name = "{name}"')
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
        part = Part(record)
        with open(alex_scad, 'w') as f:
            f.write(part.toscad())
        out = True
    return out

def validate_wireframe(label, var, option, commit_button, view):
    name = var.get()
    if name in wireframes.getlist():
        wf = wireframes.get(name)
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
    
def validate_stl(label, var, entry, commit_button):
    stl = var.get().strip()
    if not os.path.exists(stl):
        stl = os.path.join(stl_dir, stl)
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

def ask_stl_filename(label, entry):
    filename = filedialog.askopenfilename(initialdir = stl_dir,
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
            
def ask_wireframe(label, option, var):
    filename = filedialog.askopenfilename(title = f"Select {label}",
                                          filetypes = (("Mesh", "*.stl"),
                                                       ("all files","*.*")))
    if filename:
        if os.path.exists(filename):
            name = os.path.split(filename)[1].title()
            if name.lower().endswith('.stl'):
                name = name[:-4]
            wf = wireframes.from_stl(filename)
            wireframes.add_wf(name, wf)
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

def new_part_dialog(parent, name=None, onclose=None, copy=False):
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

    validators = [validate_name,
                  validate_wireframe,
                  validate_stl,
                  validate_price,
                  validate_url,
                  validate_color,
                  validate_length,
                  validate_dim,
                  validate_dim,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
                  validate_interface,
    ]
    def validate_all():
        out = True
        for v in validates:
            if not v():
                out = False
        return out
    
    validates = [] ### store no argment functions
    variables = [] ### store variables for commit

    def delete_part(*args):
        name = name_var.get()
        if name:
            result = messagebox.askquestion("Overwrite", f"Delete {name}", icon='warning')
            if result == 'yes':
                part_table.delete(where=f'Name="{name}"')
                piecewise_table.delete(where=f'PartName="{name}"')
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
                  dim2_var.get()] + [var.get() for var in interface_vars]
        prev_records = part_table.select(where=f'Name="{values[0]}"')
        if prev_records:
            result = messagebox.askquestion("Overwrite", f"Overwrite {values[0]}", icon='warning')
            if result == 'yes':
                part_table.delete(where=f'Name="{values[0]}"')
                #print("Deleted")
            else:
                #print("Skipping")            
                return
        ### import stl file into library
        values[2] = assimilate_stl(values[0], values[2])
        part_table.insert([values])
        if price_var.get() == '{piecewise}':
            price_list = cm.get_table(len_vars, cost_vars)
            name = name_var.get()
            prices = [(name, l, p) for l, p in price_list]
            piecewise_table.delete(where=f'PartName="{name}"')
            piecewise_table.insert(prices)
            
        part = Part(name_var.get())
        make_thumbnail(part)
        
    commit_button = tk.Button(part_frame, text="Commit", command=commit_new_part)
    commit_button.grid(row=31, column=2, sticky='e')
    commit_button.config(state='disabled')
    delete_button = tk.Button(part_frame, text="Delete", command=delete_part)
    delete_button.grid(row=30, column=3, sticky='e')
    
    def close_new_part_dialog():
        if(onclose):
            onclose(name_var.get())
        tl.destroy()
        
    close_button = tk.Button(part_frame, text="Close", command=close_new_part_dialog)
    close_button.grid(row=31, column=3, sticky='e')


    row = 0
    
    name_var = tk.StringVar()
    variables.append(name_var)
    tk.Label(part_frame, text="Name").grid(row=row+1, column=1, sticky='e')
    name_entry = tk.Entry(part_frame, textvariable=name_var)
    name_entry.grid(row=row+1, column=2)
    populate_button = tk.Button(part_frame, text="Lookup")
    populate_button.grid(row=row+1, column=3, sticky='w')
    ### validate created below after other entries are created.
    row += 1

    wireframe_names = list(wireframes.getlist())
    wire_var = tk.StringVar()
    wire_var.set("Cube")
    variables.append(wire_var)
    tk.Label(part_frame, text="Wireframe").grid(row=row+1, column=1, sticky='e')
    wire_opt = tk.OptionMenu(part_frame, wire_var, *wireframe_names)        
    wire_opt.grid(row=row+1, column=2, sticky='w')
    validate = curry(validators[row], ('Wireframe', wire_var, wire_opt, commit_button, wire_view))
    validates.append(validate)
    wire_opt.bind('<FocusOut>', validate)
    browse_button = tk.Button(part_frame, text="New", command=curry(ask_wireframe, ('Wireframe', wire_opt, wire_var)))
    browse_button.grid(row=row+1, column=3, sticky='w')
    wire_var.trace('w', validate)
    validate()
    row += 1

    stl_var = tk.StringVar()
    variables.append(stl_var)
    tk.Label(part_frame, text="STL").grid(row=row+1, column=1, sticky='e')
    stl_entry = tk.Entry(part_frame, textvariable=stl_var)
    stl_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('STL', stl_var, stl_entry, commit_button))
    validates.append(validate)
    stl_entry.bind('<FocusOut>', validate)
    browse_button = tk.Button(part_frame, text="Browse", command=curry(ask_stl_filename, ('STL', stl_entry)))
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

    length_var = tk.StringVar()
    variables.append(length_var)
    tk.Label(part_frame, text="Length").grid(row=row+1, column=1, sticky='e')
    length_entry = tk.Entry(part_frame, textvariable=length_var)
    length_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Length', length_var, length_entry, commit_button))
    validates.append(validate)
    length_entry.bind('<FocusOut>', validate)
    length_var.set("NA")
    row += 1
    
    dim1_var = tk.StringVar()
    variables.append(dim1_var)
    tk.Label(part_frame, text="Dim1").grid(row=row+1, column=1, sticky='e')
    dim1_entry = tk.Entry(part_frame, textvariable=dim1_var)
    dim1_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Dim1', dim1_var, dim1_entry, commit_button))
    validates.append(validate)
    dim1_entry.bind('<FocusOut>', validate)
    row += 1
    
    dim2_var = tk.StringVar()
    variables.append(dim2_var)
    tk.Label(part_frame, text="Dim2").grid(row=row+1, column=1, sticky='e')
    dim2_entry = tk.Entry(part_frame, textvariable=dim2_var)
    dim2_entry.grid(row=row+1, column=2)
    validate = curry(validators[row], ('Dim2', dim2_var, dim2_entry, commit_button))
    validates.append(validate)
    dim2_entry.bind('<FocusOut>', validate)
    row += 1

    interface_names = list(interface_table.keys())
    interface_vars = [tk.StringVar() for i in range(6)]
    variables.extend(interface_vars)
    
    for i in range(6):
        interface_var = tk.StringVar()
        label = f"Interface_{i+1:02d}"
        tk.Label(part_frame, text=label).grid(row=row+1, column=1, sticky='e')
        
        interface_vars[i].set('NA')
        interface_opt_menu = tk.OptionMenu(part_frame, interface_vars[i], *interface_names)        
        interface_opt_menu.grid(row=row+1, column=2, stick='w')
        validate = curry(validators[row], (label, interface_var, interface_opt_menu, commit_button))
        validates.append(validate)
        interface_opt_menu.bind('<FocusOut>', validate)
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
        record = part_table.select(where=f'Name="{name}"')
        if len(record) > 0:
            record = record[0]
        else:
            #print("No record found for", name)
            return
        wire_var.set(record.Wireframe)
        stl_var.set(record.STL_filename)
        price_var.set(record.Price)
        if record.Price == '{piecewise}': ### from DB, should not have spaces
           prices = piecewise_table.select(where=f'PartName = "{record.Name}"')
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
    validate = curry(validate_name, ('Name', name_var, name_entry, commit_button))
    if name is not None:
        name_var.set(name)
        populate_cb(None)
        if copy:
            copy_matcher = re.compile(r'(.*) x\d\d\d')
            match = copy_matcher.search(name)
            if match:
                name = match.group(1)
            similar_names = [l.Name for l in part_table.select(where=f'name like "{name} x___"')]
            copy_num = len([n for n in similar_names if copy_matcher.search(n)]) + 1
            copy_name = f'{name} x{copy_num:03d}'
            name_var.set(copy_name)
            name_entry.focus_set()
            name_entry.select_range(len(copy_name)-5, tk.END)
            name_entry.icursor(tk.END)
    validates.insert(0, validate)
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
