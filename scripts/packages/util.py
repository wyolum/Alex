import numpy as np
from numpy import sin, cos, pi

def numbers_only(var, entry):
    def out(*args, **kw):
        text = var.get()
        new_text = ''.join([c for c in text if c in '0123456789.+-'])
        var.set(new_text)
    return out

def change_color(label, color):
    print('change_color()::', color)
    label.config(fg=color)

class KeyboardTracker:
    '''
    Track when shift is press or released.
    '''
    def __init__(self, parent):
        self.parent = parent
        #self.parent.bind('<Shift_L>', self.pressed)
        self.parent.bind("<KeyPress>", self.keydown)
        self.parent.bind("<KeyRelease>", self.keyup)
        self.state = {}
        
    def keyup(self, event):
        if event.keysym not in self.state:
            self.state[event.keysym] = False
        self.state[event.keysym] = False

    def keydown(self, event):
        if event.keysym not in self.state:
            self.state[event.keysym] = True
        self.state[event.keysym] = True
              
    def released(self, keysym):
        if keysym not in self.state:
            self.state[keysym] = False
        return self.state[keysym]

class KeyTracker:
    def __init__(self, keyboard_tracker, key):
        self.keyboard = keyboard_tracker
        self.key = key
    def pressed(self):
        return self.keyboard.released(self.key)
    def released(self):
        return not self.pressed()

class ShiftTracker(KeyTracker):
    def __init__(self, key_tracker):
        KeyTracker.__init__(self, key_tracker, 'Shift_L')
class ControlTracker(KeyTracker):
    def __init__(self, key_tracker):
        KeyTracker.__init__(self, key_tracker, 'Control_L')

### test keys
if False:
    import tkinter
    root = tkinter.Tk()
    kb = KeyboardTracker(root)
    shift = ShiftTracker(kb)
    ctrl = ControlTracker(kb)
    def after(*args):
        print(ctrl.pressed(), shift.pressed())
        root.after(1000, after)
    root.after(1000, after)
    root.mainloop()
    here

def indent(s, n):
    '''
    Indent each line of s n spaces
    '''
    indent = ' ' * n
    return ('\n%s' % indent).join(s.splitlines())

def find_closest_in_group(pt_2d, group, projection_2d):
    '''
    find closest point in group (projected to 2d) to pt_2d
    '''
    print("find_closest_in_group", pt_2d, group)

    mind = 1e6
    minp = None
    for item in group:
        wf = projection_2d(item.get_wireframe())
        
        for p0, p1 in zip(wf[:-1], wf[1:]):
            pt, d = closest_pt_on_segment(p0, p1, pt_2d)
            if d < mind:
                mind = d
                minp = pt
        return minp, mind
    
def closest_pt_on_segment(p0, p1, p):
    '''
    all points in 2D
    '''
    p0 = np.array(p0)
    p1 = np.array(p1)
    p = np.array(p)
    b0 = (p1 - p0).astype(float)
    D = np.linalg.norm(b0)
    if D == 0:
        dist = np.linalg.norm(p - p0)
        out = p0
    else:
        b0 /= D
        b1 = np.array([-b0[1], b0[0]])
        B = np.vstack([b0, b1])
        x,y = B @ (p - p0)
        if x < 0:
            out = p0
            dist = np.linalg.norm(p - p0)
        elif x > D:
            out = p1
            dist = np.linalg.norm(p - p1)
        else:
            out = p0 + x * b0
            dist = np.abs(y)
    return out, dist

def closest_test():
    import pylab as pl
    p0 = np.array([5, 5])
    p1 = np.array([10, 10])
    p2 = np.array([0, 5])
    p3 = np.array([5, 0])
    p4 = np.array([0, -5])
    p5 = np.array([10, 5])
    p6 = np.array([10, 15])
    pl.figure()
    pl.plot([p0[0], p1[0]] ,[p0[1], p1[1]], 'b-')
    for p in [p2, p3, p4, p5, p6]:
        a, d = closest_pt_on_segment(p0, p1, p)
        pl.plot([p[0], a[0]] ,[p[1], a[1]], '--')
    pl.axis('equal')
    pl.show()
