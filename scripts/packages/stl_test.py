import numpy as np
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh

def PolyArea(xy):
    x,y = xy.T
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

fn = 'STL/Cube.stl'
mesh = mesh.Mesh.from_file(fn)
vectors = mesh.vectors
points = mesh.points
print(vectors.shape)
print(points.shape)
verts = points.reshape((-1, 3))

def merge(poly0, poly1):
    '''
    remove any shared edges of two polygons to return a single polygon.  If now shared edges, return two polys with row
    of nans inbetween
    polys are 2D polys nx2
    '''
    mid0 = (poly0 + np.roll(poly0, 1, axis=0))/2
    mid1 = (poly1 + np.roll(poly1, 1, axis=0))/2
    dists = np.linalg.norm(mid1[np.newaxis] - mid0[:,np.newaxis], axis=2)
    matches = np.column_stack(np.where(dists < eps))
    if len(matches) > 1:
        raise ValueError("only one shared edge allowed")
    match = matches[0]
    i, j = match
    p0 = np.roll(poly0, -i, axis=0)[1:]
    p1 = np.roll(poly1, -j, axis=0)[1:]
    if np.linalg.norm(poly0[i] - poly1[j]) < eps:
        return merge(poly0, poly1[::-1])
    else:
        print(i, j, 'reverse')
        return np.vstack([p0, p1])
    return poly0, poly1
    
    
n = len(verts)

vv = vectors.reshape((-1, 3))

maxs = np.max(vv, axis=0)
top = maxs[2]
eps = .0001
top_vectors = vectors[np.min(vectors[:,:,2], axis=1) > top - eps]
top_mids = (np.roll(top_vectors, 1, axis=1) + top_vectors)/2

top_area = 0
for vector in top_vectors:
    top_area += PolyArea(vector[:,:2])

print(top_area)
print(PolyArea(top_vectors[:,::2,:2].reshape((-1, 2))))
print(top_vectors[0,:,:2])
print(top_vectors[1,:,:2])
top = merge(top_vectors[0,:,:2], top_vectors[1,:,:2])
pl.plot(top[:,0], top[:,1], '-')
top = merge(top, [[1, 0], [.5, -1], [0, 0]])
pl.plot(top[:,0], top[:,1], '-')
top = merge(top, [[1, 1], [5, 1], [1, 0]])
pl.plot(top[:,0], top[:,1], '-')
print(top)
top = np.vstack([top, top[0]])
pl.plot(top[:,0], top[:,1], 'k-')
pl.show()
here
top_mids = top_mids.reshape((-1, 3))
dists = np.linalg.norm(top_mids[np.newaxis] - top_mids[:,np.newaxis], axis=-1) + np.eye(len(top_mids))
dups = np.vstack(np.where(dists < eps)).T
pl.pcolormesh(dists)
pl.plot(dups[:,0], dups[:,1], 'ro')
pl.show()
here
eps = 1e-3
top_pts = vv[vv[:,2] > top - eps]

pl.figure();pl.gca(projection='3d')
segments = []
for i, f in enumerate(vectors):
    f = np.vstack([f, f[0]])
    for start in range(3):
        segments.append([f[start], f[start + 1]])
    pl.plot(f[:,0], f[:,1], f[:,2], 'k-', alpha=.3)
segments = np.array(segments)
starts = segments[:,0]
stops = segments[:,1]
top_segs = segments[np.logical_and(starts[:,2] > top - eps,
                                   stops[:,2] > top - eps)]
top_mids = (top_segs[:,0] + top_segs[:,1])/2
top_dists = np.linalg.norm(top_mids[np.newaxis] - top_mids[:,np.newaxis], axis=-1) + np.eye(len(top_mids))

## dedup
print(top_mids.shape, verts.shape)

pl.plot(top_mids[:,0], top_mids[:,1], top_mids[:,2], 'bo')

ij = np.column_stack(np.where(top_dists < .01))
keep = ij[:,0] < ij[:,1]
top_mids = top_mids[keep]

tm = top_mids[:,:2] + np.random.random(top_mids[:,:2].shape)/100.
pl.figure();
pl.plot(tm[:,0], tm[:,1], 'ro')
pl.plot(top_segs[:,:,0].ravel(),
        top_segs[::,:,1].ravel(), 'b-', alpha=.3)
pl.show()
