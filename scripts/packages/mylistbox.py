#https://tk-tutorial.readthedocs.io/en/latest/listbox/listbox.html
import tkinter as tk

def listbox(parent, items, item_clicked, item_selected, n_row=40):

    def myclick(event=None):
        idx = lb.curselection()
        if idx:
            out = lb.get(idx)
            search.delete(0, tk.END)
            search.insert(0, out)
            item_clicked(out)
    def myselect(event):
        myclick(event)
        idx = lb.curselection()
        out = lb.get(idx)
        item_selected(out)
    def search_changed(*args):
        search_str = search_var.get()
        i = 0
        lb.delete(0, tk.END)
        for item in items:
            if search_str.lower() in item.lower():
                lb.insert(i, item)
                i += 1
        
    frame = tk.Frame(parent)
    search_var = tk.StringVar()
    #search_var.trace('w', search_changed)
    search = tk.Entry(frame, width=20, textvariable=search_var)
    search.grid(row=1, column=0)
    
    var = tk.StringVar(value=items)
    lb = tk.Listbox(frame, listvariable=var, selectmode='single', height=n_row)
    lb.grid(row=2, column=0)
    lb.bind('<<ListboxSelect>>', myclick)
    lb.bind('<Double-Button-1>', myselect)

    frame.get = lb.get
    frame.insert = lb.insert
    frame.delete = lb.delete
    frame.index = lb.index
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
