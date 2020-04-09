"""The main Graphical User Interface for AMi

This file contains all of the modules and classes needed to create the
GUI.
"""

# TODO: make callbacks private?

import tkinter as tk
from tkinter import ttk
import sys, os
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
from shutil import copyfile
import numpy as np

from Config import Config
from Microscope import Microscope

class MessageArea(tk.Frame):
    """An area for displaying text to the user.

    A dynamic area for displaying text. This area's width is limited
    by its parent's width and will wrap text to keep the area from
    expanding width.

    Attributes:
        parent: The parent TK widget
    """
    def __init__(self, parent, text):
        """Initializes the message area.
        """
        tk.Frame.__init__(self, parent, highlightbackground="black", 
                                        highlightthickness=1,
                                        background=parent['bg'])
        self.parent = parent
        self._text = tk.StringVar() 
        self._text.set(text)
        self._label = ttk.Label(self, textvariable=self._text, 
                                background=parent['bg']) 
        self._label.config(wraplength=self.parent.winfo_width())
        self._label.bind("<Configure>", self._onresize)
        self._label.pack()

    def _onresize(self, event):
        """Callback for when the internal label is resized.

        Args:
            event: information from the event that triggered a call
        """
        self._label.config(wraplength=self.parent.winfo_width())

    def setText(self, t):
        """Changes the text displayed.

        TODO: change setText to set_text to match naming convention

        Args:
            t: String containing the new text
        """
        self._text.set(t)

