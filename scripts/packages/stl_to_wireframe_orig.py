import numpy as np
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh

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
def merge_2d_poly(poly0, poly1, eps=eps):
    '''
    remove any shared edges of two polygons to return a single polygon.  If now shared edges, return two polys with row
    of nans inbetween
    polys are 2D polys nx2
    '''
    print(poly0.shape, poly1.shape)
    n0 = len(poly0)
    n1 = len(poly1)
    idx0 = np.arange(n0)
    idx1 = np.arange(n1)

    mid0 = (poly0 + np.roll(poly0, 1, axis=0))/2
    mid1 = (poly1 + np.roll(poly1, 1, axis=0))/2
    dists = np.linalg.norm(mid1[np.newaxis] - mid0[:,np.newaxis], axis=2)
    matches = np.column_stack(np.where(dists < eps))
    if len(matches) == 0:
        return idx0, idx1
    if len(matches) > 1:
        pass
        # print(ValueError("only one shared edge allowed, ignoring extras"))
    match = matches[0]
    i, j = match
    
    idx0 = idx0[idx0 != i]
    idx1 = idx1[idx1 != i]

    if np.linalg.norm(poly0[i] - poly1[j]) < eps:
        return idx0, idx1[::-1]
    else:
        return idx0, idx1
    return idx0, idx1

def keep_left(triangles_2d):
    ### n x 3 x 2
    t2d = triangles_2d
    
    x = triangles_2d[:,:,0]
    left = np.min(x)
    for t in t2d:
        i = np.argmin(abs(t[:,0] - left))
        if t[i,0] == left:
            start = t[i]
            print(i)
            if PolyArea(t) < 1e-6:
                j = np.argmax(np.linalg.norm(t - t[i], axis=1))
            else:
                j = np.argsort(t[:,0])[1]
            edge = [t[i], t[j]]
            dir = edge[-1] - edge[-2]
            dir = dir / np.linalg.norm(dir)
            break
    ### find all edges that share last point
    while np.linalg.norm(edge[-1] - edge[0]) > 1e-9:
        options = []    
        for t in t2d:
            ds = np.linalg.norm(t - edge[-1], axis=1)
            for i in range(3):
                if ds[i] < 1e-9:
                    op = t[(i + 1) % 3]
                    if np.min(np.linalg.norm(op - np.array(edge), axis=1)) > 1e-6:
                        options.append(op)
                    op = t[(i - 1) % 3]                        
                    if np.min(np.linalg.norm(op - np.array(edge), axis=1)) > 1e-6:
                        options.append(op)
        best = -100
        best_i = None
        for i, option in enumerate(options):
            op = option - edge[-1]
            op /= np.linalg.norm(op)
            val = np.linalg.det(np.vstack([dir, op]))
            if val > best:
                best = val
                best_i = i
        if best_i is None:
            break
        edge.append(options[best_i])
        print(len(edge), len(t2d))
    print(edge)
    edge = np.array(edge)
    #pl.plot(edge[:,0], edge[:,1])
    #pl.show()
    return edge

def get_face(vectors, d, eps=eps):
    vals = vectors @ d
    mx = np.amax(vals)
    
    b2_index = np.abs(d) < eps
    b2 = np.eye(3)[:,b2_index]
    keep = np.all(vals > mx - eps, axis=1)
    plane = vectors[keep]

    p2 = plane @ b2
    idx = keep_left(p2)
    return keep, p2

dirs = np.vstack([np.eye(3),
                  -np.eye(3)])
wfs = []
pl.figure();pl.gca(projection='3d')
for dir in dirs:
    keep, p2 = get_face(vectors, dir)
    p3 = vectors[keep]
    nkeep = np.sum(keep)
    
    if nkeep == 0:
        continue
    if nkeep == 1:
        outline3 = p3[0]
        outline2 = p2[0]
    else:
        idx0, idx1 = merge_2d_poly(p2[0], p2[1])
        outline2 = np.vstack([p2[0][idx0], p2[1][idx1]])
        outline3 = np.vstack([p3[0][idx0], p3[1][idx1]])
        for p_3d, p_2d in zip(p3[2:], p2[2:]):
            idx0, idx1 = merge_2d_poly(outline2, p_2d)
            outline3 = np.vstack([outline3[idx0], p_3d[idx1]])
            outline2 = np.vstack([outline2[idx0], p_2d[idx1]])
    outline3 = np.vstack([outline3, outline3[0], [np.nan, np.nan, np.nan]])
    wfs.append(outline3)
    # pl.plot(outline3[:,0], outline3[:,1], outline3[:,2])
wfs = np.vstack(wfs)
#pl.plot(wfs[:,0], wfs[:,1], wfs[:,2])

pl.show()
here
    
    
