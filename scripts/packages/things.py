import numpy as np
try:
    from stl import mesh
    STL_SUPPORTED = True
except ImportError:
    STL_SUPPORTED = False

from constants import mm, DEG
import util
import wireframes
import quaternion

class Thing:
    total = 0
    normal_color = 'black'
    select_color = 'red'
    def __init__(self):
        Thing.total += 1
        self.pos = np.array([0, 0, 0])
        self.orient = np.eye(3)
        
    def set_length(self, length):
        self.length = length
        
    def __del__(self):
        try:
            views.delete(self)
        except:
            pass
    def iscontainer(self):
        return False

    def contains(self, other):
        return self is other

    def rotate(self, roll=0, pitch=0, yaw=0):
        '''
        rotate in right angles
        x, y, z -- integer number of right angles (nominally between 0 and 3)
        '''
        self.orient = util.get_integer_rotation(roll, pitch, yaw) @ self.orient
        return self
    
    def translate(self, v):
        self.pos = self.pos + v
        return self
    
    def render(self, view, selected=False):
        raise NotImplemented('Abstract base class')

    def dup(self):
        out = []
        for thing in self:
            out.append(thing.dup())
        return Group(out)
    def toscad(self):
        raise NotImplemented("Abstract Base Class")
    def tobom(self):
        raise NotImplemented("Abstract Base Class")
    def get_orientation_angle_and_vec(self):
        #q = quaternion.from_rotation_matrix(self.orient) ## numpy-quaternion
        q = quaternion.Quaternion(matrix=self.orient)## pyquaternion
        angle = q.angle
        # vec = q.vec ## numpy-quaternion
        vec = q.vector ## pyquaternion
        return angle, vec

class Group(Thing):
    def __init__(self, things=None):
        Thing.__init__(self)
        if things is None:
            things = []
        self.things = things
        if len(things) > 0:
            self.pos = np.mean(self.get_verts(), axis=0)
    def __len__(self):
        return len(self.things)
    
    def iscontainer(self):
        return True

    def __getitem__(self, idx):
        return self.things[idx]

    def __str__(self):
        out = ['Group([']
        for thing in self:
            out.append('   ' + str(thing) + ',')
        out.append('])')
        return '\n'.join(out)

    def get_verts(self):
        out = []
        for thing in self:
            out.append(thing.get_verts())
        if out:
            out = np.vstack(out)
        else:
            out = np.array(out)
        return out
            
    def contains(self, thing):
        out = thing in self.things
        if not out:
            for t in self:
                if t.contains(thing):
                    out = True
                    break
        return out

    def append(self, thing):
        if thing not in self.things:
            self.things.append(thing)
        thing.group = self

    def remove(self, thing):
        if thing in self.things:
            idx = self.things.index(thing)
            self.things.pop(idx)

    def ungroup(self):
        out = self.things
        self.things = []
        return out

    def translate(self, *args, **kw):
        if len(self) == 0:
            pass
        else:
            for thing in self.things:
                thing.translate(*args, **kw)
            self.pos = np.mean(self.get_verts(), axis=0)
        return self

    def get_center(self):
        verts = self.get_verts()
        if len(verts) > 0:
            ### return center of bounding box
            maxs = np.max(verts, axis=0)
            mins = np.min(verts, axis=0)
            center = (maxs + mins) / 2
        else:
            center = np.zeros(3)
        return center
    
    def rotate(self, *args, **kw):
        if len(self.things) == 1:
            center_of_rotation = self.things[0].pos
        else:
            center_of_rotation = self.get_center()
        c = center_of_rotation
        R = util.get_integer_rotation(*args, **kw)
        for thing in self.things:
            thing.rotate(*args, **kw)
            p0 = thing.pos.copy()
            p1 = R @ (p0 - c) + c
            thing.translate(p1 - p0)

    def render(self, view, selected=False):
        for thing in self:
            thing.render(view, selected=selected)
            
        center = self.get_center()
        #view.create_path(self, [center - [10, 0, 0], center + [10, 0, 0]], 'black', 1)
        #view.create_path(self, [center - [0, 10, 0], center + [0, 10, 0]], 'black', 1)
        #view.create_path(self, [center - [0, 0, 10], center + [0, 0, 10]], 'black', 1)

    def toscad(self):
        out = ['union(){']
        for thing in self:
            out.append('  ' + util.indent(thing.toscad(), 2))
        out.append('}')
        return '\n'.join(out)
    
    def tobom(self):
        lines = []
        for thing in self.things:
            lines.extend(thing.tobom())
        return lines
    def cost(self):
        out = 0
        for thing in self:
            out += thing.cost()
        return out
