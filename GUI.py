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

class Canvas(tk.Tk):
    camera_delay=.2 # delay, in seconds, that the system should sit idle before each image 
    fracbelow=0.5 # this is the fraction of zrange below the expected plane of focus
    xmax,ymax,zmax=160.,118.,29.3 #translation limits in mm  
    disable_hard_limits=True  #this disables hard limits during RUN only
    samp=0  #samp is the sub-sample index (used when there is more than one sample at each position)
    gx,gy=0,0      #clicked coordinates on the canvas
    mx,my,mz=0,0,0 #machine position
    yrow,xcol=0,0  #sample position indices (starting at 0, not 1)
    pose_txt='A1'   
    corner='unset'
    viewing=False; running=False; stopit=False
    lighting1=False;lighting2=False

    """
    Parameters
    ----------
    config: Config class object of data read in from config file
    
    """
    def __init__(self, config, title="Canvas", geom="320x637+1597+30"):
        super(Canvas, self).__init__()
        self.title(title)
        self.geometry(geom)
        ##TODO: add left click and motion callback to root/self
        self.width = 320
        self.height = 637
        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()

        self._draw_window()
        self._draw_bounding_boxes()
        self._draw_labels()

        self._add_buttons()

    def _add_buttons(self):
        tlbutton = Button(self, button_text="TL", width=3, color="skyblue1", active_color="green", cbs={"<Button-1>": self.tl_left_b})
        self.canvas.create_window(10, 345, anchor=tk.NW, window=tlbutton)
    
    def _draw_window(self):
        self.canvas.create_rectangle(0,0,self.width,self.height, width=0, fill="white")

    def _draw_bounding_boxes(self):
        # draw xyz translation coordinate box
        self.canvas.create_rectangle(5,65,40,335, width=2, outline="darkblue",fill="lightgrey") #z setting
        self.canvas.create_rectangle(45,65,315,335, width=2, outline="darkblue",fill="lightgrey") #xy setting
        self.canvas.create_line(45, 200, 315, 200, width=2) #horizontal for xy
        self.canvas.create_line(180, 65, 180, 335, width=2)  #vertical for xy
        self.canvas.create_line(5, 200, 40, 200, width=2)   #horizontal for z
        self.canvas.create_line(15, 120, 30, 120,fill="red")   #z lines
        self.canvas.create_line(15, 160, 30, 160,fill="red")   #z lines
        self.canvas.create_line(15, 240, 30, 240,fill="red")   #z lines
        self.canvas.create_line(15, 280, 30, 280,fill="red")   #z lines
        self.canvas.create_oval(60, 80, 300, 320, outline="red") #outer circle
        self.canvas.create_oval(100, 120, 260, 280, outline = "red") #middle circle
        self.canvas.create_oval(140, 160, 220, 240, outline="red") #inner circle
        #draw calibration tool box
        self.canvas.create_rectangle(5,340,138,443,width=3,fill="lightgrey")
        #draw manual movement tool box
        self.canvas.create_rectangle(5,450,168,525,width=3,fill="lightgrey") 
        #draw automated imaging tool box
        self.canvas.create_rectangle(5,532,315,634,width=3,fill="lightgrey") 
        #TODO: not hardcoded babay

    def _draw_labels(self):
        self.canvas.create_text(295,190,fill="darkblue",font="Helvetia 12 bold",text="+X")
        self.canvas.create_text(60,190,fill="darkblue",font="Helvetia 12 bold",text="-X")
        self.canvas.create_text(197,75,fill="darkblue",font="Helvetia 12 bold",text="+Y")
        self.canvas.create_text(197,325,fill="darkblue",font="Helvetia 12 bold",text="-Y")
        self.canvas.create_text(20,80,fill="darkblue",font="Helvetia 12 bold",text="+Z")
        self.canvas.create_text(20,320,fill="darkblue",font="Helvetia 12 bold",text="-Z")

    # Button Callbacks
    @staticmethod
    def tl_left_b(event):
        corner='TL'
        xcol=0; yrow=0; samp=0
        mcoords() # move to TL
        canvas.create_rectangle(2,2,318,60,fill='white')
        canvas.create_text(160,20,text="SET now changes TL coordinates",font="Helvetia 9")
        if config.samps>1:
            canvas.create_text(160,40,text="After the corners Right Click TL for sub-samples",font="Helvetia 9")


def _default_cb(event):
    print('yay')

root = tk.Tk()
root.title("Test")
root.geometry("320x637+1597+30")

canvas = tk.Canvas(root, width=320, height=637)
canvas.pack()

our_canvas = Canvas("h")

cbs = {}
cbs["<Button-1>"] = _default_cb
testButton = Button(root, button_text="Test", cbs=cbs, is_bold=False, color="blue")

canvas.create_window(0, 0, anchor = tk.NW, window=testButton)
root.mainloop()