class TranslationTool(tk.Frame):
    """A tool used to move the CNC tray.

    Attributes:
        parent: The parent TK widget
        zsetting: the canvas for controlling the z location
        xysetting: the canvas for controlling the xy location
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, pady=1, highlightthickness=0, 
                          background=parent['bg'], *args, **kwargs)
        self.parent = parent
        self._gx = 0
        self._gy = 0

        background = "lightgrey"
        self.zsetting = tk.Canvas(self, width=1, height=1, 
                                  highlightthickness=0, bg=background)
        self.zsetting.bind("<Motion>", self.motion)
        self.zsetting.bind("<Button-1>", self.left_click_z)
        self.zsetting.pack(side=tk.LEFT)

        self.xysetting = tk.Canvas(self, width=1, height=1, 
                                   highlightthickness=0, bg=background)
        self.xysetting.bind("<Motion>", self.motion)
        self.xysetting.bind("<Button-1>", self.left_click_xy)
        self.xysetting.pack(side=tk.RIGHT)

        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Callback function for when this widget's window is resized.

        Args:
            event: information on the event that triggered this
        """
        self.draw()

    def draw(self):
        """Draws the canvas.
        """
        xywidth = self.parent.winfo_width() * 0.90 - 5
        xyheight = xywidth
        zwidth = self.parent.winfo_width() * 0.10
        zheight = xywidth
        guidespacing = 40 # spacing between lines and ovals
        linescuttoff = 10 # cutoff on either side (horizontal) of zsetting 
                          # guide lines
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
        self.zsetting.create_rectangle(bordermargin, bordermargin, 
                                       zwidth - bordermargin,
                                       zheight - bordermargin, 
                                       outline=bordercolor, 
                                       width=borderwidth) # z-setting outline
        self.zsetting.create_line(bordermargin, zheight/2 - borderwidth/2, 
                                  zwidth - bordermargin, 
                                  zheight/2 - borderwidth/2, 
                                  width=borderwidth) # z-setting center line
        for i in range(1, int(zheight/2/guidespacing) + 1): # z guide lines
            self.zsetting.create_line(linescuttoff, 
                                      zheight/2 - i * guidespacing,
                                      zwidth - linescuttoff, 
                                      zheight/2 - i * guidespacing,
                                      fill=guidecolor)
            self.zsetting.create_line(linescuttoff, 
                                      zheight/2 + i * guidespacing,
                                      zwidth - linescuttoff, 
                                      zheight/2 + i * guidespacing,
                                      fill=guidecolor)
        self.zsetting.create_text(zwidth/2, 0, fill=labelcolor, font=labelfont,
                                  text="+Z", anchor=tk.N)
        self.zsetting.create_text(zwidth/2, zheight, fill=labelcolor,
                                  font=labelfont, text="-Z", anchor=tk.S)
    
        # Draw xy-setting
        self.xysetting.delete("all")
        self.xysetting.config(width=xywidth, height=xyheight)
        self.xysetting.create_rectangle(bordermargin, bordermargin,
                                        xywidth - bordermargin,
                                        xyheight - bordermargin, 
                                        outline=bordercolor, 
                                        width=borderwidth) # xy border
        self.xysetting.create_line(xywidth/2 - borderwidth/2, bordermargin,
                                   xywidth/2 - borderwidth/2,
                                   xyheight - bordermargin, 
                                   width=borderwidth) #xy vertical
        self.xysetting.create_line(bordermargin, 
                                   xyheight/2 - borderwidth/2, 
                                   xywidth - bordermargin, 
                                   xyheight/2 - borderwidth/2, 
                                   width=borderwidth) #xy horizontal
        for i in range(1, int(xywidth/2/guidespacing) + 1): #xy guide circles
            self.xysetting.create_oval(xywidth/2 - i * guidespacing, 
                                       xyheight/2 - i * guidespacing,
                                       xywidth/2 + i * guidespacing, 
                                       xyheight/2 + i * guidespacing,
                                       outline=guidecolor)
        self.xysetting.create_text(xywidth/2, 0, fill=labelcolor, 
                                   font=labelfont, text="+Y", anchor=tk.NW)
        self.xysetting.create_text(xywidth/2, xyheight, fill=labelcolor, 
                                   font=labelfont, text="-Y", anchor=tk.SW)
        self.xysetting.create_text(borderwidth, xyheight/2, fill=labelcolor,
                                   font=labelfont, text="-X", anchor=tk.SW)
        self.xysetting.create_text(xywidth - borderwidth, xyheight/2, 
                                   fill=labelcolor,font=labelfont, text="+X", 
                                   anchor=tk.SE)
    
    def motion(self, event):
        """Callback that records the last clicked area within the tool.

        Args:
            event: information for the event that triggered this
        """
        self._gx, self._gy = event.x, event.y

    def left_click_z(self, event):
        """Callback that triggers a z-move for the machine

        Args:
            event: information for the event that triggered this
        """
        print('left_click gx,gy,xcol,yrow',self._gx, self._gy, 
              self.parent.microscope.xcol, self.parent.microscope.yrow)
        midpoint = self.zsetting.winfo_height() / 2
        rz = midpoint - self._gy
        mzsav = self.parent.microscope.mz
        self.parent.microscope.mz += 0.0001 * (abs(rz)**2.2) * np.sign(rz)
        if (self.parent.microscope.mz > 0. and 
           self.parent.microscope.mz < self.parent.microscope.zmax):
            self.parent.microscope.grbl.rapid_move(z=self.parent.microscope.mz)
            message = ('current Z: '+str(round(self.parent.microscope.mz,3))+
                      ' change: '+
                      str(round((self.parent.microscope.mz-mzsav),3)))
            if self.parent.calibrationtool.corner:
                self.parent.messagearea.setText(message)
            else:
                self.parent.messagearea.setText("")
            print(message)
        else:
            self.parent.messagearea.setText(
                "that move would take you out of bounds")
            self.parent.microscope.mz = mzsav

    def left_click_xy(self, event):
        """Callback that triggers a xy-move for the machine

        Args:
            event: information for the event that triggered this
        """
        print('left_click gx,gy,xcol,yrow',self._gx, self._gy, 
              self.parent.microscope.xcol, self.parent.microscope.yrow)
        x_mid = self.xysetting.winfo_width() / 2
        y_mid = self.xysetting.winfo_height() / 2
        rx = self._gx - x_mid
        ry = y_mid - self._gy
        mxsav = self.parent.microscope.mx
        mysav = self.parent.microscope.my
        self.parent.microscope.mx += 0.0001*(abs(rx)**2.2)*np.sign(rx)
        self.parent.microscope.my += 0.0001*(abs(ry)**2.2)*np.sign(ry)
        if (self.parent.microscope.mx>0. and self.parent.microscope.my>0. and 
           self.parent.microscope.mx < self.parent.microscope.xmax and 
           self.parent.microscope.my < self.parent.microscope.ymax):
            self.parent.microscope.grbl.rapid_move(
                x=self.parent.microscope.mx,
                y=self.parent.microscope.my)
            if self.parent.calibrationtool.corner:
                self.parent.messagearea.setText(
                    'current X,Y: {}, {}'.format(
                        str(round(self.parent.microscope.mx,3)), 
                        str(round((self.parent.microscope.my),3))))
            else:
                self.parent.messagearea.setText('')
            print('current X: {} change: {}'.format(
                str(round(self.parent.microscope.mx,3)),
                str(round((self.parent.microscope.mx-mxsav),3))))
            print('current Y: {} change: {}'.format(
                str(round(self.parent.microscope.my,3)),
                str(round((self.parent.microscope.my-mysav),3))))
        else:
            self.parent.messagearea.setText(
                "that move would take you out of bounds")
            self.parent.microscope.mx = mxsav
            self.parent.microscope.my = mysav

