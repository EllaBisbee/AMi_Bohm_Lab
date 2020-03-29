import tkinter as tk
from tkinter import ttk
import sys, os
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
from shutil import copyfile

from Config import Config
from Microscope import Microscope

class MessageArea(tk.Frame):
    """
    A message area who's width is limited to the parent's
    """
    def __init__(self, parent, text):
        tk.Frame.__init__(self, parent, highlightbackground="black", 
                                     highlightthickness=1,
                                     background=parent['bg'])
        self.parent = parent
        self.text = tk.StringVar()
        self.text.set(text)
        self.label = ttk.Label(self, textvariable=self.text, background=parent['bg'])
        self.label.config(wraplength=self.parent.winfo_width())
        self.label.bind("<Configure>", self.onresize)
        self.label.pack()

    def onresize(self, event):
        self.label.config(wraplength=self.parent.winfo_width())

    def setText(self, t):
        self.text.set(t)

class TranslationTool(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, pady=1, highlightthickness=0, background=parent['bg'], *args, **kwargs)
        self.parent = parent

        background = "lightgrey"
        self.zsetting = tk.Canvas(self, width=1, height=1, highlightthickness=0, bg=background)
        self.zsetting.pack(side=tk.LEFT)

        self.xysetting = tk.Canvas(self, width=1, height=1, highlightthickness=0, bg=background)
        self.xysetting.pack(side=tk.RIGHT)

        self.bind("<Configure>", self.onResize)

    def onResize(self, event):
        self.draw()

    def draw(self):
        xywidth = self.parent.winfo_width() * 0.90 - 5
        xyheight = xywidth
        zwidth = self.parent.winfo_width() * 0.10
        zheight = xywidth
        guidespacing = 40 # spacing between lines and ovals
        linescuttoff = 10 # cutoff on either side (horizontal) of zsetting guide lines
        guidecolor = "red" # color of guides
        fontname = "Helvetia" # label font name
        fontsize = 12 # label font size
        fonteffect = "bold" # label font effect 
        labelfont = (fontname, fontsize, fonteffect)
        labelcolor = "darkblue"
        bordercolor = "darkblue"
        borderwidth = 2

        # Draw Z-Setting
        self.zsetting.delete("all")
        self.zsetting.config(width=zwidth, height=zheight)
        bordermargin = borderwidth - 1
        self.zsetting.create_rectangle(bordermargin,
                                       bordermargin,
                                       zwidth - bordermargin,
                                       zheight - bordermargin, 
                                       outline=bordercolor, 
                                       width=borderwidth) # z-setting outline
        self.zsetting.create_line(bordermargin,
                                  zheight/2 - borderwidth / 2, 
                                  zwidth - bordermargin, 
                                  zheight/2 - borderwidth / 2, 
                                  width=borderwidth) # z-setting center line
        for i in range(1, int(zheight/2/guidespacing) + 1): # z guide lines
            self.zsetting.create_line(linescuttoff, zheight/2 - i * guidespacing,
                                 zwidth - linescuttoff, zheight/2 - i * guidespacing,
                                 fill=guidecolor)
            self.zsetting.create_line(linescuttoff, zheight/2 + i * guidespacing,
                                 zwidth - linescuttoff, zheight/2 + i * guidespacing,
                                 fill=guidecolor)
        self.zsetting.create_text(zwidth/2,0,fill=labelcolor,font=labelfont,text="+Z",anchor=tk.N)
        self.zsetting.create_text(zwidth/2,zheight,fill=labelcolor,font=labelfont,text="-Z",anchor=tk.S)
    
        # Draw xy-setting
        self.xysetting.delete("all")
        self.xysetting.config(width=xywidth, height=xyheight)
        self.xysetting.create_rectangle(bordermargin,
                                        bordermargin,
                                        xywidth - bordermargin,
                                        xyheight - bordermargin, 
                                        outline=bordercolor, 
                                        width=borderwidth) # xy border
        self.xysetting.create_line(xywidth/2 - borderwidth / 2,
                                   bordermargin,
                                   xywidth/2 - borderwidth / 2,
                                   xyheight - bordermargin, 
                                   width=borderwidth) #xy vertical
        self.xysetting.create_line(bordermargin, 
                                   xyheight/2 - borderwidth/2, 
                                   xywidth - bordermargin, 
                                   xyheight/2 - borderwidth/2, 
                                   width=borderwidth) #xy horizontal
        for i in range(1, int(xywidth/2/guidespacing) + 1): #xy guide circles
            self.xysetting.create_oval(xywidth/2 - i * guidespacing, xyheight/2 - i * guidespacing,
                                  xywidth/2 + i * guidespacing, xyheight/2 + i * guidespacing,
                                  outline=guidecolor)
        self.xysetting.create_text(xywidth/2,0,fill=labelcolor,font=labelfont,text="+Y", anchor=tk.NW)
        self.xysetting.create_text(xywidth/2,xyheight, fill=labelcolor,font=labelfont, text="-Y", anchor=tk.SW)
        self.xysetting.create_text(borderwidth,xyheight/2, fill=labelcolor,font=labelfont, text="-X", anchor=tk.SW)
        self.xysetting.create_text(xywidth - borderwidth,xyheight/2, fill=labelcolor,font=labelfont, text="+X", anchor=tk.SE)

