import glob
import os.path
import numpy as np
from numpy import cos, sin, pi
import sys
if '.' not in sys.path:
    sys.path.append('.')
from packages.constants import npy_dir
from packages.stl_to_wireframe import from_stl

import sys
if '.' not in sys.path:
    sys.path.append('.')
from packages import constants
from packages import things

def path(pts):
    return np.array(pts)

def Wireframe(paths):
    N = np.sum([len(p) for p in paths]) + len(paths) - 1
    out = np.empty((N, 3), int) * np.nan
    
    start = 0
    for p in paths:
        n = len(p)
        out[start:start + n] = p
        start += n + 1
    return out

def draw_wireframe(wf, rescale, view):
    ### use view.create_path in most cases
    wf = wf.copy()
    wf *= rescale
    view.create_path(wf, wf, 'black', 1)

bottom_square = path([
    [-.5, -.5, 0],
    [-.5,  .5, 0],
    [ .5,  .5, 0],
    [ .5, -.5, 0],
    [-.5, -.5, 0],
    ])
top_square = bottom_square + np.array([0, 0, 1])
square_columns = [path([bottom_square[i], top_square[i]]) for i in range(4)]

prism_back = path([
    [-.5, -.5, 0],
    [ .5, -.5, 1],
    [ .5, -.5, 0],
])
    
prism_front = prism_back + np.array([0, 1, 0])
prism_top = path([[.5, -.5, 1], [.5, .5, 1]])

cube_frame = path([
    [-.5, -.5, 0], # 1
    [-.5,  .5, 0], # 2
    [ .5,  .5, 0], # 3
    [ .5, -.5, 0], # 4
    [-.5, -.5, 0], # 1
    
    [-.5, -.5, 1], # 5

    [-.5,  .5, 1], # 6
    [-.5,  .5, 0], # 2
    [-.5,  .5, 1], # 6

    [ .5,  .5, 1], # 7
    [ .5,  .5, 0], # 3
    [ .5,  .5, 1], # 7

    [ .5, -.5, 1], # 8
    [ .5, -.5, 0], # 4
    [ .5, -.5, 1], # 8

    [-.5, -.5, 1], # 5
    ])
prism_frame = path([
    [ .5,  .5, 0], # 1
    [ .5, -.5, 0], # 2
    [-.5, -.5, 0], # 3
    [-.5,  .5, 0], # 4
    [ .5,  .5, 0], # 1

    [ .5,  .5, 1], # 5 
    [-.5,  .5, 0], # 4
    [ .5,  .5, 1], # 5

    [ .5, -.5, 1], # 6
    [-.5, -.5, 0], # 3
    [ .5, -.5, 1], # 6
    
    [ .5, -.5, 0], # 2
])    

theta = np.linspace(0, pi/4, 3)
peak = np.array([0, 0, 1])
cone = []
for i in range(8):
    t = theta + i * pi / 4
    arc = np.column_stack([cos(t)/2, sin(t)/2, np.zeros(len(t))])
    cone.append(arc)
    cone.append(peak)

theta = np.linspace(0, pi/4, 3)
cylinder = []
top = []
for i in range(8):
    t = theta + i * pi / 4
    arc = np.column_stack([cos(t)/2, sin(t)/2, np.zeros(len(t))])
    cylinder.append(arc)
    cylinder.append(arc[-1] + [0, 0, 1])
    cylinder.append(arc[-1])
cylinder = cylinder[:-2]
theta = np.linspace(0, 2 * pi, 17)
top = np.column_stack([cos(theta)/2, sin(theta)/2, np.ones(len(theta))])
cylinder.append(top)
cylinder = np.vstack(cylinder)

#print(bottom_square)
#print(top_square)
#print(square_columns)
#cube = Wireframe([bottom_square, top_square, *square_columns])
#prism = Wireframe([bottom_square, prism_front, prism_back, prism_top])
cube = Wireframe([cube_frame])
prism = Wireframe([prism_frame])
cone = Wireframe([np.vstack(cone)])
cylinder = Wireframe([cylinder])

__wireframes = {'Cube': cube,
                'Prism': prism,
                'Cone': cone,
                'Cylinder': cylinder}

def read_npy():
    out = {}
    for fn in glob.glob(f'{npy_dir}/*.npy'):
        name = os.path.split(fn)[1][:-4]
        out[name] = np.load(fn)
    return out

def from_stl_to_bounding_box(stl_fn):
    wf = things.STL(stl_fn).get_wireframe()
    mx = np.max(wf, axis=0)
    mn = np.min(wf, axis=0)
    dim = mx - mn
    pos = (mx + mn) / 2
    pos[2] = mn[2]
    return (wf - pos) / dim

def remove_wf(name):
    if name in __wireframes:
        del __wireframes[name]
def rename_wf(old, new):
    if new != old:
        add_wf(new, get(old), force=True)
        remove_wf(old)
def add_wf(name, wf, force=False):
    names = list(__wireframes.keys())
    if name.lower() in names and not force:
        raise ValueErrror(f'{name} already exists in wireframes')
    else:
        __wireframes[name] = wf
        np.save(f'{npy_dir}/{name}.npy', wf)
def getlist():
    out = list(__wireframes.keys())
    out.sort()
    return out

__wireframes = read_npy()
def get(name):
    npy = f'{npy_dir}/{name}.npy'
    if name not in __wireframes:
        if os.path.exists(npy):
            wf = np.load(npy)
            add_wf(name, wf)
        else:
            raise ValueError(f"Wireframe '{name}' not found")
    out = __wireframes[name]
    return out

if __name__ == '__main__':
    import isometric_view as iv
    import tkinter as tk
    from things import Group
    
    scene = Group()
    selected_group = Group()
    
    DEG = np.pi / 180
    scale = 1.
    theta = 240 * DEG
    phi =  10 * DEG

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
    
    root = tk.Tk()
    can1 = tk.Canvas(root, width=400, height=400)
    can1.grid(row=0, column=0)
    can2 = tk.Canvas(root, width=400, height=400)
    can2.grid(row=0, column=1)

    class Unit:
        def get(self):
            return 1
    unit = Unit()
    view1 = iv.IsoView(can1, -iso_x, iso_y, [200, 300], unit, unit, unit, unit)
    view2 = iv.IsoView(can2, [1, 0, 0], [0, 1, 0], [200, 200], unit, unit, unit, unit)

    views = iv.Views([view1, view2])
    print(from_stl('packages/STL/CornerTwoWay.stl'))
    draw_wireframe(from_stl('packages/STL/2020 Angle Bracket.stl'), 100, views)
    #draw_wireframe(cube, 100, views)
    #draw_wireframe(prism, 100, views)
    #draw_wireframe(cone, 100, views)
    #draw_wireframe(cylinder, 100, views)
    root.mainloop()

    #add_wf('Cone', cone, force=True)
    #add_wf('Cylinder', cylinder, force=True)
    #remove_wf('Aaa')
    #rename_wf('Corner_Plate_Threeway_Wf', 'T-Plate')
    #rename_wf('Gusset_Wireframe', 'Corner-Plate')
    #commit()
    
