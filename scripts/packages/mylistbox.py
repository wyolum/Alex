#https://tk-tutorial.readthedocs.io/en/latest/listbox/listbox.html
import tkinter as tk

def listbox(parent, items, item_clicked, item_selected, n_row=40):

    def myclick(event=None):
        idx = lb.curselection()
        out = lb.get(idx)
        label['text'] = out
        item_clicked(idx[0], out)
    def myselect(event):
        myclick(event)
        idx = lb.curselection()
        out = lb.get(idx)
        item_selected(idx[0], out)
    frame = tk.Frame(parent)
    label = tk.Label(frame)
    label.grid(row=1, column=0)
    
    var = tk.StringVar(value=items)
    lb = tk.Listbox(frame, listvariable=var, selectmode='single', height=n_row)
    lb.grid(row=2, column=0)
    lb.bind('<<ListboxSelect>>', myclick)
    lb.bind('<Double-Button-1>', myselect)

    return frame


def click(*args):
    print('click', args)
def select(*args):
    print('select', args)
if __name__ == '__main__':
    root = tk.Tk()
    frame = listbox(root, dir(tk), click, select)
    frame.grid()

    root.mainloop()