class CalibrationTool(tk.Frame):
    """A tool used to calibrate the internal configuration

    Attributes:
        parent: actual parent is a container so this is the container's parent
        corner: the corner currently calibrating
        tlButton: the button to select the top left corner
        trButton: the button to select the top right corner
        blButton: the button to select the bottom left corner
        brButton: the button to select the bottom right corner
        setButton: the button to store the calibration
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, highlightbackground="black", 
                          highlightthickness=3, background="lightgrey", 
                          *args, **kwargs)
        self.parent = parent.parent
        self.corner = None
        GUI.configure_rows(self, 3)
        GUI.configure_columns(self, 4)

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
        """Callback for the top left button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
        """Callback for the top left button right click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        config = self.parent.config
        for i in range(config.samps):
            #TODO: I don't think this look is necessary anymore since removing the update to config.samps within this function
            try:
                _ = config.samp_coord[i]
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
        """Callback for the top right button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "TR"
        self.parent.microscope.xcol = self.parent.config.nx - 1
        self.parent.microscope.yrow = 0
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes TR coordinates.")
    
    def bl_cb(self, event):
        """Callback for the bottom left button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "BL"
        self.parent.microscope.xcol = 0
        self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes BL coordinates.")

    def br_cb(self, event):
        """Callback for the bottom right button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "BR"
        self.parent.microscope.xcol = self.parent.config.nx - 1
        self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.samp = 0
        self.parent.microscope.mcoords()
        self.parent.messagearea.setText("SET now changes BR coordinates.")

    def set_cb(self, event):
        """Callback for the set button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
            self.parent.messagearea.setText(self.parent.config.get_subsample_id(int(self.corner))+" coordinates saved")
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

class HardwareControls(tk.Frame):
    """Additional controls for the external hardware

    Buttons to control the additional hardware. This include the lights
    and the camera. Also includes control to reset the origin and to
    close the program.

    Attributes:
        parent: actual parent is a container so this is the container's parent
        viewButton: Controls the live preview of the camera
        resetButton: Resets the origin
        closeButton: Stops a run or closes the program
        light1Button: Light switch for white light
        light2Button: Light switch for color light
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, background=parent['bg'], *args, **kwargs)
        self.parent = parent.parent
        GUI.configure_rows(self, 3)
        GUI.configure_columns(self, 2)

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        style = ttk.Style()
        # TODO: create active green button style in "Controller" to inherit from
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

    def view_cb(self, event):
        """Toggles live preview

        Args:
            event: information on the event that triggered this
        """
        if not self.parent.microscope.running:
            self.parent.microscope.switch_camera_preview()
            self.parent.messagearea.setText("click VIEW to open/close live view")

    def reset_cb(self, event):
        """Resets CNC machine to home

        Args:
            event: information on the event that triggered this
        """
        self.parent.calibrationtool.corner = None
        print("clicked origin reset")
        self.parent.messagearea.setText("wait while machine resets...")
        self.parent.microscope.grbl.kill_alarm_lock()
        self.parent.microscope.grbl.run_homing_cycle() # Send g-code home command to grbl
        self.parent.messagearea.setText("Ready to rumble!")

    def reset_right_cb(self, event):
        """Resets CNC machine to home due to critical error (alarm)
        Args:
            event: information on the event that triggered this
        """
        self.parent.calibrationtool.corner = None
        print("clicked reset alarm")
        self.parent.messagearea.setText("$X sent to GRBL...")
        self.parent.microscope.grbl.kill_alarm_lock()
        self.parent.messagearea.setText("It might work now...")

    def close_cb(self, event):
        """Closes the interface if not collecting images. Stops otherwise.

        Args:
            event: information on the event that triggered this
        """
        if self.parent.microscope.running:
            print("stopping the run")
            self.parent.microscope.stopit = True
        else:
            self.parent.close()

    def light1_cb(self, event):
        """Toggles light1

        Args:
            event: information on the event that triggered this
        """
        self.parent.microscope.toggle_light1()

    def light2_cb(self, event):
        """Toggles light2

        Args:
            event: information on the event that triggered this
        """
        self.parent.microscope.toggle_light2_arduino()
            
