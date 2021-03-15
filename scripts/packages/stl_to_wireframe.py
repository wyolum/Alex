import time
import numpy as np
from numpy import linalg as la
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh
import sys
if '.' not in sys.path:
    sys.path.append('.')
from packages.constants import stl_dir, alex_dir
DEG = np.pi / 180

na = np.newaxis

def PolyArea(xy):
    x,y = xy.T
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

eps = 0.01

class Edge:
    def __init__(self, p0, p1):
        self.data = np.vstack([p0, p1]).astype(float)
        self.p0 = self.data[0]
        self.p1 = self.data[1]
        self.dir = (self.p1 - self.p0) / la.norm(self.p1 - self.p0)

    def __getitem__(self, i):
        return self.data[i]
    
    def dist(self, other):
        return la.norm(self.data - other.data)

    def __neg__(self):
        return Edge(self.p1, self.p0)
    def __repr__(self):
        return f'Edge({self.p0}, {self.p1})'
    def connected(self, other):
        return la.norm(self.p1 - other.p0) < eps

    def angle(self, other):
        if self.connected(other):
            s = (self.dir[0] * other.dir[1] - self.dir[1] * other.dir[0])
            c = self.dir @ other.dir
            out = np.arctan2(s, c)
        else:
            print(self, other, 'not connected')
            out = np.nan
        return out
    def plot(self, color=None, alpha=1, arrow=False):
        d = (self.p1 - self.p0)
        ## shrink d by head width
        if color is None:
            style = '-'
        else:
            style = '%s-' % color
        if arrow:
            head_width = .0125
            d = d * la.norm(d) / (la.norm(d) + head_width)
            pl.arrow(self.p0[0], self.p0[1], d[0], d[1], color=color, head_width=head_width, alpha=alpha)
        else:
            pl.plot([self.p0[0], self.p1[0]],
                    [self.p0[1], self.p1[1]], style, alpha=alpha)
        
class Path:
    def __init__(self, edges):
        self.edges = list(edges)
        if len(edges) > 0:
            self.start = edges[0].p0
            self.stop = edges[-1].p1
    def __repr__(self):
        body = '\n'.join(['    ' + str(e) for e in self.edges])
        return '\n'.join(['Path(', body, ')'])
    def __getitem__(self, i):
        return self.edges[i]
    def __len__(self):
        return len(self.edges)
    def get_xy(self):
        n = len(self) + 1
        out = []
        if len(self):
            last = self[0]
            out.append(self[0].p0)
            out.append(self[0].p1)
            for edge in self[1:]:
                if not last.connected(edge):
                    out.append([np.nan, np.nan])
                    out.append(edge.p0)
                out.append(edge.p1)
                last = edge
        return np.array(out)
            
    def append(self, edge):
        self.edges.append(edge)
        self.stop = edge.p1
        if len(self.edges) == 1:
            self.start = edge.p0

    def extend(self, other):
        self.edges.extend(other.edges)
        self.stop = other.stop
            
    def connected(self):
        out = True
        if len(self.edges) > 0:
            last= self.edges[0]
        for e in self.edges[1:]:
            if not last.connected(e):
                out = False
                break
            last = e
        return out
    
    def closed(self):
        return self.connected() and la.norm(self.start - self.stop) < eps

    def area(self):
        if self.closed():
            n = len(self.edges)
            xy = np.zeros((n, 2))
            for i, e in enumerate(self.edges):
                xy[i] = e.p0
            return PolyArea(xy)
        else:
            return np.nan

    def angles(self):
        last = self.edges[0]
        out = []
        for next in self.edges[1:]:
            out.append(last.angle(next))
            last = next
        if self.edges[-1].connected(self.edges[0]):
            out.append(self.edges[-1].angle(self.edges[0]))
        return np.array(out)

    def plot(self, arrow=False, color=None):
        for e in self.edges:
            e.plot(arrow=arrow, color=color)
            
        if len(self.edges) > 0:
            last = self.edges[0]
            xy = [last.p0, last.p1]
            for e in self.edges[1:]:
                if last.connected(e):
                    xy.append(e.p1)
                else:
                    xy.append([np.nan, np.nan])
                    xy.append(e.p0)
                    xy.append(e.p1)
                last = e
            xy = np.array(xy)
            if self.closed():
                pl.plot(xy[:,0], xy[:,1], 'b')
                pl.fill(xy[:,0], xy[:,1], alpha=.3)
                # print(xy)
            else:
                pass
                # pl.plot(xy[:,0], xy[:,1], 'r')
    def contains(self, p):
        if self.closed():
            angle_sum = 0
            for edge in self:
                if la.norm(p - edge.p0) < 1e-8 or la.norm(p - edge.p1) < 1e-8:
                    angle = np.pi
                else:
                    d1 = edge.p0 - p
                    d2 = edge.p1 - p
                    angle = np.arccos((d1 @ d2) / (la.norm(d1) * la.norm(d2)))
                angle_sum += angle
            out = angle_sum > np.pi
            # print(angle_sum, out)
        else:
            out = False
        return out