#closest_test()

def snap_to_grid(v, step):
    return (v / step).astype(int) * step
    
ROLL = np.array([[1, 0, 0],
                 [0, 0, -1],
                 [0, 1, 0]])
PITCH = np.array([[0, 0, -1],
                  [0, 1, 0],
                  [1, 0, 0]])
YAW = np.array([[0, -1, 0],
                [1, 0, 0],
                [0, 0, 1]])

def get_roll(theta):
    return np.array([[1, 0, 0],
                     [0, cos(theta), -sin(theta)],
                     [0, sin(theta),  cos(theta)]])
def get_pitch(theta):
    return np.array([[cos(theta), 0, -sin(theta)],
                     [0, 1, 0],
                     [sin(theta), 0, cos(theta)]])
def get_yaw(theta):
    return np.array([[cos(theta), -sin(theta), 0],
                     [sin(theta), cos(theta), 0],
                     [0, 0, 1]])

def get_right_rotation(roll=0, pitch=0, yaw=0):
    '''
    Return rotation matrix for give angles given above in right angles.
    1 ==>  90 or -270 DEG
    2 ==> 180 or -180 DEG
    3 ==> 270 or  -90 DEG
    4 ==> 360 or    0 DEG

    It also works with fractional angles.
    '''
    return (get_roll(2 * pi * roll / 4) @
            get_pitch(2 * pi * pitch / 4) @
            get_yaw(2 * pi * yaw / 4))
    orient = np.eye(3)
    for i in range(roll % 4):
        orient = ROLL @ orient
    for i in range(pitch % 4):
        orient = PITCH @ orient
    for i in range(yaw % 4):
        orient = YAW @ orient
    return orient

class DummyKey:
    def __init__(self, *args, **kw):
        pass
    def pressed(self):
        return False
    def released(self):
        return not self.pressed()

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    

def unselect_all():
    from packages import things
    scene = things.TheScene
    for part in scene.selected.ungroup():
        part.render(scene.view, selected=False)
            
def select(part):
    from packages import things
    scene = things.TheScene
    scene.selected.append(part)
    part.render(scene.view, selected=True)
    
def zoom_fit_selected(ignored=None):
    from packages import things
    scene = things.TheScene
    #views = iv.Views([top, side, front, iso])
    views = scene.view
    top, side, front, iso = views

    verts = scene.selected.get_verts()
    if len(verts) > 0:
        window_dims = np.array([top.can.winfo_width(),
                                top.can.winfo_height(),
                                front.can.winfo_height()])
        
        wfxy = top.project_2d(verts)
        wfz = front.project_2d(verts)[:,1]
        wfxyz = np.column_stack([wfxy, wfz])
        
        d = np.max(wfxyz, axis=0) - np.min(wfxyz, axis=0)
        D = .75 * np.min(window_dims / d)
        views.set_scale(D * top.scale)
        
        m3 = (np.max(verts, axis=0) + np.min(verts, axis=0)) / 2
        c2_top = window_dims[:2] / 2
        c2_front = window_dims[1::2] / 2
        offset_new_top = c2_top - m3 @ top.B * top.scale
        offset_new_front = c2_front - m3 @ front.B * front.scale
        delta_xy = offset_new_top - top.offset
        delta_z = (offset_new_front - front.offset)[1]

        # print(offset_new_top, top.offset, delta_xy)
        views.slew(top.B @ delta_xy + front.B @ [0, delta_z])
def clear_all():
    from packages import things
    things.TheScene.selected.ungroup()
    things.TheScene.delete_all()
    things.TheScene.view.erase_all()
    things.TheScene.view.draw_axes()
    
