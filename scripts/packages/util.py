import numpy as np

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

def closest_pt_on_segment(p0, p1, p):
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

ROLL = np.array([[1, 0, 0],
                 [0, 0, -1],
                 [0, 1, 0]])
PITCH = np.array([[0, 0, -1],
                  [0, 1, 0],
                  [1, 0, 0]])
YAW = np.array([[0, -1, 0],
                [1, 0, 0],
                [0, 0, 1]])

def snap_to_grid(v, step):
    return (v / step).astype(int) * step
    
def get_integer_rotation(roll=0, pitch=0, yaw=0):
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
    print('  do len(history)', len(history), history_i[0])
    
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
    print(len(sel), len(things.TheScene.selected))
        
def undo(*args, **kw):
    from packages import things

    #### save current state for redo if this is the latest
    if history_i[0] == len(history):
        print('add current state to end for redo')
        history.append((things.TheScene.dup(), things.TheScene.selected.dup()))
        #history_i[0] += 1
    
    if history_i[0] > 0:
        history_i[0]-= 1
        prev_scene, prev_selected  = history[history_i[0]]
        restore(prev_scene, prev_selected)
        print('undo len(history)', len(history), history_i[0])
    else:
        print('no more undos')

def redo(*args, **kw):
    print('redo len(history)', len(history), history_i[0])
    if history_i[0] < len(history)-1:
        history_i[0] += 1
        next_scene, next_selected  = history[history_i[0]]
        restore(next_scene, next_selected)
    else:
        print("No more redos")

def reset_undo_history():
    del history[:]
    history_i[0] = 0
    print('reset len(history)', len(history), history_i[0])

## UNDO/REDO
################################################################################
def dedup(points):
    '''return induces of non-duplicates'''
    d = np.linalg.norm(points[:,np.newaxis] - points[np.newaxis], axis=-1)
    import pylab as pl
    dups = np.transpose(np.where(d < .1))
    dups = dups[dups[:,1] > dups[:,0],0]
    keep = [i for i in range(len(points)) if i not in dups]
    return keep
def convexhull(points):
    '''
    return induces of convex hull
    '''
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

    h, i = convexhull(p)
    print(h)
    pl.plot(p[:,0], p[:,1], 'b.')
    pl.plot(h[:,0], h[:,1], 'b-')
    pl.show()
#xconvexhull_test()