def perimeter_edges(edges, max_time_sec=10, start_sec=None):
    if start_sec is None:
        start_sec = time.time()
    if time.time() - start_sec > max_time_sec:
        raise ValueError(f'Perimiter is too complex.  Exceeded {max_time_sec} second allocation.')
    left = np.inf
    for e in edges:
        for p in e:
            if p[0] < left:
                left = p[0]

    ### find all points with this left
    upness = -np.inf
    best = Edge([0, 0], [1, 0])
    for e in edges:
        if np.min(np.abs(e.data[:,0] - left)) < eps:
            if np.abs(e.dir[1]) > upness:
                if e.dir[1] > 0:
                    best = e
                    upness = best.dir[1]
                else:
                    best = -e
                    upness = best.dir[1]
    path = Path([best])

    iter = 0
    while len(path) < len(edges) and not path.closed():
        ### find all points that share end of path
        options = []
        for e in edges:
            if path[-1].connected(e):
                if path[-1].dist(-e) > 0:
                    options.append(e)

        # find left most turn
        most_ccw = -np.inf
        for option in options:
            ccw = path[-1].angle(option)
            if ccw > most_ccw:
                most_ccw = ccw
                best = option
        path.append(best)
        if False:
            pl.close('all')
            pl.figure(figsize=(6, 6))
            for e in edges:
                e.plot(color='r', alpha=.05)
            for op in options:
                op.plot(color='k')
            best.plot(color='b')
            path.plot(color='g', arrow=True)
            pl.axis('equal')
            pl.axis('off')
            #print(options)
            #print(most_ccw, best)
            #print()
            pl.savefig(f'/Users/justin/code/Alex/images/path/{len(path):04d}.png')
            # pl.show()
    ### thow away all edges that are not contained in perimeter.
    keep = []
    for i, e in enumerate(edges):
        if path.contains(e.p0) or path.contains(e.p1):
            pass
        else:
            keep.append(i)
    if keep:
        tri_2d = []
        edges = [edges[i] for i in keep]
        island = perimeter_edges(edges, max_time_sec=max_time_sec, start_sec=start_sec)
        path.extend(island)
    return path

def perimeter(triangles_2d):
    ### n x 3 x 2
    idx = []
    edges = []
    for t in triangles_2d:
        for i in range(3):
            edges.append(Edge(t[i], t[(i + 1) % 3]))
            #edges[-1].plot()
            edges.append(-edges[-1])
            #edges[-1].plot()
    ### find left most point
    out = perimeter_edges(edges)
    return out

def get_face(vectors, d, eps=eps):
    vals = vectors @ d
    mx = np.amax(vals)
    
    b2_index = np.abs(d) < eps
    b2 = np.eye(3)[:,b2_index]
    keep = np.all(vals > mx - eps, axis=1)
    plane = vectors[keep]

    p2 = plane @ b2
    return keep, p2, mx, b2


def from_stl(stl_fn):
    stl = mesh.Mesh.from_file(stl_fn)
    vectors = stl.vectors
    #### normalize
    mx = np.amax(vectors.reshape((-1, 3)), axis=0)
    mn = np.amin(vectors.reshape((-1, 3)), axis=0)

    dim = mx - mn
    pos = (mx + mn) / 2
    pos[2] = mn[2]
    vectors = (vectors - pos) / dim

    ds = np.vstack([np.eye(3),
                    -np.eye(3)])
    wf = []
    nn = 0
    for d in ds:
        idx, p2, mx, b2 = get_face(vectors, d, eps=eps)
        path = perimeter(p2)
        xy = path.get_xy()
        p3 = (b2 @ xy.T).T + d * mx
        wf.append(p3)
        nn += len(p3)
    _wf = np.empty((nn + len(wf) - 1, 3)) * np.nan
    ii = 0
    for w in wf:
        _wf[ii:ii+len(w)] = w
        ii += len(w) + 1
    return _wf

