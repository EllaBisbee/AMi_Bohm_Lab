from tkinter import *

class MessageArea(Frame):
    def __init__(self, parent, text, wraplength=None):
        Frame.__init__(self, parent, highlightbackground="black", 
                                     highlightthickness=1)
        self.text = StringVar()
        self.text.set(text)
        self.label = Label(self, textvariable=self.text)
        if wraplength:
            self.label.config(wraplength=wraplength)
        self.label.pack()

    def setText(self, t):
        self.text.set(t)

#https://stackoverflow.com/questions/22835289/how-to-get-tkinter-canvas-to-dynamically-resize-to-window-width/22835732
class TranslationTool(Frame):
    bcolor = "darkblue"
    bwidth = 2

    def __init__(self, parent):
        Frame.__init__(self, parent, pady=1, highlightthickness=0)
        self.update()
        Grid.rowconfigure(self, 0, weight=1)
        for i in range(10):
            Grid.columnconfigure(self, i, weight=1)

        self.zsetting = Frame(self, highlightthickness=0)
        self.zsetting.rowconfigure(0, weight=1)
        self.zsetting.columnconfigure(0, weight=1)
        self.zsettingCanvas = Canvas(self.zsetting, width=1, height=1, highlightthickness=0, bg="lightgrey")
        self.zsettingCanvas.bind("<Configure>", self.onResize)
        self.zsettingCanvas.grid(row=0, column=0, sticky=N+E+S+W)
        self.zsetting.grid(row=0, column=0, sticky=W+E, padx=1)

        self.xysetting = Frame(self, highlightthickness=0)
        self.xysetting.rowconfigure(0, weight=1)
        self.xysetting.columnconfigure(0, weight=1)
        self.xysettingCanvas = Canvas(self.xysetting, width=1, height=1, highlightthickness=0, bg="lightgrey")
        self.xysettingCanvas.grid(sticky=N+E+S+W)
        self.xysetting.grid(row=0, column=1, columnspan=9, sticky=W+E, padx=1)

        self.redraw()

    def onResize(self, event):
        self.redraw()
    
    def redraw(self):
        spacing = 40 # spacing between lines and ovals
        linescuttoff = 10 # cutoff on either side of internal lines in zsetting
        color = "red" # color of spacing and ovals
        fontname = "Helvetia" # label font name
        fontsize = 12 # label font size
        fonteffect = "bold" # label font effect 
        labelfont = (fontname, fontsize, fonteffect)
        labelcolor = self.bcolor

        # renaming variable for local use
        zsetting = self.zsettingCanvas
        xysetting = self.xysettingCanvas

        # calculate window size
        zdim = {
            "w": self.zsetting.winfo_width(),
            "h": self.xysetting.winfo_width()
        }
        xydim = {
            "w": self.xysetting.winfo_width(),
            "h": self.xysetting.winfo_width()
        }

        # create zsetting
        zsetting.delete("all")
        zsetting.config(width=zdim["w"], height=zdim["h"])
        zsetting.create_rectangle(1,1,zdim["w"]-1,zdim["h"]-1, outline=self.bcolor, width=self.bwidth)
        zsetting.create_line(0,zdim["h"]/2, zdim["w"], zdim["h"]/2, width=2)
        for i in range(1, int(zdim["h"]/2/spacing) + 1): #z lines
            zsetting.create_line(linescuttoff, zdim["h"]/2 - i * spacing,
                                 zdim["w"] - linescuttoff, zdim["h"]/2 - i * spacing,
                                 fill=color)
            zsetting.create_line(linescuttoff, zdim["h"]/2 + i * spacing,
                                 zdim["w"] - linescuttoff, zdim["h"]/2 + i * spacing,
                                 fill=color)
        zsetting.create_text(zdim["w"]/2 - fontsize/2,0,fill=labelcolor,font=labelfont,text="+Z",anchor=NW)
        zsetting.create_text(zdim["w"]/2 - fontsize/2,zdim["h"],fill=labelcolor,font=labelfont,text="-Z",anchor=SW)

        xysetting.delete("all")
        xysetting.config(width=xydim["w"], height=xydim["h"])
        xysetting.create_rectangle(1,1,xydim["w"]-1,xydim["h"]-1, outline=self.bcolor, width=self.bwidth)
        xysetting.create_line(xydim["w"]/2,0,xydim["w"]/2,xydim["h"], width=2) #xy vertical
        xysetting.create_line(0, xydim["h"]/2, xydim["w"], xydim["h"]/2, width=2) #xy horizontal
        for i in range(1, int(xydim["w"]/2/spacing) + 1): #xy circles
            xysetting.create_oval(xydim["w"]/2 - i * spacing, xydim["h"]/2 - i * spacing,
                                  xydim["w"]/2 + i * spacing, xydim["h"]/2 + i * spacing,
                                  outline=color)
        xysetting.create_text(xydim["w"]/2,0,fill=labelcolor,font=labelfont,text="+Y", anchor=NW)
        xysetting.create_text(xydim["w"]/2,xydim["h"], fill=labelcolor,font=labelfont, text="-Y", anchor=SW)
        xysetting.create_text(2,xydim["h"]/2, fill=labelcolor,font=labelfont, text="-X", anchor=SW)
        xysetting.create_text(xydim["w"],xydim["h"]/2, fill=labelcolor,font=labelfont, text="+X", anchor=SE)

