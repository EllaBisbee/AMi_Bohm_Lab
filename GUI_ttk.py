import tkinter as tk
from tkinter import ttk

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
        self.parent = parent
        self.configureRows(3)
        self.configureColumns(4)

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        btnwidth = 0
        style = ttk.Style()
        style.configure("Calibration.TButton", font="Helvetia 12", background="skyblue1")
        style.map("Calibration.TButton", background=[('active', 'green'), ('pressed', 'green')])
        # Top-left
        self.tlButton = ttk.Button(self, text="TL", style="Calibration.TButton", width=btnwidth)
        self.tlButton.grid(row=0, column=0, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Top-right
        self.trButton = ttk.Button(self, text="TR", style="Calibration.TButton", width=btnwidth)
        self.trButton.grid(row=0, column=2, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Bottom-left
        self.blButton = ttk.Button(self, text="BL", style="Calibration.TButton", width=btnwidth)
        self.blButton.grid(row=2, column=0, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # Bottom-right
        self.brButton = ttk.Button(self, text="BR", style="Calibration.TButton", width=btnwidth)
        self.brButton.grid(row=2, column=2, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        # set button
        style.configure("Calibration-Set.TButton", font="Helvetia 12 bold", background="yellow")
        style.map("Calibration-Set.TButton", background=[('active', 'green'), ('pressed', 'green')])
        self.setButton = ttk.Button(self, text="SET", style="Calibration-Set.TButton", width=btnwidth)
        self.setButton.grid(row=1, column=1, columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

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
        self.parent = parent
        self.configureRows(3)
        self.configureColumns(2)

        fillcell = tk.N + tk.E + tk.S + tk.W
        btnpad = 1
        style = ttk.Style()
        style.configure('LiveView.TButton', font="Helvetia 12 bold", foreground="black", background="orange")
        style.map('LiveView.TButton', background=[('active', 'green'), ('pressed', 'green')])
        self.viewButton = ttk.Button(self, text="VIEW", style="LiveView.TButton")
        self.viewButton.grid(columnspan=2, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.resetButton = ttk.Button(self, text="reset origin")
        self.resetButton.grid(row=1, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)
        
        self.closeButton = ttk.Button(self, text="stop/close")
        self.closeButton.grid(row=1, column=1, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light1Button = ttk.Button(self, text="light1")
        self.light1Button.grid(row=2, column=0, sticky=fillcell, pady=btnpad, padx=btnpad)

        self.light2Button = ttk.Button(self, text="light2")
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
        self.parent = parent
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
        self.gotoButton.grid(row=0, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.pose = ttk.Entry(self, width=width)
        self.pose.insert(0, "A1")
        self.pose.grid(row=0, column=1, sticky=fillcell, pady=pady, padx=padx)

        self.prevButton = ttk.Button(self, text="prev", style="Movement.TButton", width=width)
        self.prevButton.grid(row=1, column=0, sticky=fillcell, pady=pady, padx=padx)

        self.nextButton = ttk.Button(self, text="next", style="Movement.TButton", width=width)
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

class ImagingControls(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.config(background=parent['bg'])
        self.parent = parent
        self.configureRows(2)
        self.configureColumns(1)

        fillcell = tk.N + tk.E + tk.S + tk.W
        style = ttk.Style()
        style.map('ActvGreen.TButton', background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Img-Snp.ActvGreen.TButton', font="Helvetia 12 bold", foreground="white", background="medium blue")
        style.configure('Img-Run.ActvGreen.TButton', font="Helvetia 12 bold", foreground="yellow", background="black")

        self.snapButton = ttk.Button(self, text="SNAP IMAGE", style="Img-Snp.ActvGreen.TButton")
        self.snapButton.grid(sticky=fillcell, pady=(0,5))

        self.runButton = ttk.Button(self, text="RUN", style="Img-Run.ActvGreen.TButton")
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
        self.configureRows(8)
        self.configureColumns(3)

        fillcell = tk.N + tk.E + tk.S + tk.W
        style = ttk.Style()
        style.configure('Config.TButton', font="Helvetia 10", width=8, background="yellow")
        style.map('Config.TButton', background=[('active', 'green'), ('pressed', 'green')])
        style.configure('Config.TLabel', background=self['bg'], font="Helvetia 10")

        self.updateButton = ttk.Button(self, text="write/update", style="Config.TButton")
        self.updateButton.grid(row=2, column=2, rowspan=2, sticky=fillcell, padx=2, pady=2)

        self.readButton = ttk.Button(self, text="read file", style="Config.TButton")
        self.readButton.grid(row=4, column=2, rowspan=2, sticky=fillcell, padx=2, pady=2)

        labels = []
        entries = []
        labels.append(ttk.Label(self, text="Filename:", style="Config.TLabel", anchor=tk.E))
        self.filee = ttk.Entry(self)
        entries.append(self.filee)

        labels.append(ttk.Label(self, text='Sample ID:', style="Config.TLabel"))
        self.sIDe = ttk.Entry(self)
        entries.append(self.sIDe)

        labels.append(ttk.Label(self, text='Plate ID:', style="Config.TLabel"))
        self.pIDe = ttk.Entry(self)
        entries.append(self.pIDe)

        labels.append(ttk.Label(self, text='nx:', style="Config.TLabel"))
        self.nxe = ttk.Entry(self, width=3)
        entries.append(self.nxe)

        labels.append(ttk.Label(self, text='ny:', style="Config.TLabel"))
        self.nye = ttk.Entry(self, width=3)
        entries.append(self.nye)

        labels.append(ttk.Label(self, text='samples/pos:', style="Config.TLabel"))
        self.sampse = ttk.Entry(self, width=3)
        entries.append(self.sampse)

        labels.append(ttk.Label(self, text='n_images:', style="Config.TLabel"))
        self.nimge = ttk.Entry(self, width=3)
        entries.append(self.nimge)

        labels.append(ttk.Label(self, text='Z-spacing:', style="Config.TLabel"))
        self.zspe = ttk.Entry(self, width=3)
        entries.append(self.zspe)

        fillcell = tk.N + tk.E + tk.S + tk.W
        for i, label in enumerate(labels):
            label.config(anchor=tk.E)
            label.grid(row=i, column=0, sticky=fillcell, pady=2)
            entries[i].config(width=0)
            entries[i].grid(row=i, column=1, sticky=fillcell, pady=2)
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

class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.configureRows(5)
        self.configureColumns(1)
        self.parent = parent
        
        self.messagearea = MessageArea(self, text="Welcome AMi!")
        self.translationtool = TranslationTool(self)
        self.calibrationandhardware = CalibrationAndHardware(self)
        self.calibrationtool = self.calibrationandhardware.calibrationtool
        self.hardwarecontrols = self.calibrationandhardware.hardwarecontrols
        self.movementandimaging = MovementAndImaging(self)
        self.movementtool = self.movementandimaging.movementtool
        self.imagingcontrols = self.movementandimaging.imagingcontrols
        self.configurationtool = ConfigurationTool(self)

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

def main():
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

if __name__ == "__main__":
    main()