################################################################################
## UNDO/REDO
history = []
history_i = [0] ### how long is history
max_undo = 15
def register_undo():
    from packages import things
    del history[history_i[0]:]

    unselected = things.Group()
    selected = things.TheScene.selected
    for thing in things.TheScene:
        if thing not in selected:
            unselected.append(thing.dup())
    history.append((unselected, selected.dup()))
    history_i[0] += 1
    if len(history) > max_undo:
        del history[:-(max_undo - len(history))]
        history_i[0] = max_undo
    # print('  do len(history)', len(history), history_i[0])
    
def undoable(doable):
    def out(*args, **kw):
        register_undo()
        doable(*args, **kw)
    return out


def restore(scn, sel):
    '''
    restore scn to scene and sel to scn.selected
    '''
    from packages import things
    clear_all()
    for thing in scn:
        things.TheScene.append(thing)
        thing.render(things.TheScene.view)
    for thing in sel:
        things.TheScene.append(thing)
        things.TheScene.selected.append(thing)
        thing.render(things.TheScene.view, selected=True)
    #print(len(sel), len(things.TheScene.selected))
        
def undo(*args, **kw):
    from packages import things

    #### save current state for redo if this is the latest
    if history_i[0] == len(history):
        history.append((things.TheScene.dup(), things.TheScene.selected.dup()))
        #history_i[0] += 1
    
    if history_i[0] > 0:
        history_i[0]-= 1
        prev_scene, prev_selected  = history[history_i[0]]
        restore(prev_scene, prev_selected)
        #print('undo len(history)', len(history), history_i[0])
    else:
        pass
        #print('no more undos')

def redo(*args, **kw):
    # print('redo len(history)', len(history), history_i[0])
    if history_i[0] < len(history)-1:
        history_i[0] += 1
        next_scene, next_selected  = history[history_i[0]]
        restore(next_scene, next_selected)
    else:
        pass
        # print("No more redos")

def reset_undo_history():
    del history[:]
    history_i[0] = 0
    # print('reset len(history)', len(history), history_i[0])

## UNDO/REDO
################################################################################
def cacheable(f):
    function_cache = {}
    def out(string):
        if string not in function_cache:
            function_cache[string] = f(string)
        return function_cache[string]
    return out

# @cacheable
# def junk(string):
#     return len(string)
# print(junk('justin'))
# print(junk('justin shaw'))
# print(junk('justin shaw'))
# print(junk('justin'))

def dedup(points):
    '''return induces of non-duplicates'''
    d = np.linalg.norm(points[:,np.newaxis] - points[np.newaxis], axis=-1)
    import pylab as pl
    dups = np.transpose(np.where(d < .1))
    dups = dups[dups[:,1] > dups[:,0],0]
    keep = [i for i in range(len(points)) if i not in dups]
    return keep

def curry(f, args, **kw):
    def out(ignore_event=None, *ignore_args, **ignore_kw):
        return f(*args, **kw)
    return out

def convexhull(points):
    '''
    return induces of convex hull
    '''
    points = points + np.random.uniform(-.0001, .0001, np.shape(points))
    nan_i = np.where(np.isnan(np.sum(points, axis=1)))[0]
    non_nan_i = np.logical_not(np.isnan(np.sum(points, axis=1)))
    midpoint = (np.max(points[non_nan_i], axis=0) + np.min(points[non_nan_i], axis=0)) / 2
    for i in nan_i:
        points[i] = midpoint

    unique_i = dedup(points)
    p = points[unique_i]
    n = len(p)
    start = np.argmin(p[:,1])
    xy = p - p[start]
    theta = np.arctan2(xy[:,1], xy[:,0])
    sorted = np.argsort(theta)
    hull = [p[sorted[0]]]
    out = [unique_i[sorted[0]]]
    
    idx = np.arange(3)
    def getv(p3):
        return np.linalg.det(np.diff(p3, axis=0))
    for i in range(n):
        p3 = p[sorted[(idx + i) % n]]
        v = getv(p3)
        if v > 0:
            hull.append(p3[1])
            out.append(unique_i[sorted[(idx[1] + i) % n]])
        if len(hull) > 2:
            remove = []
            for j in range(2, len(hull) + 1):
                if len(hull) == 3:
                    p3 = hull
                else:
                    p3 = [hull[- j - 1], hull[-j], hull[-1]]
                if getv(p3) < 0:
                    remove.append(j)
                else:
                    break
            for r in remove:
                del hull[-2]
                del out[-2]
    return np.array(hull), out