class CalibrationAndHardware(tk.Frame):
    """Container for Calibration and Hardware

    Attributes:
        parent: The parent TK widget
        calibrationtool: Widget containing calibration tools
        hardwarecontrols: Widget containing hardware tools
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent
        GUI.configure_rows(self, 1)
        GUI.configure_columns(self, 2)

        self.calibrationtool = CalibrationTool(self)
        self.hardwarecontrols = HardwareControls(self)

        fillhorizontal = tk.E + tk.W
        self.calibrationtool.grid(row=0, column=0, sticky=fillhorizontal, padx=3)
        self.hardwarecontrols.grid(row=0, column=1, sticky=fillhorizontal, padx=3)

class MovementTool(tk.Frame):
    """Tool to navigate between drops

    Attributes:
        parent: actual parent is a container so this is the container's parent
        pose: Entry box for the desired sample
        gotoButton: Navigates to sample specified in pose above
        prevButton: Navigates to the previous sample
        nextButton: Navigates to the next sample
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(highlightbackground="black",
                    highlightthickness=3,
                    background="lightgrey")
        self.parent = parent.parent
        GUI.configure_rows(self, 2)
        GUI.configure_columns(self, 2)

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
    
    def goto_cb(self, event):
        """Navigates to the well specified in pose

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
        """Navigates to the sample before the current one

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
        """Navigates to the previous row, keeping column and subsample

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        # TODO: is there a reason this button doesn't reset corner to None?
        self.parent.messagearea.setText("")
        self.parent.microscope.yrow -= 1
        if self.parent.microscope.yrow == -1: 
            self.parent.microscope.yrow = self.parent.config.ny - 1
        self.parent.microscope.mcoords()

    def next_left_cb(self, event):
        """Navigates to the sample following the current one

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
        """Navigates to the following row, keeping column and subsample

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = None
        self.parent.messagearea.setText("")
        self.parent.microscope.yrow += 1
        if self.parent.microscope.yrow == self.parent.config.ny: 
            self.parent.microscope.yrow = 0
        self.parent.microscope.mcoords()

class ImagingControls(tk.Frame):
    """Tool to control imaging

    Attributes:
        parent: actual parent is a container so this is the container's parent
        snapButton: takes a single image of the current view
        runButton: takes a series of images, determined by the configuration
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent.parent
        GUI.configure_rows(self, 2)
        GUI.configure_columns(self, 1)

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
    
    def tdate(self):
        """Returns the current date as a nice string
        TODO: private?
        """
        return datetime.now().strftime('%h-%d-%Y_%I:%M%p').replace(" ","")

    def _get_samp_name(self, row=None, col=None, samp=None):
        """Returns the sample name of the current sample or given sample if specified

        Args:
            row: row of sample
            col: column of sample
            samp: subsample index

        Throws:
            Exception if only one argument is specified.
        """
        if row or col or samp:
            assert((row is not None) and (col is not None) and (samp is not None))
            yrow = row
            xcol = col
            samp_index = samp
        else:
            yrow = self.parent.microscope.yrow
            xcol = self.parent.microscope.xcol
            if self.parent.config.samps > 1:
                samp_index = self.parent.microscope.samp
            else:
                samp_index = None
        self.parent.configurationtool.update_config()
        samp_name = self.parent.config.get_sample_name(yrow, xcol)
        if self.parent.config.samps > 1 or samp:
            samp_name += self.parent.config.get_subsample_id(samp_index)
        return samp_name

    def _initialize_directories(self, snap=True):
        """Ensure all directories and subdirectories exist for images
        
        Args:
            snap: Boolean indicating whether this is for a single image
        
        Returns:
            The path to the innermost directory
        """
        self.parent.configurationtool.update_config()
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

    def snap_cb(self, event):
        """Takes a simple snapshot of the current view

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        path1 = self._initialize_directories()
        xcol = self.parent.microscope.xcol
        yrow = self.parent.microscope.yrow
        if self.parent.config.samps == 1: 
            sname = path1 + '/' + self.parent.config.get_sample_name(yrow, xcol)+"_"+self.tdate()+'.jpg'
        else:
            sname = path1 + '/' + self.parent.config.get_sample_name(yrow, xcol)+self.parent.config.get_subsample_id(self.parent.microscope.samp)+"_"+self.tdate()+'.jpg'
        self.parent.microscope.camera.capture(sname)
        self.parent.messagearea.setText("image saved to {}".format(sname))

    def snap_right_cb(self, event):
        """right mouse snap - takes a series of z-stacked pictures using nimages and Z-spacing parameters

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
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
            self.parent.microscope.grbl.rapid_move(z=z)
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
        self.parent.microscope.grbl.rapid_move(z=z_sav) # return to original z 
        self.parent.microscope.wait_for_Idle()
        self.parent.messagearea.setText("individual images:" + path1 + "\n" + 'source '+samp_name+'_process_snap.com to combine z-stack')
    
    def run_cb(self, event):
        """Runs a series of image shots

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.updatebtn_cb(event) # get data from the GUI window and save/update the configuration file... 
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
            self.parent.microscope.grbl.hard_limits(False)
            print('hard limits disabled')
        for yrow in range(self.parent.config.ny):
            for xcol in range(self.parent.config.nx):
                for samp in range(self.parent.config.samps):
                    self.parent.microscope.mcoords() # go to the expected position of the focussed sample 
                    z = self.parent.microscope.mz-(1-self.parent.microscope.fracbelow)*zrange # bottom of the zrange (this is the top of the sample!)
                    samp_name = self._get_samp_name(yrow, xcol, samp)
                    processf.write('echo \'processing: '+samp_name+'\' \n')
                    line='align_image_stack -m -a OUT '
                    # TODO: i think this is reused in snap function
                    for imgnum in range(self.parent.config.nimages):
                        self.parent.microscope.rapid_move(z=z)
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
            self.parent.microscope.grbl.hard_limits(True) # turn hard limits back on
            print('hard limits enabled')
        self.parent.microscope.stopit = False

class MovementAndImaging(tk.Frame):
    """Container for Movement and Imaging

    Attributes:
        parent: actual parent is a container so this is the container's parent
        movementtool: tools for navigation
        imagingcontrols: tools for taking images
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent
        GUI.configure_rows(self, 1)
        GUI.configure_columns(self, 2)

        self.movementtool = MovementTool(self)
        self.imagingcontrols = ImagingControls(self)

        fillhorizontal = tk.E + tk.W
        self.movementtool.grid(row=0, column=0, sticky=fillhorizontal, padx=3)
        self.imagingcontrols.grid(row=0, column=1, sticky=fillhorizontal, padx=3)