def Group__test__():
    g = Group()
    t = Thing()
    s = Thing()
    g.append(t)
    assert t in g
    assert s not in g
# Group__test__()

class STL(Thing):
    normal_color = 'lightgrey'
    select_color = 'salmon'
    def __init__(self, filename, cost=0, unit=mm):
        self.filename = filename
        self.mesh = mesh.Mesh.from_file(self.filename)
        self.vectors = self.mesh.vectors
        self.points = self.mesh.points
        
        maxs = np.max(self.points.reshape((-1, 3)), axis=0)
        mins = np.min(self.points.reshape((-1, 3)), axis=0)
        
        left = mins[0]
        right = maxs[0]
        self.dim1 = right - left
        
        back = maxs[1]
        front = mins[1]
        self.dim2 = back - front
        
        top = maxs[2]
        bottom = mins[2]
        self.length = top - bottom

        self.wireframe = wireframes.get('Cube')
        d1 = right - left
        d2 = back - front
        length = top - bottom
        Thing.__init__(self)
        self.offset = np.array([-self.dim1 / 2, -self.dim2 / 2, -bottom])
        self.offset = np.array([0, 0, -bottom])
        self.__cost = cost

    def cost(self):
        return self.__cost
    
    def toscad(self):
        off = self.offset
        pos = self.pos + 2 * off
        out = []
        angle, vec = self.get_orientation_angle_and_vec()
        out.append(f'translate([{pos[0]}, {pos[1]}, {pos[2]}])')
        out.append(f'  rotate(a={angle / DEG:.0f}, v=[{vec[0]:.4f}, {vec[1]:4f}, {vec[2]:4f}])')
        out.append(f'  color([0, 1, 0])translate([{-off[0]}, {-off[1]}, {-off[2]}])import("{self.filename}");')
        return ''.join(out)

    def get_wireframe(self):
        return self.wireframe * [self.dim1, self.dim2, self.length] @ self.orient.T + self.pos
    
    def render(self, view, selected=False):
        view.erase(self)
        if selected:
            color = self.select_color
            width = max([1, np.min([view.get_scale(), 3])])
        else:
            color = self.normal_color
            width = max([1, np.min([view.get_scale(), 1.5])])
        wf = self.get_wireframe()
        view.create_path(self, wf, color, width)
    def get_verts(self):
        return self.get_wireframe()

class Selected(Group):
    pass

class Scene(Group):
    def __init__(self, view, selected):
        Group.__init__(self, [])
        self.view = view
        self.selected = selected
        self.view.set_scene(self) ### allow view to access Scene

    def delete_all(self):
        for thing in self:
            self.view.erase(thing)
            del thing
        self.things = []
        
    def render(self, *args): ### ignore args, use self.view
        for thing in self:
            if thing not in self.selected:
                thing.render(self.view, selected=False)
        for thing in self.selected:
            thing.render(self.view, selected=True)

    def append(self, thing, select=False):
        Group.append(self, thing)
        if select:
            self.selected.append(thing)
            selected=True
        else:
            selected=False
        thing.render(self.view, selected=selected)
        self.export()
    def remove(self, thing):
        Group.remove(self, thing)
        self.view.erase(thing)
        self.export()
    def ungroup(self):
        raise NotImplimented("Cannot ungroup Scene, remove items individually")
    def translate(self, *args, **kw):
        Group.translate(self, *args, **kw)
        self.view.erase_all()
        self.render(self.view)

    def export(self):
        with open("Alex_test.scad", 'w') as f:
            for thing in self:
                if thing not in self.selected:
                    f.write(thing.toscad())
            for thing in self.selected:
                f.write("#" + thing.toscad())

            f.close()
