import os.path
import numpy as np
from numpy import cos, sin
import constants

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

npz = 'wireframes.npz'
def write_npz():
    mydir = constants.package_dir
    np.savez(os.path.join(mydir, npz), Cube=cube, Prism=prism)
    print('wrote', npz)
    
def read_npz():
    mydir = os.path.split(os.path.abspath(__file__))[0]
    mynpz = os.path.join(mydir, npz)
    if os.path.exists(mynpz):
        out = np.load(mynpz)
    else:
        out = {}
    return out

wireframes = read_npz()
def get(name):
    return wireframes[name]

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

