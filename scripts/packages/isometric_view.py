import numpy as np
import tkinter as tk
from tkinter import messagebox
from packages import util
from packages.constants import bgcolor, hlcolor

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

def noop(*args, **kw):
    pass

class IsoView:
    def __init__(self, can, ihat, jhat, offset, step_var, x_var, y_var, z_var,
                 shift_key=None, control_key=None, scale=1, bgcolor=bgcolor):
        self.can = can
        self.can.config(bg=bgcolor)
        self.ihat = np.array(ihat)
        self.jhat = np.array(jhat)
        self.khat = np.cross(self.ihat, self.jhat)
        self.B = np.column_stack([self.ihat, self.jhat])
        self.scale=scale
        self.offset = np.array(offset)
        self.step_var = step_var
        self.x_var = x_var
        self.y_var = y_var
        self.z_var = z_var
        self.can.bind('<ButtonPress-1>', self.onpress)
        self.can.bind('<ButtonRelease-1>', self.onrelease)
        self.can.bind('<Motion>', self.ondrag)
        self.can.bind('<ButtonPress-2>', self.detail_part)
        self.tags = {}
        self.dragging = False
        self.drag_initialized = False
        self.axes_on = True
        self.click_pt = np.array([0, 0])
        
        ### UI tracking
        self.button1_down = False
        if shift_key is None:
            shift_key = util.DummyKey()
        if control_key is None:
            control_key = util.DummyKey()
        self.shift_key = shift_key
        self.control_key = control_key

        self.draw_axes()

    def highlight_part(self, part, color):
        wf = part.get_wireframe()
        wf2d = wf @ self.B
        hull, hull_i = util.convexhull(wf2d)
        width = max([1, np.min([self.get_scale(), 3])]) * 2
        self.create_path("highlight", wf[hull_i], hlcolor, width) ### consider changing

    def toggle_axes(self):
        self.axes_on = not self.axes_on
        self.draw_axes()
        
    def redraw(self):
        self.can.delete('all')
        self.draw_axes()
        self.scene.render(self)
        
    def slew(self, delta_vec):
        self.offset += self.B.T @ delta_vec
        self.redraw()
        
    def set_scene(self, scene):
        self.scene = scene
        
    def erase_all(self):
        self.can.delete('all')
        
    def get_scale(self):
        return self.scale

    def invert_2d(self, v2d):
        return self.B @ (v2d - self.offset)/self.scale
    
    def project_2d(self, path):
        return path @ self.B * self.get_scale() + self.offset
    
    def create_polygon(self, thing, path, color, width):
        tag = str(thing)
        path = self.project_2d(path)
        id = self.can.create_polygon(*path.ravel(),
                                     tags=(tag,),
                                     fill=color,
                                     width=width, alpha=.3)
        
    def create_path(self, thing, path, color, width):
        path = path @ self.B * self.get_scale() + self.offset
        breaks = np.where(np.isnan(path[:,0]))[0]
        breaks = np.hstack([breaks, len(path) ])
        start = 0
        tag = str(thing)
        for stop in breaks:
            if stop == 2:
                if np.linalg.norm(np.diff(path[:2], axis=0)) < 1:
                    path[0] = path[0] - [width/2, width/2]
                    path[1] = path[1] + [width/2, width/2]
            args = path[start:stop].ravel()
            id = self.can.create_line(*args,
                                      tags=(tag,),
                                      fill=color,
                                      width=width)
            self.tags[id] = thing
            start = stop + 1
        return
            
    def create_line(self, thing, start, stop, color, width):
        return self.create_path(thing, [start, stop], color, width)

    def erase(self, thing):
        self.can.delete(str(thing))
        if hasattr(thing, 'iscontainer') and thing.iscontainer():
            for subthing in thing:
                self.erase(subthing)
                
    def onpress(self, event):
        if not hasattr(self, 'scene'):
            return
        self.click_pt = np.array([event.x, event.y])
        self.start = self.B @ self.click_pt / self.scale
        self.last = self.start
        self.button1_down = True
        
        clicked = self.can.find_closest(event.x, event.y)
        if len(clicked) > 0:
            closest = clicked[0]
            min_dist = 10
            coords = self.can.coords(closest)
            if len(coords) == 2:
                coords.append(coords[0]) ## repeat coords for follow on processing
                coords.append(coords[1])
            if len(coords) > 3:
                ### find closest segment
                mind = 1e9
                minp = None
                for i in range(0, len(coords) - 2, 2):
                    x0, y0, x1, y1 = coords[i:i+4]
                    p0 = [x0, y0]
                    p1 = [x1, y1]
                    p = self.click_pt
                    p, d = util.closest_pt_on_segment(p0, p1, p)
                    if d < mind:
                        mind = d
                        minp = p
                d = mind
                p = p
                if d < min_dist:
                    if closest in self.tags: ### something was clicked
                        clicked = self.tags[closest]
                        if  clicked == 'axes': ## axis was clicked..
                            self.dragging = False
                            for thing in self.scene.selected.ungroup():
                                thing.render(self.scene.view, selected=False)
                        else:                                          ### cant drag the axis
                            for thing in self.scene.things:            ### grab containing group
                                if thing.contains(clicked):
                                    clicked = thing
                            if self.scene.selected.contains(clicked):
                                ### already toggle selected status for clicked part
                                ### unless dragging starts??
                                if self.shift_key.pressed():
                                    self.scene.selected.remove(clicked)
                                    assert clicked not in self.scene.selected
                                    clicked.render(self.scene.view, selected=False)
                            else:
                                if self.shift_key.released():
                                    for thing in self.scene.selected.ungroup():
                                        thing.render(self.scene.view, selected=False)

                                self.scene.selected.append(clicked)
                                clicked.render(self.scene.view, selected=True)
                            self.dragging = True
                else:                                      ### nothing was clicked
                    if self.shift_key.released():
                        self.dragging = False
                        for thing in self.scene.selected.ungroup():
                            thing.render(self.scene.view, selected=False)

    def ondrag(self, event):
        if not hasattr(self, 'scene'):
            return
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.dragging:
            current = self.B @ np.array([event.x, event.y]) / self.scale
            delta = util.snap_to_grid(current - self.start, self.step_var.get())
            if self.control_key.pressed(): ### only allow one parameter to change
                keep = np.argmax(abs(delta))
                _delta = np.zeros(3)
                _delta[keep] = delta[keep]
                delta = _delta
            if np.linalg.norm(delta) > 0:
                if self.drag_initialized:
                    pass
                else:
                    self.drag_initialized = True
                    util.register_undo() ### make drag undoable
                new_pos = self.start + delta
                self.scene.selected.translate(new_pos - self.last)
                self.last = new_pos
                self.scene.selected.render(self.scene.view, selected=True)

        else:
            if self.button1_down:
                self.can.delete('selection_box')
                self.can.create_rectangle(self.click_pt[0], self.click_pt[1],
                                            event.x, event.y,
                                            tag=('selection_box',),
                                            outline='lightgrey')
            
            
    def onrelease(self, event):
        if not hasattr(self, 'scene'):
            return
        self.button1_down = False
        self.drag_initialized = False
        self.can.delete('selection_box')
        if self.dragging:
            self.dragging = False
            current = self.B @ np.array([event.x, event.y]) / self.scale
        else:
            corner_1 = (np.array([event.x, event.y]) - self.offset) / self.scale
            corner_2 = (self.click_pt - self.offset) / self.scale
            selection_box = Rectangle(corner_1, corner_2)
            for thing in self.scene:
                verts = thing.get_verts()
                verts = (self.B.T @ verts.T).T 
                if selection_box.contains(verts):
                    self.scene.selected.append(thing)
                    thing.render(self.scene.view, selected=True)
        self.scene.export()
        #if len(self.scene.selected) > 0:
        #    lengths = [thing.length for thing in self.scene.selected if not thing.iscontainer()]
        #    if np.max(lengths) - np.min(lengths) < 1e-2:
        #        pass ## TOOD? print('set length var tp length')
        #    
    def detail_part(self, event):
        print('Isometric View:: option menu!', event)
        clicked = self.can.find_closest(event.x, event.y)
        if len(clicked) > 0:
            closest = clicked[0]
            if closest in self.tags: ### something was clicked
                clicked = self.tags[closest]
                bom = clicked.tobom()[0].split(',')
                msg = (f'{bom[0]}\n{float(bom[1]):.0f}mm x {float(bom[2]):.0f}mm x {float(bom[3]):.0f}mm\n' +
                       f'{bom[4]}\n{bom[5]}')
                
                messagebox.showinfo("Details", msg)
    def draw_axes(self):
        if self.axes_on:
            id = self.can.create_oval(self.offset[0] - 2, self.offset[1] - 2,
                                 self.offset[0] + 2, self.offset[1] + 2, tags=('axes',))
            self.create_line('axes', [0, 0, 0], [50 / self.scale, 0, 0], color="red", width=.25)
            self.create_line('axes', [0, 0, 0], [0, 50 / self.scale, 0], color="green", width=.25)
            self.create_line('axes', [0, 0, 0], [0, 0, 50 / self.scale], color="blue", width=.25)
            self.tags[id] = 'axes'
            x, y = self.B.T @ ([55, 0, 0])
            if x ** 2 + y ** 2 > 10:
                id = self.can.create_text(x + self.offset[0], y + self.offset[1], text='x', font='times',
                                          tags=('axes',))
                self.tags[id] = 'axes'
            x, y = self.B.T @ ([0, 55, 0])
            if x ** 2 + y ** 2 > 10:
                id = self.can.create_text(x + self.offset[0], y + self.offset[1], text='y', font='times',
                                          tags=('axes',))
                self.tags[id] = 'axes'

            x, y = self.B.T @ ([0, 0, 55])
            if x ** 2 + y ** 2 > 10:
                id = self.can.create_text(x + self.offset[0], y + self.offset[1], text='z', font='times',
                                     tags=('axes',))
                self.tags[id] = 'axes'
        else:
            self.can.delete('axes')
                

    def set_scale(self, scale, mouse_xyz=None):
        s0 = self.scale
        self.scale = scale
        if mouse_xyz is not None:
            s1 = self.scale
            p = mouse_xyz
            
            c0 = self.offset + 0.
            c1 = (s0 - s1) * self.B.T @ p + c0
            
            self.offset = np.array(c1)
        self.redraw()

