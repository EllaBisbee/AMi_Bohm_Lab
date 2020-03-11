import serial
import numpy as np
#import RPi.GPIO as GPIO
import re, sys, os
from time import sleep
from datetime import datetime
from shutil import copyfile
#from picamera import PiCamera

from Config import Config
from GUI_Helper import *

def main():
    print('\n Bonjour, ami \n')
    if not os.path.isdir("images"): # check to be sure images directory exists
        print('"images" directory (or symbolic link) not found. \n' +
             'This should be in the same directory as this program. \n' +
             'You need to create the directory or fix the link before continuing. \n' +
             'i.e. mkdir images')
        sys.exit()
    config = read_config()

    # camera setup
    ###camera = PiCamera()
    ###camera.resolution=(1640,1232)
    ###camera.iso=50 # nnot sure this does anytihng

    #light1 and light2 setup - this is controled by gpio pins 17 and 18 on the pi
    #the light2 button also controls the 24V output of the arduino
    #gpio 27 is used to tell the pi when the arduino has fininished moving
    ###GPIO.setmode(GPIO.BCM)
    ###GPIO.setwarnings(False)
    ###GPIO.setup(17,GPIO.OUT) #controls light 1
    ###GPIO.setup(18,GPIO.OUT) #controls light 2
    ###GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # signal for movement completion

    # connect to the arduino and set zero 
    """
    s = serial.Serial('/dev/ttyUSB0',115200) # open grbl serial port
    s.write(("\r\n\r\n").encode('utf-8')) # Wake up grbl
    sleep(2)   # Wait for grbl to initialize
    s.flushInput()  # Flush startup text in serial input
    s.write(('$21=1 \n').encode('utf-8')) # enable hard limits
    print(' ok so far...')
    s.write(('$H \n').encode('utf-8')) # tell grbl to find zero 
    grbl_out = s.readline() # Wait for grbl response with carriage return
    s.write(('? \n').encode('utf-8')) # Send g-code block to grbl
    response = s.readline().decode('utf-8') # Wait for grbl response with carriage return
    response=response.replace(":",","); response=response.replace(">",""); response=response.replace("<","")
    a_list=response.split(",")
    #print(a_list)
    wx=float(a_list[6]); wy=float(a_list[7]); wz=float(a_list[8])
    if wx==-199.0:
        s.write(('G10 L2 P1 X '+str(wx)+' Y '+str(wy)+' Z '+str(wz)+' \n').encode('utf-8')) # ensures that zero is zero and not -199.0, -199.0, -199.0 
        grbl_out = s.readline() # Wait for grbl response with carriage return
    s.write(('m8 \n').encode('utf-8')) # set pin A3 high -used later to detect end of movement 
    print(' You\'ll probably want to click VIEW and turn on some lights at this point. \n Then you may want to check the alignment of the four corner samples')
    s.write(('$x \n').encode('utf-8')) # unlock so spindle power can engage for light2 
    grbl_out = s.readline() # Wait for grbl response with carriage return
    s.write(('s1000 \n').encode('utf-8')) # set max spindle volocity
    grbl_out = s.readline() # Wait for grbl response with carriage return
    """

    # set up the canvas
    windowwidth = 200
    windowheight = 0
    root = Tk()
    root.title('AMiGUI v1.0')
    root.update()
    print(root.winfo_screenheight())
    root.minsize(windowwidth,windowheight)
    root.update()

    # for selfresizing: https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
    Grid.rowconfigure(root, 0, weight=1)
    Grid.columnconfigure(root, 0, weight=1)

    master = Frame(root)
    master.configure(background='white')
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

    ### Calibration and Controls
    Grid.rowconfigure(master, 2, weight=1)
    calibrationAndControls = Frame(master, background=master['bg'], pady=3)
    calibrationAndControls.grid(sticky=E+W)
    Grid.rowconfigure(calibrationAndControls, 0, weight=1)
    Grid.columnconfigure(calibrationAndControls, 0, weight=1)
    Grid.columnconfigure(calibrationAndControls, 1, weight=1)

    calibrationTool = CalibrationTool(calibrationAndControls)
    calibrationTool.grid(row=0, column=0, sticky=E+W)

    generalControls = GeneralControls(calibrationAndControls)
    generalControls.grid(row=0, column=1, sticky=E+W)

    ## Movement and Imaging
    Grid.rowconfigure(master, 3, weight=1)
    movementAndImaging = Frame(master, background=master['bg'], pady=3)
    movementAndImaging.grid(sticky=E+W)
    Grid.rowconfigure(movementAndImaging, 0, weight=1)
    Grid.columnconfigure(movementAndImaging, 0, weight=1)
    Grid.columnconfigure(movementAndImaging, 1, weight=1)

    movementTool = MovementTool(movementAndImaging)
    movementTool.grid(row=0, column=0, sticky=E+W)

    imagingControls = ImagingControls(movementAndImaging)
    imagingControls.grid(row=0, column=1, sticky=E+W)

    ## Auto-imaging
    Grid.rowconfigure(master, 4, weight=1)
    autoimaging = AutoImagingTool(master, config=config, messagearea=topMessage)
    autoimaging.grid(sticky=E+W)

    # start message
    topMessage.setText("The corner samples must be centered and in focus before imaging. Use blue buttons to check alignment, and XYZ windows to make corrections. Good luck!!")

    root.mainloop()

    # Exit procedures
    print('\n Hope you find what you\'re looking for!  \n')
    """GPIO.output(17, GPIO.LOW) #turn off light1
    GPIO.output(18, GPIO.LOW) #turn off light2
    s.write(('m5 \n').encode('utf-8')) #turn off light2
    s.close() # Close serial port 
    camera.stop_preview() # stop preview"""


def read_config(fname='AMi.config'):  # read information from the configuration file
    config = None
    try:
        config = Config(fname)
    except:
        Config.print_help()
        if fname=='AMi.config': sys.exit() #TODO: what does this do?

    return config
    
if __name__ == "__main__":
    main()