if __name__ == '__main__':
    wf = from_stl(f'{alex_dir}/part_libraries/Main/STL/2020 Alex.stl')
    #wf = from_stl(f'{alex_dir}/part_libraries/Justin/STL/CylinderLamp.stl')
    #wf = from_stl('/Users/justin/Desktop/trilobe_nut_knob-qtr_inch.stl')
    pl.close('all')
    pl.figure(); pl.gca(projection='3d')
    pl.plot(wf[:,0],
            wf[:,1],
            wf[:,2], 'b-')
    #np.save('wireframes/Plate-T.npy', wf)
    pl.show()
    here
if False:
    e0 = Edge([0, 0], [1, 1.])
    e1 = Edge([1, 1], [0, 0])
    e3 = Edge([2, 2], [2, 1])

    t0 = Edge([0, 0], [1, 0])
    t1 = Edge([1, 0], [1, 1])
    t2 = Edge([1, 1], [0, 0])

    u0 = Edge([0, 0], [0, 1])
    u1 = Edge([0, 1], [1, 1])
    u2 = Edge([1, 1], [0, 0])
    
    w0 = Edge([0, 1], [.5, 2])
    w1 = Edge([.5, 2], [1, 1])
    w2 = Edge([1, 1], [0, 1])
    w3 = Edge([.5, 2], [.25, 2])
    w4 = Edge([.25, 2], [0, 1])

    w5 = Edge([1, 1], [2, .4])
    w6 = Edge([2, .4], [.5, 2])

    w7 = Edge([2, .4], [1.5, .5])
    w8 = Edge([1.5, .5], [1, 1])
    
    path0 = Path([e0, e1])
    path1 = Path([e0, e1, e3])
    triangle0 = Path([t0, t1, t2])
    triangle1 = Path([u0, u1, u2])
    triangle2 = Path([w0, w1, w2])
    triangle3 = Path([w0, w3, w4])
    triangle4 = Path([w1, w5, w6])
    triangle5 = Path([w5, w7, w8])
    

    assert e0.dist(e1) == 2
    assert e0.dist(-e1) == 0

    assert path0.connected()
    assert not path1.connected()

    assert triangle0.connected()
    assert triangle0.closed()
    p1 = [.8, .2]
    p2 = [2, .2]
    #triangle0.plot()
    #pl.plot(p1[0], p1[1], 'bo')
    #pl.plot(p2[0], p2[1], 'ro')
    assert triangle0.contains(p1)
    assert not triangle0.contains(p2)
    
    assert triangle0.area() == .5
    # print(triangle0)

    assert la.norm(triangle0.angles() / DEG - [90, 135, 135]) < 1e-9
    
    triangle0.plot()
    triangle1.plot()
    triangle2.plot()
    triangle3.plot()
    triangle4.plot()
    triangle5.plot()

    #pl.show()
    #here
    
    #path0.plot()
    #path1.plot()

    stl = [triangle0, triangle1, triangle2, triangle3, triangle4, triangle5]
    triangles = []
    for t in stl:
        xy = [t[i].p0 for i in range(3)]
        triangles.append(xy)
    triangles = np.array(triangles)

    # print(vectors)
    here

    
    here
    perimeter(triangles).plot()
    pl.show()
    here
    for tri in stl:
        tri.plot()
    # pl.show()
    edges = []
    for t in stl:
        edges.extend(t.edges)
    
    ### find left most point
    left = np.inf
    for e in edges:
        for p in e:
            if p[0] < left:
                left = p[0]

    ### find all points with this left
    upness = -np.inf
    for e in edges:
        if np.min(np.abs(e.data[:,0] - left)) < eps:
            if np.abs(e.dir[1]) > upness:
                if e.dir[1] > 0:
                    best = e
                    upness = best.dir[1]
                else:
                    best = -e
                    upness = best.dir[1]
    print(best)
    print('left', left)
    path = Path([best])

    while len(path) < len(edges) and not path.closed():
        ### find all points that share end of path
        options = []
        for e in edges:
            # print(e, path[-1].connected(e), path[-1].connected(-e))
            if path[-1].connected(e):
                if path[-1].dist(-e) > 0:
                    options.append(e)
            elif path[-1].connected(-e):
                if path[-1].dist(e) > 0:
                    options.append(-e)
        # find left most turn
        most_ccw = -np.inf
        for option in options:
            ccw = path[-1].angle(option)
            if ccw > most_ccw:
                most_ccw = ccw
                best = option
        path.append(best)
        if True:
            pl.clf()
            path.plot()
            for t in stl:
                for e in t:
                    e.plot(color='r', alpha=.3)
            for op in options:
                print(op, path[-1].angle(op))
                op.plot(color='k')
            best.plot(color='b')
            print(options)
            print(most_ccw, best)
            print()
            pl.show()
            
    pl.clf()
    path.plot()
    pl.show()





    
