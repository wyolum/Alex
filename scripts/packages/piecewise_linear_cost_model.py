import tkinter as tk
import numpy as np

import sys
if '.' not in sys.path:
    sys.path.append('.')
from packages.util import curry

bgcolor = 'white'

margin = 50
W = 400 + 2 * margin
H = 300 + 2 * margin

default_table = [['50',   '3.00'],
                 ['299',  '3'],
                 ['300',  '2.50'],
                 ['4000', '30'],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', ''],
                 ['', '']]
NROW = len(default_table)

def plot_coords(offset, scale, xy):
    '''
    convert data coords to plot pixel coords
    '''
    return xy * scale + offset

def get_table(len_vars, cost_vars):
    out = []
    for i in range(NROW):
        l = len_vars[i].get()
        c = cost_vars[i].get()
        if len(l) > 0 and len(c) > 0:
            try:
                l = int(np.round(float(l)))
                v = float(c)
                out.append([l, v])
            except:
                raise
    return np.array(out)

def plot(can, len_vars, cost_vars):
    table = get_table(len_vars, cost_vars)
    can.delete('all')

    if len(table) == 0:
        return
    l = table[:,0]
    c = table[:,1]
    mytable = table[np.logical_and(l > 0, c > 0)]
    mytable = mytable[np.argsort(mytable[:,0])]
    scale = np.array([W - 2 * margin, -(H - 2 * margin)]) / np.max(mytable, axis=0)
    offset = np.array([margin, H - margin])
    path = plot_coords(offset, scale, mytable)

    for pt in path:
        can.create_oval(pt[0] - 1, pt[1] - 1,
                        pt[0] + 1, pt[1] + 1, fill='red')
    can.create_line(*path.ravel(), fill='red')
    can.create_line(margin, H - margin, W - margin, H - margin, fill='black')
    can.create_line(margin, H - margin, margin, margin, fill='black')
    can.create_line(path[-1,0], H - margin + 4, path[-1, 0], H - margin-4, fill='black')
    can.create_line(margin - 4, path[-1, 1], margin + 4, path[-1, 1], fill='black')
    can.create_text(margin/2, H/2, text='Cost [USD]', angle=90)
    can.create_text(W/2, H-margin/2, text='mm')
    can.create_text(path[-1,0], H-margin/2, text=str(int(round(mytable[-1, 0]))))
    if mytable[-1, 1] > 1000:
        fontsize=12
        angle = 90
    elif mytable[-1, 1] > 100:
        fontsize=12
        angle = 0
    else:
        fontsize=14
        angle = 0
    max_cost_id = can.create_text(0, path[-1, 1], text='$' + str(int(round(mytable[-1, 1]))),
                                  font=('times', fontsize), angle=angle
                                  )
    coords = can.bbox(max_cost_id)
    xoffset = coords[0]
    can.move(max_cost_id, -xoffset + margin/3, 0)

        
def dollar(s):
    if len(s) > 0:
        v = float(s)
        out = f'{v:.2f}'
    else:
        out = ''
    return out

def cost_var(row):
    var = tk.StringVar()
    def onchange(*args):
        try:
            cost_str = var.get().strip()
            cost = float(cost_str)
            var.entry.config(bg=bgcolor)
        except ValueError:
            pass
            # var.entry.config(bg='red')
    var.trace('w', onchange)
    return var

def len_var(row):
    var = tk.StringVar()
    def onchange(*args):
        try:
            len_str = var.get().strip()
            len = float(len_str)
            var.entry.config(bg=bgcolor)
        except ValueError:
            pass
            # var.entry.config(bg='red')
    var.trace('w', onchange)
    return var

def check_cost(row, can, len_vars, cost_vars):
    c = cost_vars[row].get().strip()

    if len(c) > 0:
        try:
            cost_vars[row].set(dollar(c))
            cost_vars[row].entry.config(bg=bgcolor)
        except:
            #cost_vars[row].entry.config(bg="red")
            raise
        
    plot(can, len_vars, cost_vars)

def check_len(row, can, len_vars, cost_vars):
    l= len_vars[row].get().strip()
    if len(l) > 0:
        try:
            v = float(l)
            len_vars[row].set(int(np.round(v)))
            len_vars[row].entry.config(bg=bgcolor)
        except:
            len_vars[row].entry.config(bg="red")
    plot(can, len_vars, cost_vars)
    
def select_cost(row, can, len_vars, cost_vars):
    cost_vars[row].entry.selection_range(0, tk.END)
def select_len(row, can, len_vars, cost_vars):
    len_vars[row].entry.selection_range(0, tk.END)


def piecewise_linear_cost_model(parent):
    string_table = default_table[:]

    frame = tk.Frame(parent)
    tk.Label(frame, text="Piecewise Linear Cost").grid(row=9, column=1, columnspan=4)
    tk.Label(frame, text="Length [mm]").grid(row=10, column=1)
    tk.Label(frame, text="Price [USD]").grid(row=10, column=3)

    can = tk.Canvas(frame, width=W, height=H)
    can.grid(row=10, column=4, rowspan=20)

    len_vars = {}
    cost_vars = {}
    for i in range(NROW): #Rows
        #for j in range(ncol): #Columns
        args = (i, can, len_vars, cost_vars)
        l_var = len_var(i)
        c_var = cost_var(i)
        len_vars[i] = l_var
        cost_vars[i] = c_var
        
        l = tk.Entry(frame, width=10, justify="right", textvariable=l_var)
        c = tk.Entry(frame, width=10, textvariable=c_var)
        l.bind('<FocusIn>', curry(select_len, args))
        c.bind('<FocusIn>', curry(select_cost, args))
        l.bind('<FocusOut>', curry(check_len, args))
        c.bind('<FocusOut>', curry(check_cost, args))
        l_var.entry = l
        c_var.entry = c

        l.grid(row=i+11, column=1)
        tk.Label(frame, text="        $").grid(row=i+11, column=2, padx=0, sticky='N')
        c.grid(row=i+11, column=3)

        if len(string_table[i][0]) > 0:
            l.delete(0, tk.END)
            l.insert(0, int(np.round(float(string_table[i][0]))))
        if len(string_table[i][1]) > 0:
            c.delete(0, tk.END)
            c.insert(0, dollar(string_table[i][1]))
    plot(can, len_vars, cost_vars)
    return frame, can, len_vars, cost_vars

if __name__ == '__main__':
    frame, can, len_vars, cost_vars = piecewise_linear_cost_model(root)
    frame.grid()
    root.mainloop()
    print("Table:")
    print(get_table(len_vars, cost_vars))
        