def convexhull_test():
    import pylab as pl
    import numpy as np
    p = np.random.normal(0, 1, (1000, 2))
    p = np.array([[ 107.45190528,  -20.71308365],
                  [ 117.45190528,  -30.64771895],
                  [ 134.77241336,  -24.91195459],
                  [ 124.77241336,  -14.97731929],
                  [ 107.45190528,  -20.71308365],
                  [ 107.45190528, -102.62828808],
                  [ 117.45190528, -112.56292338],
                  [ 117.45190528,  -30.64771895],
                  [ 117.45190528, -112.56292338],
                  [ 134.77241336, -106.82715902],
                  [ 134.77241336,  -24.91195459],
                  [ 134.77241336, -106.82715902],
                  [ 124.77241336,  -96.89252372],
                  [ 124.77241336,  -14.97731929],
                  [ 124.77241336,  -96.89252372],
                  [ 107.45190528, -102.62828808]])

    p = np.array([
        [0, 0],
        [0, .5],
        [0, 1],
        [1, 1],
        [1, 0],
        ]) #+ np.random.normal(0, 1e-4, (5, 2))
         
    h, i = convexhull(p)
    print(h)
    pl.plot(p[:,0], p[:,1], 'b.')
    pl.plot(h[:,0], h[:,1], 'b-')
    pl.show()
# convexhull_test()

def sameedge(e1, e2, tol):
    e1 = np.array(e1)
    e2 = np.array(e2)
    return np.linalg.norm(e1 - e2) < tol or np.linalg.norm(np.roll(e1, 1, axis=0) - e2) < tol
assert sameedge([[0, 0], [0, 1]],
               [[0, 0], [0, 1.1]], .2)
assert not sameedge([[0, 0], [0, 1]],
                   [[0, 0], [0, 1.1]], .05)
assert sameedge([[0, 0], [1, 1]],
               [[1, 1], [0, .1]], .2)

def edge3d(points, point):
    '''
    coarrse algorithm to determine if point is on the exterior of mesh given by edges
    '''
    points = np.vstack([point, points])
    hullxy, idxy = convexhull(points[:,[0, 1]])
    hullyz, idyz = convexhull(points[:,[1, 2]])
    hullzx, idzx = convexhull(points[:,[2, 0]])

    id3d = list(set(idxy).union(idyz, idzx))
    hull3d = points[id3d]
    
    print(hull3d)
    
    import pylab as pl
    fig, ax = pl.subplots(2, 2)
    ax[0,0].plot(points[:,0], points[:,1], 'b-')
    ax[0,0].plot(hull3d[:,0], hull3d[:,1], 'ro')

    ax[0,1].plot(points[:,1], points[:,2], 'b-')
    ax[0,1].plot(hull3d[:,1], hull3d[:,2], 'ro')

    ax[1,0].plot(points[:,2], points[:,0], 'b-')
    ax[1,0].plot(hull3d[:,2], hull3d[:,0], 'ro')
    
    pl.show()
    

def edge3d_test():
    ps = np.array([
        [0, 0, 0],
        [0, 0, 1],
        [0, 1, 1],
        [0, 1, 0],
        [0, 0, 1],
        [0, 0, 0],
        [1, 0, 0],
        [1, 0, 1],
        [1, 1, 1],
        [1, 1, 0],
        [1, 0, 0]])
    p = [0, .5, .5]
    edge3d(ps, p)
# edge3d_test()
