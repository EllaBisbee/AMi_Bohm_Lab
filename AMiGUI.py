"""The main Graphical User Interface for AMi

This file contains all of the modules and classes needed to create the
GUI.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from datetime import datetime
from time import sleep
from shutil import copyfile
from threading import Thread
from dotenv import load_dotenv
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
                          highlightthickness=1, background=parent['bg'])
        self.parent = parent
        self._text = tk.StringVar()
        self._text.set(text)
        self._label = ttk.Label(self, textvariable=self._text,
                                background=parent['bg'])
        self._label.config(wraplength=self.parent.winfo_width())
        self._label.bind("<Configure>", self._onresize)
        self._label.pack()

    def _onresize(self, _event):
        """Callback for when the internal label is resized.

        Args:
            event: information from the event that triggered a call
        """
        self._label.config(wraplength=self.parent.winfo_width())

    def set_text(self, text):
        """Changes the text displayed.

        Args:
            text: String containing the new text
        """
        self._text.set(text)

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

    def _on_resize(self, _event):
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
        # z-setting outline
        self.zsetting.create_rectangle(
            bordermargin, bordermargin, zwidth - bordermargin,
            zheight - bordermargin, outline=bordercolor, width=borderwidth)
        # z-setting center line
        self.zsetting.create_line(
            bordermargin, zheight/2 - borderwidth/2, zwidth - bordermargin,
            zheight/2 - borderwidth/2, width=borderwidth)
        # z guide lines
        for i in range(1, int(zheight/2/guidespacing) + 1):
            self.zsetting.create_line(
                linescuttoff, zheight/2 - i * guidespacing,
                zwidth - linescuttoff, zheight/2 - i * guidespacing,
                fill=guidecolor)
            self.zsetting.create_line(
                linescuttoff, zheight/2 + i * guidespacing,
                zwidth - linescuttoff, zheight/2 + i * guidespacing,
                fill=guidecolor)
        self.zsetting.create_text(zwidth/2, 0, fill=labelcolor, font=labelfont,
                                  text="+Z", anchor=tk.N)
        self.zsetting.create_text(zwidth/2, zheight, fill=labelcolor,
                                  font=labelfont, text="-Z", anchor=tk.S)

        # Draw xy-setting
        self.xysetting.delete("all")
        self.xysetting.config(width=xywidth, height=xyheight)
        # xy border
        self.xysetting.create_rectangle(
            bordermargin, bordermargin, xywidth - bordermargin,
            xyheight - bordermargin, outline=bordercolor, width=borderwidth)
        # xy vertical
        self.xysetting.create_line(
            xywidth/2 - borderwidth/2, bordermargin, xywidth/2 - borderwidth/2,
            xyheight - bordermargin, width=borderwidth)
        # xy horizontal
        self.xysetting.create_line(
            bordermargin, xyheight/2 - borderwidth/2, xywidth - bordermargin,
            xyheight/2 - borderwidth/2, width=borderwidth)
        for i in range(1, int(xywidth/2/guidespacing) + 1): #xy guide circles
            self.xysetting.create_oval(
                xywidth/2 - i * guidespacing, xyheight/2 - i * guidespacing,
                xywidth/2 + i * guidespacing, xyheight/2 + i * guidespacing,
                outline=guidecolor)
        self.xysetting.create_text(xywidth/2, 0, fill=labelcolor,
                                   font=labelfont, text="+Y", anchor=tk.NW)
        self.xysetting.create_text(xywidth/2, xyheight, fill=labelcolor,
                                   font=labelfont, text="-Y", anchor=tk.SW)
        self.xysetting.create_text(borderwidth, xyheight/2, fill=labelcolor,
                                   font=labelfont, text="-X", anchor=tk.SW)
        self.xysetting.create_text(
            xywidth - borderwidth, xyheight/2, fill=labelcolor, font=labelfont,
            text="+X", anchor=tk.SE)

    def motion(self, event):
        """Callback that records the last clicked area within the tool.

        Args:
            event: information for the event that triggered this
        """
        self._gx, self._gy = event.x, event.y

    def left_click_z(self, _event):
        """Callback that triggers a z-move for the machine

        Args:
            event: information for the event that triggered this
        """
        print('left_click gx,gy,xcol,yrow', self._gx, self._gy,
              self.parent.microscope.xcol, self.parent.microscope.yrow)
        midpoint = self.zsetting.winfo_height() / 2
        rz = midpoint - self._gy
        mzsav = self.parent.microscope.mz
        self.parent.microscope.mz += 0.0001 * (abs(rz)**2.2) * np.sign(rz)
        mz = self.parent.microscope.mz
        zmax = self.parent.microscope.zmax
        if mz > 0. and mz < zmax:
            self.parent.microscope.grbl.rapid_move(z=self.parent.microscope.mz)
            message = ('current Z: '+str(round(self.parent.microscope.mz, 3))+
                       ' change: '+
                       str(round((self.parent.microscope.mz-mzsav), 3)))
            if self.parent.calibrationtool.corner:
                self.parent.messagearea.set_text(message)
            else:
                self.parent.messagearea.set_text("")
            print(message)
        else:
            self.parent.messagearea.set_text(
                "that move would take you out of bounds")
            self.parent.microscope.mz = mzsav

    def left_click_xy(self, _event):
        """Callback that triggers a xy-move for the machine

        Args:
            event: information for the event that triggered this
        """
        print('left_click gx,gy,xcol,yrow', self._gx, self._gy,
              self.parent.microscope.xcol, self.parent.microscope.yrow)
        x_mid = self.xysetting.winfo_width() / 2
        y_mid = self.xysetting.winfo_height() / 2
        rx = self._gx - x_mid
        ry = y_mid - self._gy
        mxsav = self.parent.microscope.mx
        mysav = self.parent.microscope.my
        self.parent.microscope.mx += 0.0001*(abs(rx)**2.2)*np.sign(rx)
        self.parent.microscope.my += 0.0001*(abs(ry)**2.2)*np.sign(ry)
        mx, my = self.parent.microscope.mx, self.parent.microscope.my
        xmax, ymax = self.parent.microscope.xmax, self.parent.microscope.ymax
        if mx > 0. and my > 0. and mx < xmax and my < ymax:
            self.parent.microscope.grbl.rapid_move(
                x=self.parent.microscope.mx,
                y=self.parent.microscope.my)
            if self.parent.calibrationtool.corner:
                self.parent.messagearea.set_text(
                    'current X,Y: {}, {}'.format(
                        str(round(self.parent.microscope.mx, 3)),
                        str(round((self.parent.microscope.my), 3))))
            else:
                self.parent.messagearea.set_text('')
            print('current X: {} change: {}'.format(
                str(round(self.parent.microscope.mx, 3)),
                str(round((self.parent.microscope.mx-mxsav), 3))))
            print('current Y: {} change: {}'.format(
                str(round(self.parent.microscope.my, 3)),
                str(round((self.parent.microscope.my-mysav), 3))))
        else:
            self.parent.messagearea.set_text(
                "that move would take you out of bounds")
            self.parent.microscope.mx = mxsav
            self.parent.microscope.my = mysav

class CalibrationTool(tk.Frame):
    """A tool used to calibrate the internal configuration

    Attributes:
        parent: actual parent is a container so this is the container's parent
        corner: the corner OR subsample index currently calibrating
        tl_btn: the button to select the top left corner
        tr_btn: the button to select the top right corner
        bl_btn: the button to select the bottom left corner
        br_btn: the button to select the bottom right corner
        set_btn: the button to store the calibration
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
        style.configure("Calibration.TButton", font="Helvetia 12",
                        background="skyblue1")
        style.map("Calibration.TButton",
                  background=[('active', 'green'), ('pressed', 'green')])
        # Top-left
        self.tl_btn = ttk.Button(
            self, text="TL", style="Calibration.TButton", width=btnwidth)
        self.tl_btn.bind("<Button-1>", self.tl_left_cb)
        self.tl_btn.bind("<Button-3>", self.tl_right_cb)
        self.tl_btn.grid(row=0, column=0, columnspan=2, sticky=fillcell,
                         pady=btnpad, padx=btnpad)

        # Top-right
        self.tr_btn = ttk.Button(self, text="TR",
                                 style="Calibration.TButton", width=btnwidth)
        self.tr_btn.bind("<Button-1>", self.tr_cb)
        self.tr_btn.grid(row=0, column=2, columnspan=2,
                         sticky=fillcell, pady=btnpad, padx=btnpad)

        # Bottom-left
        self.bl_btn = ttk.Button(self, text="BL",
                                 style="Calibration.TButton", width=btnwidth)
        self.bl_btn.bind("<Button-1>", self.bl_cb)
        self.bl_btn.grid(row=2, column=0, columnspan=2, sticky=fillcell,
                         pady=btnpad, padx=btnpad)

        # Bottom-right
        self.br_btn = ttk.Button(self, text="BR",
                                 style="Calibration.TButton", width=btnwidth)
        self.br_btn.bind("<Button-1>", self.br_cb)
        self.br_btn.grid(row=2, column=2, columnspan=2, sticky=fillcell,
                         pady=btnpad, padx=btnpad)

        # set button
        style.configure("Calibration-Set.TButton", font="Helvetia 12 bold",
                        background="yellow")
        style.map("Calibration-Set.TButton",
                  background=[('active', 'green'), ('pressed', 'green')])
        self.set_btn = ttk.Button(
            self, text="SET", style="Calibration-Set.TButton", width=btnwidth)
        self.set_btn.bind("<Button-1>", self.set_cb)
        self.set_btn.grid(row=1, column=1, columnspan=2, sticky=fillcell,
                          pady=btnpad, padx=btnpad)

    def tl_left_cb(self, event):
        """Callback for the top left button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "TL"
        self.parent.mcoords(0, 0, 0)
        if self.parent.config.samps > 1:
            self.parent.messagearea.set_text(
                "SET now changes TL coordinates. " +
                "After the corners Right Click TL for sub-samples")
        else:
            self.parent.messagearea.set_text(
                "SET now changes TL coordinates.")

    def tl_right_cb(self, event):
        """Callback for the top left button right click.

        Updates subsample offsets

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        config = self.parent.config
        config.ensure_samp_coord_dimension()
        print('samp_coord', config.samp_coord)
        if config.samps > 1:
            newsamp = self.parent.microscope.samp + 1
            if newsamp == config.samps:
                newsamp = 1
            self.parent.microscope.samp = newsamp
            self.corner = str(newsamp)
            self.parent.mcoords(0, 0, newsamp)
            self.parent.messagearea.set_text(
                "SET now changes sub-sample {} coordinates.".format(
                    config.get_subsample_id(self.parent.microscope.samp)))
        else:
            self.parent.messagearea.set_text("no sub-samples specified.")

    def tr_cb(self, event):
        """Callback for the top right button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "TR"
        self.parent.mcoords(self.parent.config.nx - 1, 0, 0)
        self.parent.messagearea.set_text("SET now changes TR coordinates.")

    def bl_cb(self, event):
        """Callback for the bottom left button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "BL"
        self.parent.mcoords(0, self.parent.config.ny - 1, 0)
        self.parent.messagearea.set_text("SET now changes BL coordinates.")

    def br_cb(self, event):
        """Callback for the bottom right button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self.corner = "BR"
        self.parent.mcoords(
            self.parent.config.nx - 1, self.parent.config.ny - 1, 0)
        self.parent.messagearea.set_text("SET now changes BR coordinates.")

    def set_cb(self, event):
        """Callback for the set button left click.

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        m = self.parent.microscope.get_machine_position()
        config = self.parent.config
        if self.corner is None:
            self.parent.messagearea.set_text("You must first select a corner")
        elif self.corner.isdigit():
            subsample = int(self.corner)
            x_offset = (m[0]-config.tl[0])/(config.tr[0]-config.tl[0])
            y_offset = (m[1]-config.tl[1])/(config.bl[1]-config.tl[1])
            (config.samp_coord)[subsample] = [x_offset, y_offset]
            print("new sample {} coordinates: {}".format(
                subsample, config.samp_coord[subsample]))
            self.parent.messagearea.set_text("{} coordinates saved".format(
                config.get_subsample_id(subsample)))
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
            message = "{} coordinates saved".format(self.corner)
            self.parent.messagearea.set_text(message)

        self.corner = None