class ConfigurationTool(tk.Frame):
    """UI for configuration options

    Attributes:
        parent: actual parent is a container so this is the container's parent
        filee: Entry field for file name
        sIDe: Entry field for sample name
        pIDe: Entry field for plane name
        sampse: Entry field for number of samples in each well
        nxe: Entry field for number of rows
        nye: Entry field for number of columns
        nimge: Entry field for number of images to take of each drop during run
        zspe: Entry field for z-spacing in between each image
        updateButton: Writes configuration to specified file
        readButton: Reads configuration from specified file
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(highlightbackground="black",
                    highlightthickness=3,
                    background="lightgrey")
        self.parent = parent
        GUI.configure_rows(self, 4)
        GUI.configure_columns(self, 10)
        
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

    def updatebtn_cb(self, event):
        """Updates config values and writes updates to file
        
        Args:
            event: information on the event that triggered this
        """
        if not self.parent.config:
            self.parent.messagearea.setText("There is not existing configuration to update. Nothing written")
            return

        tmp_fname = str(self.filee.get())
        if " " in tmp_fname:
            self.parent.messagearea.setText("file name cannot contain spaces. Nothing written.")
            self.filee.delete(0,tk.END)
            self.filee.insert(0,"")
            self.update()
        else:
            self.update_config()
            self.parent.config.write()
            self.parent.messagearea.setText("parameters saved to " + tmp_fname)

    def update_config(self):
        """Updates all config values to current values held in text fields
        """
        if not self.parent.config:
            self.parent.messagearea.setText("There is not existing configuration to update. Nothing written")
            return
        
        self.parent.config.fname = str(self.filee.get())
        self.parent.config.nx = int(self.nxe.get())
        self.parent.config.ny = int(self.nye.get())
        self.parent.config.samps = int(self.sampse.get())
        self.parent.config.nimages = int(self.nimge.get())
        self.parent.config.zstep = float(self.zspe.get())
        self.parent.config.sID = str(self.sIDe.get())
        self.parent.config.nroot = str(self.pIDe.get())
        self.parent.messagearea.setText("parameter values up to date")


    def readbtn_cb(self, event):
        """Reads config values from file
        
        Args:
            event: information on the event that triggered this
        """
        fname = str(self.filee.get())
        self.parent.read_config(fname=fname)
        self.update_entry_fields()
        print('Parameters read from ' + fname)
        self.update()
    
    def update_entry_fields(self):
        """Updates entry fields to match those in the Config module
        """
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
    """Main window for the GUI. Acts as the "Controller" in MVC programming.

    Attributes:
        parent: TK root object
        config: configuration object containing internal representation
        microscope: object to interact with external hardware
        missagearea: see MessageArea
        translationtool: see TranslationTool
        calibrationandhardware: see CalibrationAndHardware
        calibrationtool: see CalibrationTool
        hardwarecontrols: see HardwareControls
        movementandimaging: see MovementAndImaging
        movementtool: see MovementTool
        imagingcontrols: see ImagingControls
        configurationtool: see ConfigurationTool
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        GUI.configure_rows(self, 5)
        GUI.configure_columns(self, 1)
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.close)

        # Set up initial configuration
        self.config = None
        self.read_config()
        self.microscope = Microscope(self.config)
        
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

    @staticmethod
    def configure_rows(obj, numrows):
        """Configures rows to resize appropriately when using Grid Manager

        Args:
            obj: the TK widget to configure
            numrows: Integer number of rows to configure
        """
        for i in range(numrows):
            tk.Grid.rowconfigure(obj, i, weight=1)

    @staticmethod
    def configure_columns(obj, numcols):
        """Configures columns to resize appropriately when using Grid Manager

        Args:
            obj: the TK widget to configure
            numcols: Integer number of columns to configure
        """
        for i in range(numcols):
            tk.Grid.columnconfigure(obj, i, weight=1)

    def read_config(self, fname='AMi.config'):
        """Reads information from the configuration file

        Args:
            fname: name of the configuration file
        """
        try:
            self.config = Config(fname)
        except ValueError:
            print("Configuration file does not exist")
        except:
            Config.print_help()
            if fname=='AMi.config': sys.exit() #TODO: what does this do?, I think this closes the program if the configuration file does not exist in the directory??

    def close(self):
        """Performs closing procedures
        """
        print('moving back to the origin and closing the graphical user interface')
        self.microscope.grbl.run_homing_cycle() # tell grbl to find zero 
        if self.microscope.light1_stat:
            self.microscope.toggle_light1()
        if self.microscope.light2_stat:
            self.microscope.toggle_light2_arduino()
        self.microscope.grbl.close()
        if self.microscope.viewing:
            self.microscope.switch_camera_preview()
        self.parent.destroy()

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

    root.update()
    root.geometry("{}x{}+{}+{}".format(root.winfo_width(), 
                                       root.winfo_height(), 
                                       root.winfo_screenwidth() - root.winfo_width(),
                                       0))
    root.mainloop()

    # After close
    print('\n Hope you find what you\'re looking for!  \n')

if __name__ == "__main__":
    main()