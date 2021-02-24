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
    
################################################################################
## UNDO/REDO
history = []
history_i = [0]
def register_goback():
    from packages import things
    del history[history_i[0]:]

    unselected = things.Group()
    selected = things.TheScene.selected
    for thing in things.TheScene:
        if thing not in selected:
            unselected.append(thing.dup())
    history.append((unselected, selected.dup()))
    history_i[0] += 1
    print('  do len(history)', len(history), history_i[0], len(unselected), len(selected))
    
def undoable(doable):
    def out(*args, **kw):
        register_goback()
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
        thing.render(things.TheScene.view, selected=True)
        
def undo(*args, **kw):
    from packages import things
    print('  undo len(history)', len(history), history_i[0], history_i[0] == len(history))

    #### save current state for redo if this is the latest
    if history_i[0] == len(history):
        print('add current state to end for redo')
        history.append((things.TheScene.dup(), things.TheScene.selected.dup()))
        #history_i[0] += 1
    
    if history_i[0] > 0:
        history_i[0]-= 1
        prev_scene, prev_selected  = history[history_i[0]]
        restore(prev_scene, prev_selected)
        print('  undo len(history)', len(history), history_i[0])
    else:
        print(' no more undos')

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
