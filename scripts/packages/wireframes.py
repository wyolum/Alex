import os.path
import numpy as np
from numpy import cos, sin

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
    

#print(bottom_square)
#print(top_square)
#print(square_columns)
#cube = Wireframe([bottom_square, top_square, *square_columns])
#prism = Wireframe([bottom_square, prism_front, prism_back, prism_top])
cube = Wireframe([cube_frame])
prism = Wireframe([prism_frame])
__wireframes = {'Cube': cube,
                'Prism': prism}

npz = 'wireframes.npz'
def write_npz(force=False):
    mydir = constants.package_dir
    fn = os.path.join(mydir, npz)
    if os.path.exists(fn) and not force:
        print(npz, 'already exists')
    else:
        np.savez(fn, **__wireframes)
        print('wrote', npz)
    
def read_npz():
    mydir = os.path.split(os.path.abspath(__file__))[0]
    mynpz = os.path.join(mydir, npz)
    if os.path.exists(mynpz):
        _npz = np.load(mynpz)
        out = {}
        for k in _npz:
            print(k)
            out[k] = _npz[k]
        
    else:
        out = {}
    return out

def from_stl(stl_fn):
    wf = things.STL(stl_fn).get_wireframe()
    mx = np.max(wf, axis=0)
    mn = np.min(wf, axis=0)
    dim = mx - mn
    pos = (mx + mn) / 2
    pos[2] = mn[2]
    return (wf - pos) / dim

def add_wf(name, wf):
    names = [n.lower for n in list(__wireframes.keys())]
    if name.lower() in names:
        raise ValueErrror(f'{name} already exists in wireframes')
    else:
        __wireframes[name] = wf
def getlist():
    return list(__wireframes.keys())
def commit():
    write_npz(force=True)
__wireframes = read_npz()
def get(name):
    return __wireframes[name]

if __name__ == '__main__':
    import isometric_view as iv
    import tkinter as tk
    from things import Group
    write_npz()
    
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
    view1 = iv.IsoView(can1, -iso_x, iso_y, [200, 300], Unit())
    view2 = iv.IsoView(can2, [1, 0, 0], [0, 1, 0], [200, 200], Unit())

    views = iv.Views([view1, view2])
    draw_wireframe(cube + [0, 0, 0], [200, 200, 200], views)
    draw_wireframe(prism, 100, views)
    root.mainloop()