class HardwareControls(tk.Frame):
    """Additional controls for the external hardware

    Buttons to control the additional hardware. This include the lights
    and the camera. Also includes control to reset the origin and to
    close the program.

    Attributes:
        parent: actual parent is a container so this is the container's parent
        view_btn: Controls the live preview of the camera
        reset_btn: Resets the origin
        close_btn: Stops a run or closes the program
        light1_btn: Light switch for white light
        light2_btn: Light switch for color light
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configure(background=parent['bg'])
        self.parent = parent.parent
        GUI.configure_rows(self, 3)
        GUI.configure_columns(self, 2)

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        style = ttk.Style()
        style.configure('LiveView.TButton', font="Helvetia 12 bold",
                        foreground="black", background="orange")
        style.map('LiveView.TButton',
                  background=[('active', 'green'), ('pressed', 'green')])
        self.view_btn = ttk.Button(
            self, text="VIEW", style="LiveView.TButton")
        self.view_btn.bind("<Button-1>", self.view_cb)
        self.view_btn.grid(
            columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.reset_btn = ttk.Button(self, text="reset origin")
        self.reset_btn.bind("<Button-1>", self.reset_cb)
        self.reset_btn.bind("<Button-3>", self.reset_right_cb)
        self.reset_btn.grid(
            row=1, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.close_btn = ttk.Button(self, text="stop/close")
        self.close_btn.bind("<Button-1>", self.close_cb)
        self.close_btn.grid(
            row=1, column=1, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light1_btn = ttk.Button(self, text="light1")
        self.light1_btn.bind("<Button-1>", self.light1_cb)
        self.light1_btn.grid(
            row=2, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light2_btn = ttk.Button(self, text="light2")
        self.light2_btn.bind("<Button-1>", self.light2_cb)
        self.light2_btn.grid(
            row=2, column=1, sticky=fillcell, pady=btnpad, padx=btnpad)

    def view_cb(self, event):
        """Toggles live preview

        Args:
            event: information on the event that triggered this
        """
        if not self.parent.microscope.running:
            self.parent.microscope.switch_camera_preview()
            self.parent.messagearea.set_text(
                "click VIEW to open/close live view")

    def reset_cb(self, event):
        """Resets CNC machine to home

        Args:
            event: information on the event that triggered this
        """
        self.parent.calibrationtool.corner = None
        print("clicked origin reset")
        self.parent.messagearea.set_text("wait while machine resets...")
        self.parent.microscope.grbl.kill_alarm_lock()
        self.parent.microscope.grbl.run_homing_cycle() # send homing command
        self.parent.messagearea.set_text("Ready to rumble!")

    def reset_right_cb(self, event):
        """Resets CNC machine to home due to critical error (alarm)
        Args:
            event: information on the event that triggered this
        """
        self.parent.calibrationtool.corner = None
        print("clicked reset alarm")
        self.parent.messagearea.set_text("$X sent to GRBL...")
        self.parent.microscope.grbl.kill_alarm_lock()
        self.parent.messagearea.set_text("It might work now...")

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
        self.calibrationtool.grid(
            row=0, column=0, sticky=fillhorizontal, padx=3)
        self.hardwarecontrols.grid(
            row=0, column=1, sticky=fillhorizontal, padx=3)

class MovementTool(tk.Frame):
    """Tool to navigate between drops

    Attributes:
        parent: actual parent is a container so this is the container's parent
        pose: Entry box for the desired sample
        goto_btn: Navigates to sample specified in pose above
        prev_btn: Navigates to the previous sample
        next_btn: Navigates to the next sample
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
        pady = 3
        padx = 5
        width = 0
        style = ttk.Style()
        style.configure('Movement.TButton', background="cyan2")
        style.map('Movement.TButton',
                  background=[('active', 'green'), ('pressed', 'green')])

        self.goto_btn = ttk.Button(
            self, text="go to", style="Movement.TButton", width=width)
        self.goto_btn.bind("<Button-1>", self.goto_cb)
        self.goto_btn.grid(
            row=0, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.pose = ttk.Entry(self, width=width)
        self.pose.insert(0, "A1")
        self.pose.grid(row=0, column=1, sticky=fillcell, pady=pady, padx=padx)

        self.prev_btn = ttk.Button(
            self, text="prev", style="Movement.TButton", width=width)
        self.prev_btn.bind("<Button-1>", self.prev_left_cb)
        self.prev_btn.bind("<Button-3>", self.prev_right_cb)
        self.prev_btn.grid(
            row=1, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.next_btn = ttk.Button(
            self, text="next", style="Movement.TButton", width=width)
        self.next_btn.bind("<Button-1>", self.next_left_cb)
        self.next_btn.bind("<Button-3>", self.next_right_cb)
        self.next_btn.grid(
            row=1, column=1, sticky=fillcell, pady=pady, padx=padx)

    def _cancel_calibration(self):
        """Cancels calibrating if user was previously calibrating
        """
        self.parent.calibrationtool.corner = None

    def goto_cb(self, event):
        """Navigates to the well specified in pose

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self._cancel_calibration()
        pose_txt = str(self.pose.get())
        pose_txt = pose_txt.replace(" ", "") #get rid of spaces
        pose_txt = pose_txt.rstrip("\r\n") # get rid of carraige return
        self.parent.microscope.samp = 0
        sample_name = pose_txt

        try:
            # first deal with the sub-sample character if present
            samp = 0
            if not sample_name[-1].isdigit(): # sub-sample is specified
                samp = self.parent.config.get_subsample_index(sample_name[-1])
                sample_name = sample_name[0:-1] # remove subsample
            row, col = self.parent.config.get_row_col(sample_name)
            print('yrow,xcol', row, col)
            self.parent.mcoords(col, row, samp)
        except Exception: # pylint: disable=broad-except
            self.parent.messagearea.set_text("input error")

    def prev_left_cb(self, event):
        """Navigates to the sample before the current one

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self._cancel_calibration()
        self.parent.messagearea.set_text("")
        if self.parent.microscope.samp > 0:
            self.parent.mcoords(newcol=self.parent.microscope.xcol,
                                newrow=self.parent.microscope.yrow,
                                newsamp=self.parent.microscope.samp-1)
        elif self.parent.microscope.xcol > 0:
            self.parent.mcoords(newcol=self.parent.microscope.xcol - 1,
                                newrow=self.parent.microscope.yrow,
                                newsamp=self.parent.microscope.samp-1)
        elif self.parent.microscope.yrow > 0:
            self.parent.mcoords(newcol=self.parent.config.nx-1,
                                newrow=self.parent.microscope.yrow-1,
                                newsamp=self.parent.microscope.samp-1)
        else:
            self.parent.messagearea.set_text(
                "cannot reverse beyond the first sample")

    def prev_right_cb(self, event):
        """Navigates to the previous row, keeping column and subsample

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self._cancel_calibration() # this logic was not in the original code.
        self.parent.messagearea.set_text("")
        newrow = self.parent.microscope.yrow - 1
        if newrow == -1:
            newrow = self.parent.config.ny - 1
        self.parent.mcoords(newcol=self.parent.microscope.xcol,
                            newrow=newrow,
                            newsamp=self.parent.microscope.samp)

    def next_left_cb(self, event):
        """Navigates to the sample following the current one

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self._cancel_calibration()
        self.parent.messagearea.set_text("")
        if self.parent.microscope.samp < (self.parent.config.samps - 1):
            self.parent.mcoords(newcol=self.parent.microscope.xcol,
                                newrow=self.parent.microscope.yrow,
                                newsamp=self.parent.microscope.samp+1)
        elif self.parent.microscope.xcol < (self.parent.config.nx - 1):
            self.parent.mcoords(newcol=self.parent.microscope.xcol+1,
                                newrow=self.parent.microscope.yrow,
                                newsamp=0)
        elif self.parent.microscope.yrow < (self.parent.config.ny - 1):
            self.parent.mcoords(newcol=0,
                                newrow=self.parent.microscope.yrow+1,
                                newsamp=0)
        else:
            self.parent.messagearea.set_text(
                "cannot advance beyond the last sample")

    def next_right_cb(self, event):
        """Navigates to the following row, keeping column and subsample

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        self._cancel_calibration()
        self.parent.messagearea.set_text("")
        newrow = self.parent.microscope.yrow + 1
        if newrow == self.parent.config.ny:
            newrow = 0
        self.parent.mcoords(newcol=self.parent.microscope.xcol,
                            newrow=newrow,
                            newsamp=self.parent.microscope.samp)

class ImagingControls(tk.Frame):
    """Tool to control imaging

    Attributes:
        parent: actual parent is a container so this is the container's parent
        snap_btn: takes a single image of the current view
        run_btn: takes a series of images, determined by the configuration
    """
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent.parent
        GUI.configure_rows(self, 2)
        GUI.configure_columns(self, 1)

        fillcell = tk.N + tk.E + tk.S + tk.W
        style = ttk.Style()
        style.map('ActvGreen.TButton',
                  background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Img-Snp.ActvGreen.TButton', font="Helvetia 12 bold",
                        foreground="white", background="medium blue")
        style.configure('Img-Run.ActvGreen.TButton', font="Helvetia 12 bold",
                        foreground="yellow", background="black")

        self.snap_btn = ttk.Button(
            self, text="SNAP IMAGE", style="Img-Snp.ActvGreen.TButton")
        self.snap_btn.bind("<Button-1>", self.snap_cb)
        self.snap_btn.bind("<Button-3>", self.snap_right_cb)
        self.snap_btn.grid(sticky=fillcell, pady=(0, 5))

        self.run_btn = ttk.Button(
            self, text="RUN", style="Img-Run.ActvGreen.TButton")
        self.run_btn.bind("<Button-1>", self.run_cb)
        self.run_btn.grid(sticky=fillcell, pady=(5, 0))

        self._thread = None

    def _tdate(self):
        """Returns the current date as a nice string
        """
        return datetime.now().strftime('%h-%d-%Y_%I:%M%p').replace(" ", "")

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
            msg = "created directory {} within the imaged directory".format(
                sID)
            print(msg)
        path1 += '/' + nroot
        if not os.path.isdir(path1):
            os.mkdir(path1)
            msg = 'created directory {} within the images/{} directory'.format(
                nroot, sID)
            print(msg)

        if snap:
            path1 += '/snaps'
            if not os.path.isdir(path1):
                os.mkdir(path1)
                msg = ("created directory \'snaps\' " +
                       "within the images/{}/{} directory".format(sID, nroot))
                print(msg)
        else:
            path1 += '/' + self._tdate()
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
        samp = self.parent.microscope.samp
        if self.parent.config.samps == 1:
            sname = (path1 + '/' +
                     self.parent.config.get_sample_name(yrow, xcol)+
                     "_"+self._tdate()+'.jpg')
        else:
            sname = (path1 + '/' +
                     self.parent.config.get_sample_name(yrow, xcol)+
                     self.parent.config.get_subsample_id(samp)+
                     "_"+self._tdate()+'.jpg')
        self.parent.microscope.camera.capture(sname)
        self.parent.messagearea.set_text("image saved to {}".format(sname))

    def _take_zstack(self, basepath, samp_name, internaldirs=None):
        """Takes z-stack images of current sample

        Saves images to basepath/internaldirs/fname_[img num].jpg

        Args:
            basepath: root path for images
            samp_name: base filename for image
            internaldirs: internal directory paths from basepath, if needed

        Returns:
            String with the align_image_stack bash command
        """
        zrange = (self.parent.config.nimages-1)*self.parent.config.zstep
        # bottom of the zrange (this is the top of the sample!)
        z = (self.parent.microscope.mz -
             (1-self.parent.microscope.fracbelow)*zrange)
        line = 'align_image_stack -m -a OUT '
        for imgnum in range(self.parent.config.nimages):
            self.parent.microscope.grbl.rapid_move(z=z)
            self.parent.microscope.wait_for_idle()
            fname = samp_name + "_" + str(imgnum) + ".jpg"
            if internaldirs is not None:
                internalpath = internaldirs + "/" + fname
            else:
                internalpath = fname
            imgname = basepath + "/" + internalpath
            # slow things down to allow camera to settle down
            sleep(self.parent.microscope.camera_delay)
            self.parent.microscope.camera.capture(imgname)
            line += internalpath + " "
            z += self.parent.config.zstep
        line += (' \n')
        return line

    def _append_to_stack_process(self, processf, samp_name, line):
        """Creates image stack processing commands for given line and appends
        to the given process file

        Args:
            processf: An open process file to write to
            samp_name: the sample name associated with this image stack
            line: the align_image_stack command for this image stack
        """
        processf.write('echo \'processing: '+samp_name+'\' \n')
        processf.write(line)
        enfuse = ("enfuse " +
                  "--exposure-weight=0 --saturation-weight=0 " +
                  "--contrast-weight=1 --hard-mask " +
                  "--output={}.tif OUT*.tif \n".format(samp_name))
        processf.write(enfuse)
        processf.write('rm OUT*.tif \n')

    def snap_right_cb(self, event):
        """right mouse snap - takes a series of z-stacked pictures using
        nimages and Z-spacing parameters

        Args:
            event: information on the event that triggered this
        """
        self.parent.configurationtool.update_config()
        yrow = self.parent.microscope.yrow
        xcol = self.parent.microscope.xcol
        samp = self.parent.microscope.samp
        if self.parent.config.samps > 1:
            samp_name = self.parent.config.get_name_with_subsample(
                yrow, xcol, samp)
        else:
            samp_name = self.parent.config.get_sample_name(yrow, xcol)
        path1 = self._initialize_directories()
        processf = open(path1 + '/' + samp_name + '_process_snap.com', 'w')
        processf.write('rm OUT*.tif \n')
        z_sav = self.parent.microscope.mz
        samp_name += '_' + self._tdate()
        line = self._take_zstack(path1, samp_name)
        self._append_to_stack_process(processf, samp_name, line)
        self.parent.microscope.grbl.rapid_move(z=z_sav) # return to original z
        self.parent.microscope.wait_for_idle()
        self.parent.messagearea.set_text(
            "individual images:" + path1 + "\n" +
            "source "+samp_name+"_process_snap.com to combine z-stack")

    def _run_thread(self, event):
        """Runs a series of image shots in a separate thread.

        Args:
            event: information on the event that triggered this
        """
        # get data from the GUI window and update the configuration file..
        self.parent.configurationtool.updatebtn_cb(event)
        self.parent.mcoords(0, 0, 0) #go to A1
        imgpath = self._initialize_directories(snap=False)
        if not os.path.isdir(imgpath+'/rawimages'):
            os.mkdir(imgpath+'/rawimages')
            print('created directory: '+imgpath+'/rawimages')
            copyfile(self.parent.config.fname,
                     imgpath + '/' + self.parent.config.fname)
        if not self.parent.microscope.viewing:
            self.parent.microscope.switch_camera_preview()
            sleep(2) # let camera adapt to the light before collecting images
        processf = open(imgpath+'/process'+self.parent.config.nroot+'.com', 'w')
        processf.write('rm OUT*.tif \n')
        self.parent.microscope.running = True
        self.parent.messagearea.set_text("imaging samples...")
        if self.parent.microscope.disable_hard_limits:
            self.parent.microscope.grbl.hard_limits(False)
            print('hard limits disabled')
        for well in range(self.parent.config.ny * self.parent.config.nx):
            yrow, xcol = self.parent.config.get_row_col(str(well+1))
            for samp in range(self.parent.config.samps):
                if self.parent.microscope.stopit:
                    break
                self.parent.mcoords(xcol, yrow, samp) # go to sample
                samp_name = self.parent.config.get_name_with_subsample(
                    yrow, xcol, samp)
                line = self._take_zstack(imgpath, samp_name, "rawimages")
                self._append_to_stack_process(processf, samp_name, line)
            if self.parent.microscope.stopit:
                break
        self.parent.microscope.running = False
        processf.close()
        # turn off the preview so the monitor can go black when the pi sleeps
        self.parent.microscope.switch_camera_preview()
        self.parent.microscope.toggle_light1() #turn off light1
        self.parent.microscope.toggle_light2_arduino() #turn off light2
        if self.parent.microscope.disable_hard_limits:
            # turn hard limits back on
            self.parent.microscope.grbl.hard_limits(True)
            print('hard limits enabled')
        self.parent.microscope.stopit = False

    def run_cb(self, event):
        """Runs a series of image shots

        Args:
            event: information on the event that triggered this
        """
        self._thread = Thread(target=self._run_thread, args=[event])
        self._thread.start()

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
        self.imagingcontrols.grid(
            row=0, column=1, sticky=fillhorizontal, padx=3)

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
        update_btn: Writes configuration to specified file
        read_btn: Reads configuration from specified file
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
        style.configure('Config.TButton',
                        font="Helvetia 10", width=8, background="yellow")
        style.map('Config.TButton',
                  background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Config.TLabel',
                        background=self['bg'], font="Helvetia 10")

        self.filee = ttk.Entry(self, width=1)
        self.filee.grid(
            row=0, column=0, columnspan=3, pady=2, padx=(2, 0), sticky=fillcell)

        ttk.Label(
            self, text='Sample ID:', style="Config.TLabel", anchor=tk.E).grid(
                row=0, column=3, columnspan=2, sticky=fillcell, pady=2)
        self.sIDe = ttk.Entry(self, width=1)
        self.sIDe.grid(row=0, column=5, columnspan=5, pady=2, sticky=fillcell)

        ttk.Label(
            self, text='Plate ID:', style="Config.TLabel", anchor=tk.E).grid(
                row=1, column=0, columnspan=2, sticky=fillcell, pady=2)
        self.pIDe = ttk.Entry(self, width=1)
        self.pIDe.grid(row=1, column=2, columnspan=3, pady=2, sticky=fillcell)

        ttk.Label(
            self, text='samples/pos:', style="Config.TLabel",
            anchor=tk.E).grid(
                row=1, column=5, columnspan=4, sticky=fillcell, pady=2)
        self.sampse = ttk.Entry(self, width=1)
        self.sampse.grid(row=1, column=9, sticky=fillcell, pady=2)

        ttk.Label(
            self, text='nx:', style="Config.TLabel", anchor=tk.E).grid(
                row=2, column=0, sticky=fillcell, pady=2)
        self.nxe = ttk.Entry(self, width=1)
        self.nxe.grid(row=2, column=1, sticky=fillcell, pady=2)

        ttk.Label(
            self, text='ny:', style="Config.TLabel", anchor=tk.E).grid(
                row=2, column=2, sticky=fillcell, pady=2)
        self.nye = ttk.Entry(self, width=1)
        self.nye.grid(row=2, column=3, sticky=fillcell, pady=2)

        ttk.Label(
            self, text='n_img:', style="Config.TLabel", anchor=tk.E).grid(
                row=2, column=4, sticky=fillcell, pady=2)
        self.nimge = ttk.Entry(self, width=1)
        self.nimge.grid(row=2, column=5, sticky=fillcell, pady=2)

        ttk.Label(
            self, text='Z-spacing:', style="Config.TLabel", anchor=tk.E).grid(
                row=2, column=6, columnspan=2, sticky=fillcell, pady=2)
        self.zspe = ttk.Entry(self, width=1)
        self.zspe.grid(row=2, column=8, columnspan=2, sticky=fillcell, pady=2)

        self.update_btn = ttk.Button(
            self, text="write/update", style="Config.TButton")
        self.update_btn.bind("<Button-1>", self.updatebtn_cb)
        self.update_btn.grid(
            row=3, column=0, columnspan=5, sticky=fillcell, padx=2, pady=2)

        self.read_btn = ttk.Button(
            self, text="read file", style="Config.TButton")
        self.read_btn.bind("<Button-1>", self.readbtn_cb)
        self.read_btn.grid(
            row=3, column=5, columnspan=5, sticky=fillcell, padx=2, pady=2)

        if self.parent.config:
            self.update_entry_fields()

    def updatebtn_cb(self, event):
        """Updates config values and writes updates to file

        Args:
            event: information on the event that triggered this
        """
        if not self.parent.config:
            self.parent.messagearea.set_text(
                "There is not existing configuration to update. " +
                "Nothing written")
            return

        tmp_fname = str(self.filee.get())
        if " " in tmp_fname:
            self.parent.messagearea.set_text(
                "file name cannot contain spaces. Nothing written.")
            self.filee.delete(0, tk.END)
            self.filee.insert(0, "")
            self.update()
        else:
            if self.update_config():
                self.parent.config.write()
                self.parent.messagearea.set_text(
                    "parameters saved to " + tmp_fname)

    def update_config(self):
        """Updates all config values to current values held in text fields

        Returns:
            Boolean indicating whether update operation was successful
        """
        if not self.parent.config:
            self.parent.messagearea.set_text(
                "There is no existing config to update. Nothing written")
            return False

        nx = int(self.nxe.get())
        ny = int(self.nye.get())
        samps = int(self.sampse.get())

        if nx <= 1 or ny <= 1:
            self.parent.messagearea.set_text(
                "NX and NY must be greater than 1")
            return False

        if samps < 1:
            self.parent.messagearea.set_text("Samps must be greater than 0")
            return False

        self.parent.config.fname = str(self.filee.get())
        self.parent.config.nx = nx
        self.parent.config.ny = ny
        self.parent.config.samps = samps
        self.parent.config.nimages = int(self.nimge.get())
        self.parent.config.zstep = float(self.zspe.get())
        self.parent.config.sID = str(self.sIDe.get())
        self.parent.config.nroot = str(self.pIDe.get())
        self.parent.messagearea.set_text("parameter values up to date")
        return True

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
        xmax, ymax, zmax = 160., 118., 29.3
        fracbelow = 0.5
        camera_delay = 0.2
        self.microscope = Microscope(
            self.config, xmax, ymax, zmax, fracbelow, camera_delay)

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
        fill_horizontal = tk.E + tk.W
        separationpad = 3
        self.messagearea.grid(sticky=fill_horizontal)
        self.translationtool.grid(
            sticky=fill_horizontal, pady=(separationpad, 0))
        self.calibrationandhardware.grid(
            sticky=fill_horizontal, pady=(separationpad, 0))
        self.movementandimaging.grid(
            sticky=fill_horizontal, pady=(separationpad, 0))
        self.configurationtool.grid(
            sticky=fill_horizontal, pady=(separationpad, 1), padx=3)

        self.update()
        self.microscope.camera_window = (
            0, 0, self.parent.winfo_screenwidth() - self.parent.winfo_width(),
            self.parent.winfo_screenheight()) # Set camera window size

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
            if self.config is None:
                self.config = Config(fname)
            else:
                self.config.fname = fname
                self.config.read()
        except ValueError:
            print("Configuration file does not exist. Creating one...")
            Config.write_default_config("AMi.config")
            self.config = Config("AMi.config")
        except Exception: # pylint: disable=broad-except
            Config.print_help()
            sys.exit() # invalid configuration format. Quit program.

    def mcoords(self, newcol, newrow, newsamp=0):
        """Communicates moves to the microscope and updates GUI window to
        reflect the new position of the microscope.
        """
        self.microscope.xcol = newcol
        self.microscope.yrow = newrow
        self.microscope.samp = newsamp
        mx, my, mz = self.microscope.mcoords()

        if self.config.samps > 1:
            position_str = self.config.get_name_with_subsample(
                newrow, newcol, newsamp)
        else:
            position_str = self.config.get_sample_name(newrow, newcol)

        self.movementtool.pose.delete(0, tk.END)
        self.movementtool.pose.insert(0, position_str)
        self.movementtool.update()

        message = "showing {} position {}\n".format(
            position_str, newrow*self.config.nx + newcol+1)
        message += "machine coordinates: {}, {}, {}".format(
            round(mx, 3), round(my, 3), round(mz, 3))
        self.messagearea.set_text(message)

    def close(self):
        """Performs closing procedures
        """
        print('moving back to the origin and ' +
              'closing the graphical user interface')
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
    """Main program controller
    """
    print('\n Bonjour, ami \n')
    if not os.path.isdir("images"): # check to be sure images directory exists
        print('"images" directory (or symbolic link) not found. \n' +
              'This should be in the same directory as this program. \n' +
              'You need to create the directory or fix the link before ' +
              'continuing. \n' + 'i.e. mkdir images')
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

    # for selfresizing:
    # https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
    frame = GUI(root, background="white")
    frame.pack(side="top", fill="both", expand=True)
    frame.messagearea.set_text(
        "The corner samples must be centered and in focus before imaging. " +
        "Use blue buttons to check alignment, and XYZ windows to make " +
        "corrections. Good luck!!")

    root.update()
    root.geometry("{}x{}+{}+{}".format(
        root.winfo_width(), root.winfo_height(),
        root.winfo_screenwidth() - root.winfo_width(), 0))
    root.mainloop()

    # After close
    print('\n Hope you find what you\'re looking for!  \n')

if __name__ == "__main__":
    main()
