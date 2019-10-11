"""GUI
TODO: WHAT DOES THIS FILE DO?

Ramon Fernandes, Ella Bisbee
Version 0.0.1
"""

import tkinter as tk

class Button(tk.Button):
    """
    Parameters
    ----------
    root:         the parent element
    button_text:  text displayed on button
    is_bold:      TRUE if button_text should be bold
    width:        width of the button
    color:        color when not clicked
    active_color: color when clicked
    cbs:          dictionary with pairs (k, v) where k is a string representing an event
                  and v is the callback function for that event.
    """
    def __init__(self, root, button_text="", is_bold=False, width=3, color="gray",
                active_color="green", cbs={}):
        super(Button, self).__init__(root, 
                                     text=button_text, 
                                     font="Helvetica 12" if not is_bold else "Helvetica 12 bold")
        self.configure(width=width, background=color, activebackground=active_color)
        for k,v in cbs.items():
            self.bind(k, v)

class Canvas(tk.Canvas):
    """
    Parameters
    ----------
    
    """
    def __init__(self):
        print('canvas class')

def _default_cb(event):
    print('yay')

root = tk.Tk()
root.title("Test")
root.geometry("320x637+1597+30")

canvas = tk.Canvas(root, width=320, height=637)
canvas.pack()

cbs = {}
cbs["<Button-1>"] = _default_cb
testButton = Button(root, button_text="Test", cbs=cbs, is_bold=True)

canvas.create_window(0, 0, anchor = tk.NW, window=testButton)
root.mainloop()