class CalibrationTool(Frame):
    locationButtonColor = "skyblue1"
    locationButtonFont = "Helvetia 12"
    locationButtonActive = "green"
    setButtonColor = "yellow"
    setButtonFont = "Helvetia 12 bold"
    setButtonActive = "green"
    def __init__(self, parent):
        Frame.__init__(self, parent, highlightbackground="black", 
                                     highlightthickness=3, 
                                     background="lightgrey")
        self.update()
        # Configure Grid for self-resizing
        for row in range(3):
            Grid.rowconfigure(self, row, weight=1)
        for col in range(4):
            Grid.columnconfigure(self, col, weight=1)

        # location buttons
        locationButtons = []
        # Top-left
        self.tlButton = Button(self, text="TL")
        self.tlButton.grid(row=0, column=0, columnspan=2, sticky=N+E+S+W)
        locationButtons.append(self.tlButton)

        # Top-right
        self.trButton = Button(self, text="TR")
        self.trButton.grid(row=0, column=2, columnspan=2, sticky=N+E+S+W)
        locationButtons.append(self.trButton)

        # Bottom-left
        self.blButton = Button(self, text="BL")
        self.blButton.grid(row=2, column=0, columnspan=2, sticky=N+E+S+W)
        locationButtons.append(self.blButton)

        # Bottom-right
        self.brButton = Button(self, text="BR")
        self.brButton.grid(row=2, column=2, columnspan=2, sticky=N+E+S+W)
        locationButtons.append(self.brButton)

        for btn in locationButtons:
            btn.config(font=self.locationButtonFont, bg=self.locationButtonColor,
                       activebackground=self.locationButtonActive)

        # set button
        self.setButton = Button(self, text="SET", bg=self.setButtonColor,
                                activebackground=self.setButtonActive,
                                font=self.setButtonFont)
        self.setButton.grid(row=1, column=1, columnspan=2, sticky=N+E+S+W)

windowwidth = 320
windowheight = 0
root = Tk()
root.title('AMiGUI v1.0')
root.minsize(windowwidth,windowheight)
root.update()

# for selfresizing: https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
Grid.rowconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 0, weight=1)

master = Frame(root)
master.grid(row=0, column=0, sticky=N+S+E+W)

Grid.rowconfigure(master, 0, weight=1)
Grid.columnconfigure(master, 0, weight=1)
topMessage = MessageArea(master, "Welcome AMi!", wraplength=windowwidth)
topMessage.grid(sticky=E+W)

Grid.rowconfigure(master, 1, weight=1)
translationTool = TranslationTool(master)
translationTool.grid(sticky=E+W)
translationTool.update()
translationTool.redraw()

Grid.rowconfigure(master, 2, weight=1)
Grid.columnconfigure(master, 1, weight=1)
calibrationTool = CalibrationTool(master)
calibrationTool.grid(column=0, sticky=E+W)

root.mainloop()