class Views:
    def __init__(self, views):
        self.views = views
        self.tag_dict = {}
        
    def __getitem__(self, idx):
        return self.views[idx]
        
    def apply(self, name, *args, **kw):
        '''
        execute named function on all views
        '''
        for view in self.views:
            getattr(view, name)(*args, **kw)

    def erase_all(self, *args, **kw):
        self.apply('erase_all', *args, **kw)
    def get_scale(self):
        return self.views[0].get_scale()
    def set_scene(self, scene):
        self.apply('set_scene', scene)
        self.scene = scene
    def create_path(self, *args, **kw):
        self.apply('create_path', *args, **kw)
    def erase(self, *args, **kw):
        self.apply('erase', *args, **kw)
    def create_line(self, *args, **kw):
        self.apply('create_line', *args, **kw)
    def draw_axes(self, *args, **kw):
        self.apply('draw_axes', *args, **kw)
    def set_scale(self, *args, **kw):
        self.apply('set_scale', *args, **kw)
    def slew(self, *args, **kw):
        self.apply('slew', *args, **kw)
    def toggle_axes(self, *args, **kw):
        self.apply('toggle_axes', *args, **kw)
    def highlight_part(self, *args, **kw):
        self.apply('highlight_part', *args, **kw)
        
def from_theta_phi(theta, phi, can, offset, step_var, x_var, y_var, z_var,
                   scale, shift_key=None, control_key=None, bgcolor=bgcolor):
    pov = -np.array([np.sin(phi),
                     0,
                    np.cos(phi)])

    pov = np.array([[np.cos(theta), np.sin(theta), 0],
                    [-np.sin(theta),  np.cos(theta), 0],
                    [         0,           0, 1]]) @ pov

    iso_z  = np.array([0, 0, 1])
    iso_z = iso_z - (iso_z @ pov) * pov
    iso_z /= np.linalg.norm(iso_z)
    iso_x = np.cross(pov, iso_z)
    iso_y = np.cross(iso_z, iso_x)

    return IsoView(can, -iso_x, iso_y, offset, step_var, x_var, y_var, z_var,
                   shift_key=shift_key, control_key=control_key, scale=scale, bgcolor=bgcolor)
    
def get_view(parent, theta, phi, offset, scale=1):
    
    pov = -np.array([np.sin(phi),
                    0,
                    np.cos(phi)])

    pov = np.array([[np.cos(theta), np.sin(theta), 0],
                    [-np.sin(theta),  np.cos(theta), 0],
                    [         0,           0, 1]]) @ pov

    iso_z  = np.array([0, 0, 1])
    iso_z = iso_z - (iso_z @ pov) * pov
    iso_z /= np.linalg.norm(iso_z)
    iso_x = np.cross(pov, iso_z)
    iso_y = np.cross(iso_z, iso_x)
    
    can = tk.Canvas(parent, width=400, height=400)
    can.grid()

    class constant:
        def get(self):
            return 1
    view = IsoView(can, -iso_x, iso_y, offset, constant, constant, constant, constant, scale=scale)
    return view