class CalibrationTool(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, highlightbackground="black", 
                          highlightthickness=3, background="lightgrey", 
                          *args, **kwargs)
        self.parent = parent.parent # parent only acts as a container. bypass to its parent
        self.configureRows(3)
        self.configureColumns(4)
        self.corner = None # track which corner to calibrate

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        btnwidth = 0
        style = ttk.Style()
        style.configure("Calibration.TButton", font="Helvetia 12", background="skyblue1")
        style.map("Calibration.TButton", background=[('active', 'green'), ('pressed', 'green')])
        # Top-left
        self.tlButton = ttk.Button(self, text="TL", style="Calibration.TButton", width=btnwidth)
        self.tlButton.bind("<Button-1>", self.tl_left_cb)
        self.tlButton.bind("<Button-3>", self.tl_right_cb)
        self.tlButton.grid(row=0, column=0, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Top-right
        self.trButton = ttk.Button(self, text="TR", style="Calibration.TButton", width=btnwidth)
        self.trButton.bind("<Button-1>", self.tr_cb)
        self.trButton.grid(row=0, column=2, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Bottom-left
        self.blButton = ttk.Button(self, text="BL", style="Calibration.TButton", width=btnwidth)
        self.blButton.bind("<Button-1>", self.bl_cb)
        self.blButton.grid(row=2, column=0, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Bottom-right
        self.brButton = ttk.Button(self, text="BR", style="Calibration.TButton", width=btnwidth)
        self.brButton.bind("<Button-1>", self.br_cb)
        self.brButton.grid(row=2, column=2, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # set button
        style.configure("Calibration-Set.TButton", font="Helvetia 12 bold", background="yellow")
        style.map("Calibration-Set.TButton", background=[('active', 'green'), ('pressed', 'green')])
        self.setButton = ttk.Button(self, text="SET", style="Calibration-Set.TButton", width=btnwidth)
        self.setButton.bind("<Button-1>", self.set_cb)
        self.setButton.grid(row=1, column=1, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

    def tl_left_cb(self, event):
        self.corner = "TL"
        self.parent.microscope.xcol = 0
        self.parent.microscope.yrow = 0
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        if self.parent.config.samps > 1:
            self.parent.messagearea.setText("SET now changes TL coordinates. After the corners Right Click TL for sub-samples")
        else:
            self.parent.messagearea.setText("SET now changes TL coordinates.")

    def tl_right_cb(self, event):
        config = self.parent.config
        for i in range(config.samps):
            #TODO: I don't think this look is necessary anymore since removing the update to config.samps within this function
            try:
                test = config.samp_coord[i]
            except:
                config.samp_coord = config.samp_coord.append([0., 0.])
        print('samp_coord', config.samp_coord)
        if config.samps > 1:
            self.parent.microscope.samp += 1
            if self.parent.microscope.samp == config.samps:
                self.parent.microscope.samp = 1
            self.corner = str(self.parent.microscope.samp)
            self.parent.microscope.xcol = 0
            self.parent.microscope.yrow = 0
            self.parent.microscope.mcoords()
            self.parent.messagearea.setText("SET now changes sub-sample " + 
                                            config.get_subsample_id(self.parent.microscope.samp) + 
                                            " coordinates.")
        else:
            self.parent.messagearea.setText("no sub-samples specified.")

    def tr_cb(self, event):
        self.corner = "TR"
        self.parent.microscope.xcol = self.parent.config.nx - 1
        self.parent.microscope.yrow = 0
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes TR coordinates.")
    
    def bl_cb(self, event):
        self.corner = "BL"
        self.parent.microscope.xcol = 0
        self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes BL coordinates.")

    def br_cb(self, event):
        self.corner = "BR"
        self.parent.microscope.xcol = self.parent.config.nx - 1
        self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes BR coordinates.")

    def set_cb(self, event):
        m = self.parent.microscope.get_machine_position()
        config = self.parent.config
        if not self.corner:
            self.parent.messagearea.setText("You must first select a corner")
        elif self.corner.isdigit():
            #TODO: figure out what this math is doing and maybe move to microscope?
            tmp_samp_coord = config.samp_coord
            tmp_samp_coord[(int(self.corner))][0] = (m[0]-config.tl[0])/(config.tr[0]-config.tl[0])
            tmp_samp_coord[(int(self.corner))][1] = (m[1]-config.tl[1])/(config.bl[1]-config.tl[1])
            self.parent.config.samp_coord = tmp_samp_coord
            print('new sample '+self.corner+' coordinates: '+str(config.samp_coord[(int(self.corner))]))
            self.parent.messagearea.setText(self.parent.config.get_subsample_id(int(corner))+" coordinates saved")
        else:
            if self.corner == "TL":
                self.parent.config.tl = m
            elif self.corner == "TR":
                self.parent.config.tr = m
            elif self.corner == "BL":
                self.parent.config.bl = m
            elif self.corner == "BR":
                self.parent.config.br = m
            print('new', self.corner, m)
            self.parent.messagearea.setText(self.corner + " coordinates saved")
        
        self.corner = None

    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

class HardwareControls(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, background=parent['bg'], *args, **kwargs)
        self.parent = parent.parent # parent only acts as a container. bypass to its parent
        self.configureRows(3)
        self.configureColumns(2)

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        style = ttk.Style()
        style.configure('LiveView.TButton', font="Helvetia 12 bold", foreground="black", background="orange")
        style.map('LiveView.TButton', background=[('active', 'green'), ('pressed', 'green')])
        self.viewButton = ttk.Button(self, text="VIEW", style="LiveView.TButton")
        self.viewButton.bind("<Button-1>", self.view_cb)
        self.viewButton.grid(columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.resetButton = ttk.Button(self, text="reset origin")
        self.resetButton.bind("<Button-1>", self.reset_cb)
        self.resetButton.bind("<Button-3>", self.reset_right_cb)
        self.resetButton.grid(row=1, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)
        
        self.closeButton = ttk.Button(self, text="stop/close")
        self.closeButton.bind("<Button-1>", self.close_cb)
        self.closeButton.grid(row=1, column=1, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light1Button = ttk.Button(self, text="light1")
        self.light1Button.bind("<Button-1>", self.light1_cb)
        self.light1Button.grid(row=2, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light2Button = ttk.Button(self, text="light2")
        self.light2Button.bind("<Button-1>", self.light2_cb)
        self.light2Button.grid(row=2, column=1, sticky=fillcell, pady=btnpad, padx=btnpad)

    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

    def view_cb(self, event):
        if not self.parent.microscope.running:
            self.parent.microscope.switch_camera_preview()
            self.parent.messagearea.setText("click VIEW to open/close live view")

    def reset_cb(self, event):
        self.parent.calibrationtool.corner = None
        print("clicked origin reset")
        self.parent.messagearea.setText("wait while machine resets...")
        self.parent.microscope.s.write(('$X \n').encode('utf-8')) # Send g-code home command to grbl
        self.parent.microscope.grbl_response() # Wait for grbl response with carriage return
        self.parent.microscope.s.write(('$H \n').encode('utf-8')) # Send g-code home command to grbl
        self.parent.microscope.grbl_response() # Wait for grbl response with carriage return
        self.parent.messagearea.setText("Ready to rumble!")

    def reset_right_cb(self, event):
        self.parent.calibrationtool.corner = None
        print("clicked reset alarm")
        self.parent.messagearea.setText("$X sent to GRBL...")
        self.parent.microscope.s.write(('$X \n').encode('utf-8')) # Send g-code home command to grbl
        self.parent.microscope.grbl_response() # Wait for grbl response with carriage return
        self.parent.messagearea.setText("It might work now...")

    """
    Closes the interface if not collecting images. Stops the run if you are collecting data.
    """
    def close_cb(self, event):
        if self.parent.microscope.running:
            print("stopping the run")
            self.parent.microscope.stopit = True
        else:
            print('moving back to the origin and closing the graphical user interface')
            self.parent.microscope.s.write(('$H \n').encode('utf-8')) # tell grbl to find zero 
            self.parent.microscope.grbl_response() # Wait for grbl response with carriage return
            self.parent.parent.quit()

    def light1_cb(self, event):
        self.parent.microscope.toggle_light1()

    def light2_cb(self, event):
        self.parent.microscope.toggle_light2_arduino()
            
class CalibrationAndHardware(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent
        self.configureRows(1)
        self.configureColumns(2)

        self.calibrationtool = CalibrationTool(self)
        self.hardwarecontrols = HardwareControls(self)

        fillhorizontal = tk.E + tk.W
        self.calibrationtool.grid(row=0, column=0, sticky=fillhorizontal, padx=3)
        self.hardwarecontrols.grid(row=0, column=1, sticky=fillhorizontal, padx=3)

    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

class MovementTool(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(highlightbackground="black",
                    highlightthickness=3,
                    background="lightgrey")
        self.parent = parent.parent # parent only acts as a container. bypass to its parent
        self.configureRows(2)
        self.configureColumns(2)

        fillcell = tk.N + tk.E + tk.S + tk.W
        pady=3
        padx=5
        width = 0
        style = ttk.Style()
        style.configure('Movement.TButton', background="cyan2")
        style.map('Movement.TButton', background=[('active', 'green'), ('pressed', 'green')])

        self.gotoButton = ttk.Button(self, text="go to", style="Movement.TButton", width=width)
        self.gotoButton.bind("<Button-1>", self.goto_cb)
        self.gotoButton.grid(row=0, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.pose = ttk.Entry(self, width=width)
        self.pose.insert(0, "A1")
        self.pose.grid(row=0, column=1, sticky=fillcell, pady=pady, padx=padx)

        self.prevButton = ttk.Button(self, text="prev", style="Movement.TButton", width=width)
        self.prevButton.bind("<Button-1>", self.prev_left_cb)
        self.prevButton.bind("<Button-3>", self.prev_right_cb)
        self.prevButton.grid(row=1, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.nextButton = ttk.Button(self, text="next", style="Movement.TButton", width=width)
        self.nextButton.bind("<Button-1>", self.next_left_cb)
        self.nextButton.bind("<Button-3>", self.next_right_cb)
        self.nextButton.grid(row=1, column=1, sticky=fillcell, pady=pady, padx=padx)
    
    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

    def goto_cb(self, event):
        ### config.samps = int(sampse.get()) TODO: remove
        self.corner = None
        pose_txt = str(self.pose.get())
        pose_txt = pose_txt.replace(" ", "") #get rid of spaces
        pose_txt = pose_txt.rstrip("\r\n") # get rid of carraige return
        self.parent.microscope.samp = 0
        major_well = pose_txt

        # first deal with the sub-sample character if present
        if not pose_txt[-1].isdigit(): # sub-sample is specified
            # TODO: add error checking for subsample within samps
            self.parent.microscope.samp = self.parent.config.get_subsample_index(pose_txt[-1])
            major_well = pose_txt[0:-1] # get major well letter id
        
        # now see if it is in number format
        if major_well[0].isdigit(): 
            numb = int(major_well) 
            numb -= 1
            if numb < self.parent.config.nx * self.parent.config.ny and numb >= 0:
                # TODO: add functions in config to calculate this stuff (row/col)
                self.parent.microscope.yrow = int(numb / self.parent.config.nx)
                self.parent.microscope.xcol = numb - (self.parent.microscope.yrow * self.parent.config.nx)
                print('yrow,xcol',self.parent.microscope.yrow, self.parent.microscope.xcol)
                self.parent.microscope.mcoords()
            else:
                self.parent.messagearea.setText("input error")
        else: # assume it is letter then number format
            rowletter = major_well[0]
            colnum = int(major_well[1:])
            if ((rowletter in self.parent.config.alphabet) and (colnum <= self.parent.config.nx)): 
                self.parent.microscope.yrow = self.parent.config.alphabet.index(rowletter) 
                # TODO: also add functions in config/micro to do this. When would it be necessary to recalculate yrow
                if self.parent.microscope.yrow > (self.parent.config.ny-1): 
                    self.parent.microscope.yrow = self.parent.microscope.yrow - self.parent.config.ny
                self.parent.microscope.xcol = colnum - 1
                self.parent.microscope.mcoords()
            else:
                self.parent.messagearea.setText("input error")

    def prev_left_cb(self, event):
        self.corner = None
        self.parent.messagearea.setText("")
        if self.parent.microscope.samp > 0:
            self.parent.microscope.samp -= 1
            self.parent.microscope.mcoords()
        elif self.parent.microscope.xcol > 0:
            self.parent.microscope.xcol -= 1
            self.parent.microscope.samp = self.parent.config.samps - 1
            self.parent.microscope.mcoords()
        elif self.parent.microscope.yrow > 0:
            self.parent.microscope.yrow -= 1
            self.parent.microscope.xcol = self.parent.config.nx - 1
            self.parent.microscope.samp = self.parent.config.samps-1
            self.parent.microscope.mcoords()
        else:
            self.parent.messagearea.setText("cannot reverse beyond the first sample")

    def prev_right_cb(self, event):
        # TODO: is there a reason this button doesn't reset corner to None?
        self.parent.messagearea.setText("")
        self.parent.microscope.yrow -= 1
        if self.parent.microscope.yrow == -1: 
            self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.mcoords()

    def next_left_cb(self, event):
        self.corner = None
        self.parent.messagearea.setText("")
        if self.parent.microscope.samp < (self.parent.config.samps - 1):
            self.parent.microscope.samp += 1
            self.parent.microscope.mcoords()
        elif self.parent.microscope.xcol < (self.parent.config.nx - 1):
            self.parent.microscope.xcol += 1
            self.parent.microscope.samp = 0
            self.parent.microscope.mcoords()
        elif self.parent.microscope.yrow < (self.parent.config.ny - 1):
            self.parent.microscope.yrow += 1
            self.parent.microscope.xcol = 0
            self.parent.microscope.samp = 0
            self.parent.microscope.mcoords()
        else:
            self.parent.messagearea.setText("cannot advance beyond the last sample")

    def next_right_cb(self, event):
        self.corner = None
        self.parent.messagearea.setText("")
        self.parent.microscope.yrow += 1
        if self.parent.microscope.yrow == self.parent.config.ny: 
            self.parent.microscope.yrow = 0
        self.parent.microscope.mcoords()

class ImagingControls(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent.parent # parent only acts as a container. bypass to its parent
        self.configureRows(2)
        self.configureColumns(1)

        fillcell = tk.N + tk.E + tk.S + tk.W
        style = ttk.Style()
        style.map('ActvGreen.TButton', background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Img-Snp.ActvGreen.TButton', font="Helvetia 12 bold", foreground="white", background="medium blue")
        style.configure('Img-Run.ActvGreen.TButton', font="Helvetia 12 bold", foreground="yellow", background="black")

        self.snapButton = ttk.Button(self, text="SNAP IMAGE", style="Img-Snp.ActvGreen.TButton")
        self.snapButton.bind("<Button-1>", self.snap_cb)
        self.snapButton.bind("<Button-3>", self.snap_right_cb)
        self.snapButton.grid(sticky=fillcell, pady=(0,5))

        self.runButton = ttk.Button(self, text="RUN", style="Img-Run.ActvGreen.TButton")
        self.runButton.bind("<Button-1>", self.run_cb)
        self.runButton.grid(sticky=fillcell, pady=(5,0))
    
    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

    """
    Get the current date as a nice string
    """
    def tdate(self):
        return datetime.now().strftime('%h-%d-%Y_%I:%M%p').replace(" ","")

    """
    Get the sample name
    """
    def _get_samp_name(self):
        yrow = self.parent.microscope.yrow
        xcol = self.parent.microscope.xcol
        samp_name = self.parent.config.get_sample_name(yrow, xcol)
        if self.parent.config.samps > 1:
            samp_name += self.parent.config.get_subsample_id(self.parent.microscope.samp)
        return samp_name

    """
    Ensure all directories and subdirectories exist for images
    Returns the innermost directory
    """
    def _initialize_directories(self, snap=True):
        sID = self.parent.config.sID
        nroot = self.parent.config.nroot
        path1 = 'images/' + sID
        if not os.path.isdir(path1):
            os.mkdir(path1)
            print('created directory {} within the images directory'.format(sID))
        path1 += '/' + nroot
        if not os.path.isdir(path1):
            os.mkdir(path1)
            print('created directory {} within the images/{} directory'.format(nroot, sID))
        
        if snap:
            path1 += '/snaps'
            if not os.path.isdir(path1):
                os.mkdir(path1)
                print('created directory \'snaps\' within the images/{}/{} directory'.format(sID, nroot))
        else:
            path1 += '/' + self.tdate()
            if not os.path.isdir(path1):
                os.mkdir(path1)
                print('created directory: {}'.format(path1))
        return path1

    """
    Takes a simple snapshot of the current view
    """
    def snap_cb(self, event):
        # config.sID = str(sIDe.get()) TODO: get rid of this, maybe add listeners for when entries in config are changed to update the config object??
        # config.nroot = str(IDe.get()) TODO: get rid of this
        path1 = self._initialize_directories()
        if self.parent.config.samps == 1: 
            # TODO: is there a better way to write this using functions in other modules?
            sname = 'images/' + self.parent.config.sID + '/' + self.parent.config.nroot + '/snaps/' + self.parent.config.alphabet[self.parent.microscope.yrow]+str(self.parent.microscope.xcol+1)+"_"+self.tdate()+'.jpg'
        else:
            sname = 'images/' + self.parent.config.sID + '/' + self.parent.config.nroot + '/snaps/' + self.parent.config.alphabet[self.parent.microscope.yrow]+str(self.parent.microscope.xcol+1)+self.parent.config.get_subsample_id(self.parent.microscope.samp)+"_"+self.tdate()+'.jpg'
        self.parent.microscope.camera.capture(sname)
        self.parent.messagearea.setText("image saved to {}".format(sname))

    """
    right mouse snap - takes a series of z-stacked pictures using nimages and Z-spacing parameters
    """
    def snap_right_cb(self, event):
        #config.sID = str(sIDe.get()) TODO: get rid of these
        #config.nroot = str(IDe.get())
        #config.nimages = int(nimge.get())
        #config.zstep = float(zspe.get())
        # TODO: move image taking to microscope?
        samp_name = self._get_samp_name()
        path1 = self._initialize_directories()
        processf = open(path1 + '/' + samp_name + '_process_snap.com','w')
        processf.write('rm OUT*.tif \n')
        zrange = (self.parent.config.nimages-1)*self.parent.config.zstep
        z = self.parent.microscope.mz-(1-self.parent.microscope.fracbelow)*zrange # bottom of the zrange (this is the top of the sample!)
        z_sav = self.parent.microscope.mz
        processf.write('echo \'processing: '+samp_name+'\' \n')
        samp_name += '_' + self.tdate()
        line = 'align_image_stack -m -a OUT '
        for imgnum in range(self.parent.config.nimages):
            self.parent.microscope.s.write(('G0 z '+ str(z) + '\n').encode('utf-8')) # move to z
            self.parent.microscope.grbl_response()
            self.parent.microscope.wait_for_Idle()
            imgname = path1 + '/' + samp_name + '_' + str(imgnum) + '.jpg'
            sleep(self.parent.microscope.camera_delay)#slow things down to allow camera to settle down
            self.parent.microscope.camera.capture(imgname)
            line += samp_name + '_' + str(imgnum) + '.jpg '
            z += self.parent.config.zstep
        line += (' \n') 
        processf.write(line)
        processf.write('enfuse --exposure-weight=0 --saturation-weight=0 --contrast-weight=1 --hard-mask --output='+samp_name+'.tif OUT*.tif \n')
        processf.write('rm OUT*.tif \n')
        processf.close()
        self.parent.microscope.s.write(('G0 z '+ str(z_sav) + '\n').encode('utf-8')) # return to original z 
        self.parent.microscope.grbl_response()
        self.parent.microscope.wait_for_Idle()
        self.parent.messagearea.setText("individual images:" + path1 + "\n" + 'source '+samp_name+'_process_snap.com to combine z-stack')
    
    def run_cb(self, event):
        self.parent.configurationtool.update_config() # get data from the GUI window and save/update the configuration file... 
        self.parent.microscope.yrow = 0
        self.parent.microscope.xcol = 0
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords() #go to A1 
        imgpath = self._initialize_directories(snap=False)
        if not os.path.isdir(imgpath+'/rawimages'):
            os.mkdir(imgpath+'/rawimages')
            print('created directory: '+imgpath+'/rawimages')
            copyfile(self.parent.config.fname,(imgpath + '/' + self.parent.config.fname))
        if not self.parent.microscope.viewing:
            self.parent.microscope.switch_camera_preview()
            sleep(2) # let camera adapt to the light before collecting images
        processf = open(imgpath+'/process'+self.parent.config.nroot+'.com','w')
        processf.write('rm OUT*.tif \n')
        zrange=(self.parent.config.nimages-1)*self.parent.config.zstep
        self.parent.microscope.running=True
        self.parent.messagearea.setText("imaging samples...")
        if self.parent.microscope.disable_hard_limits: 
            self.parent.microscope.s.write(('$21=0 \n').encode('utf-8')) #turn off hard limits
            print('hard limits disabled')
        for yrow in range(self.parent.config.ny):
            for xcol in range(self.parent.config.nx):
                for samp in range(self.parent.config.samps):
                    self.parent.microscope.mcoords() # go to the expected position of the focussed sample 
                    z = self.parent.microscope.mz-(1-self.parent.microscope.fracbelow)*zrange # bottom of the zrange (this is the top of the sample!)
                    samp_name = self._get_samp_name()
                    processf.write('echo \'processing: '+samp_name+'\' \n')
                    line='align_image_stack -m -a OUT '
                    # TODO: i think this is reused in snap function
                    for imgnum in range(self.parent.config.nimages):
                        self.parent.microscope.s.write(('G0 z '+ str(z) + '\n').encode('utf-8')) # move to z
                        self.parent.microscope.grbl_response()
                        self.parent.microscope.wait_for_Idle()
                        sleep(0.2)
                        # take image
                        imgname = imgpath+'/rawimages/'+samp_name+'_'+str(imgnum)+'.jpg'
                        sleep(self.parent.microscope.camera_delay)#slow things down to allow camera to settle down
                        self.parent.microscope.camera.capture(imgname)
                        line+='rawimages/'+samp_name+'_'+str(imgnum)+'.jpg '
                        z+=self.parent.config.zstep
                    line+=(' \n') 
                    processf.write(line)
                    processf.write('enfuse --exposure-weight=0 --saturation-weight=0 --contrast-weight=1 --hard-mask --output='+samp_name+'.tif OUT*.tif \n')
                    processf.write('rm OUT*.tif \n')
                    if self.parent.microscope.stopit: 
                        break
                if self.parent.microscope.stopit: 
                    break
            if self.parent.microscope.stopit: 
                break
        self.parent.microscope.running = False
        processf.close()
        self.parent.microscope.switch_camera_preview() # turn off the preview so the monitor can go black when the pi sleeps
        self.parent.microscope.toggle_light1() #turn off light1
        self.parent.microscope.toggle_light2_arduino() #turn off light2
        if self.parent.microscope.disable_hard_limits: 
           self.parent.microscope.s.write(('$21=1 \n').encode('utf-8')) # turn hard limits back on
           print('hard limits enabled')
        self.parent.microscope.stopit = False

class MovementAndImaging(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent
        self.configureRows(1)
        self.configureColumns(2)

        self.movementtool = MovementTool(self)
        self.imagingcontrols = ImagingControls(self)

        fillhorizontal = tk.E + tk.W
        self.movementtool.grid(row=0, column=0, sticky=fillhorizontal, padx=3)
        self.imagingcontrols.grid(row=0, column=1, sticky=fillhorizontal, padx=3)
    
    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

class ConfigurationTool(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(highlightbackground="black",
                    highlightthickness=3,
                    background="lightgrey")
        self.parent = parent
        self.configureRows(4)
        self.configureColumns(10)
        
        fillcell = tk.N + tk.E + tk.S + tk.W
        style = ttk.Style()
        style.configure('Config.TButton', font="Helvetia 10", width=8, background="yellow")
        style.map('Config.TButton', background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Config.TLabel', background=self['bg'], font="Helvetia 10")

        self.filee = ttk.Entry(self, width=1)
        self.filee.grid(row=0, column=0, columnspan=3, pady=2, padx=(2,0), sticky=fillcell)

        ttk.Label(self, text='Sample ID:', style="Config.TLabel", anchor=tk.E).grid(row=0, column=3, columnspan=2, sticky=fillcell,pady=2)
        self.sIDe = ttk.Entry(self, width=1)
        self.sIDe.grid(row=0, column=5, columnspan=5, pady=2, sticky=fillcell)

        ttk.Label(self, text='Plate ID:', style="Config.TLabel", anchor=tk.E).grid(row=1, column=0, columnspan=2, sticky=fillcell, pady=2)
        self.pIDe = ttk.Entry(self, width=1)
        self.pIDe.grid(row=1, column=2, columnspan=3, pady=2, sticky=fillcell)

        ttk.Label(self, text='samples/pos:', style="Config.TLabel", anchor=tk.E).grid(row=1, column=5, columnspan=4, sticky=fillcell, pady=2)
        self.sampse = ttk.Entry(self, width=1)
        self.sampse.grid(row=1, column=9, sticky=fillcell, pady=2)

        ttk.Label(self, text='nx:', style="Config.TLabel", anchor=tk.E).grid(row=2, column=0, sticky=fillcell, pady=2)
        self.nxe = ttk.Entry(self, width=1)
        self.nxe.grid(row=2, column=1, sticky=fillcell, pady=2)

        ttk.Label(self, text='ny:', style="Config.TLabel", anchor=tk.E).grid(row=2, column=2, sticky=fillcell, pady=2)
        self.nye = ttk.Entry(self, width=1)
        self.nye.grid(row=2, column=3, sticky=fillcell, pady=2)

        ttk.Label(self, text='n_img:', style="Config.TLabel", anchor=tk.E).grid(row=2, column=4, sticky=fillcell, pady=2)
        self.nimge = ttk.Entry(self, width=1)
        self.nimge.grid(row=2, column=5, sticky=fillcell, pady=2)

        ttk.Label(self, text='Z-spacing:', style="Config.TLabel", anchor=tk.E).grid(row=2, column=6, columnspan=2, sticky=fillcell, pady=2)
        self.zspe = ttk.Entry(self, width=1)
        self.zspe.grid(row=2, column=8, columnspan=2, sticky=fillcell, pady=2)

        self.updateButton = ttk.Button(self, text="write/update", style="Config.TButton")
        self.updateButton.bind("<Button-1>", self.updatebtn_cb)
        self.updateButton.grid(row=3, column=0, columnspan=5, sticky=fillcell, padx=2, pady=2)

        self.readButton = ttk.Button(self, text="read file", style="Config.TButton")
        self.readButton.bind("<Button-1>", self.readbtn_cb)
        self.readButton.grid(row=3, column=5, columnspan=5, sticky=fillcell, padx=2, pady=2)

        if self.parent.config:
            self.update_entry_fields()

    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

    def updatebtn_cb(self, event):
        self.update_config()

    """
    Callback function for update buttom
    """
    def update_config(self):
        if not self.parent.config:
            self.messagearea.setText("There is not existing configuration to update. Nothing written")
            return
        
        tmp_fname = str(self.filee.get())
        if " " in tmp_fname:
            self.parent.messagearea.setText("file name cannot contain spaces. Nothing written.")
            self.filee.delete(0,END)
            self.filee.insert(0,"")
            self.update()
        else:
            self.parent.config.fname = tmp_fname
            self.parent.config.nx = int(self.nxe.get())
            self.parent.config.ny = int(self.nye.get())
            self.parent.config.samps = int(self.sampse.get())
            self.parent.config.nimages = int(self.nimge.get())
            self.parent.config.zstep = float(self.zspe.get())
            self.parent.config.sID = str(self.sIDe.get())
            self.parent.config.nroot = str(self.pIDe.get())

            self.parent.config.write()
            self.parent.messagearea.setText("parameters saved to " + tmp_fname)

    """
    Callback function for read button
    """
    def readbtn_cb(self, event):
        fname = str(self.filee.get())
        self.parent.read_config(fname=fname)
        self.update_entry_fields()
        print('Parameters read from ' + fname)
        self.update()
    """
    Updates the entry fields to match those in the Config module
    """
    def update_entry_fields(self):
        # Clear fields
        self.filee.delete(0, tk.END)
        self.sIDe.delete(0, tk.END)
        self.pIDe.delete(0, tk.END)
        self.nxe.delete(0, tk.END)
        self.nye.delete(0, tk.END)
        self.sampse.delete(0, tk.END)
        self.nimge.delete(0, tk.END)
        self.zspe.delete(0, tk.END)

        # update
        config = self.parent.config
        self.filee.insert(0, config.fname)
        self.sIDe.insert(0, config.sID)
        self.pIDe.insert(0, config.nroot)
        self.nxe.insert(0, config.nx)
        self.nye.insert(0, config.ny)
        self.sampse.insert(0, config.samps)
        self.nimge.insert(0, config.nimages)
        self.zspe.insert(0, config.zstep)

class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configureRows(5)
        self.configureColumns(1)
        self.parent = parent

        # Set up initial configuration
        self.config = None
        self.read_config()
        self.microscope = Microscope()
        
        # Create GUI Areas
        self.messagearea = MessageArea(self, text="Welcome AMi!")
        self.translationtool = TranslationTool(self)
        self.calibrationandhardware = CalibrationAndHardware(self)
        self.calibrationtool = self.calibrationandhardware.calibrationtool
        self.hardwarecontrols = self.calibrationandhardware.hardwarecontrols
        self.movementandimaging = MovementAndImaging(self)
        self.movementtool = self.movementandimaging.movementtool
        self.imagingcontrols = self.movementandimaging.imagingcontrols
        self.configurationtool = ConfigurationTool(self)

        # Add GUI Areas to Frame
        fillHorizontal = tk.E + tk.W
        separationpad = 3
        self.messagearea.grid(sticky=fillHorizontal)
        self.translationtool.grid(sticky=fillHorizontal, pady=(separationpad,0))
        self.calibrationandhardware.grid(sticky=fillHorizontal, pady=(separationpad,0))
        self.movementandimaging.grid(sticky=fillHorizontal, pady=(separationpad,0))
        self.configurationtool.grid(sticky=fillHorizontal, pady=(separationpad,1), padx=3)

    """
    Configures rows to resize appropriately when using Grid Manager
    """
    def configureRows(self, numrows):
        for i in range(numrows):
            tk.Grid.rowconfigure(self, i, weight=1)

    """
    Configures columns to resize appropriately when using Grid Manager
    """
    def configureColumns(self, numcols):
        for i in range(numcols):
            tk.Grid.columnconfigure(self, i, weight=1)

    """
    read information from the configuration file
    """
    def read_config(self, fname='AMi.config'): 
        try:
            self.config = Config(fname)
        except ValueError:
            print("Configuration file does not exist")
        except:
            Config.print_help()
            if fname=='AMi.config': sys.exit() #TODO: what does this do?

def main():
    print('\n Bonjour, ami \n')
    if not os.path.isdir("images"): # check to be sure images directory exists
        print('"images" directory (or symbolic link) not found. \n' +
             'This should be in the same directory as this program. \n' +
             'You need to create the directory or fix the link before continuing. \n' +
             'i.e. mkdir images')
        sys.exit()

    # load environment variables
    load_dotenv()

    # Set up GUI Window
    windowwidth = 320
    windowheight = 0
    root = tk.Tk()
    root.title('AMiGUI v1.0')
    root.minsize(windowwidth, windowheight)
    root.resizable(False, False)
    root.update()

    # for selfresizing: https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
    frame = GUI(root, background="white")
    frame.pack(side="top", fill="both", expand=True)
    frame.messagearea.setText("The corner samples must be centered and in focus before imaging. Use blue buttons to check alignment, and XYZ windows to make corrections. Good luck!!")
    root.mainloop()

    # Exit procedures
    print('\n Hope you find what you\'re looking for!  \n')

if __name__ == "__main__":
    main()