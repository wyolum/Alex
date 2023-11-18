import numpy as np
from numpy import linalg as la
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh

na = np.newaxis

def PolyArea(xy):
    x,y = xy.T
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

fn = 'STL/Alex11.stl'
fn = 'STL/2020 Angle Bracket.stl'
mesh = mesh.Mesh.from_file(fn)
vectors = mesh.vectors
points = mesh.points

verts = points.reshape((-1, 3))

eps = 0.1

class Edge:
    def __init__(self, p1, p2):
        self.data = np.vstack([p1, p2])

    def dist(self, other):
        return np.min([la.norm(self.data - other.data),
                       la.norm(self.data - np.roll(other.data, axis=0))])

e1 = Edge([0, 0], [1, 1.])
e2 = Edge([1, 1], [0, 0])

print(e1.dist(e2))

