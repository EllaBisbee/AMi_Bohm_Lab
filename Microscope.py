"""
Microscope handles all aspects of external interactions with the microscope unit

Andrew Bohm, Ella Bisbee, Ramon Fernandes
Version 0.0.1
"""

from picamera import PiCamera
import RPi.GPIO as GPIO
import serial, pty, os
from time import sleep

class Microscope():
    """
    CLASS DESCRIPTION HERE

    Parameters
    ----------
    config      : configuration object

    Attributes
    ----------
    config      : configuration object
    xcol        : Sample position (x)
    yrow        : Sample position (y)
    samp        : Sub-sample index (used when there is more than one sample in each well)
    mx          : Machine position (x)
    my          : Machine position (y)
    mz          : Machine position (z)
    xmax        : translation limit (x) in mm
    ymax        : translation limit (y) in mm
    zmax        : translation limit (z) in mm
    viewing     : Live preview of machine camera
    running     : Program is collecting images
    stopit      : Trigger to cancel collection of images
    camera      : TODO: description for this
    light1      : GPIO channel for Light 1
    light1_stat : On/Off state of light 1
    light2      : GPIO channel for Light 2
    light2_stat : On/Off state of light 2
    arduinopwr  : GPIO channel for arduino power
    arduinomvmt : GPIP channel for arduino movement flag
    s           : TODO: description for this, serial port control?
    _sname      : serial port name
    _baudrate   : serial port bit rate
    wx          : CNC Work position (x)
    wy          : CNC Work position (y)
    wz          : CNC Work position (z)
    fracbelow   : this is the fraction of zrange below the expected plane of focus
    camera_delay: delay, in seconds, that the system should sit idle before each image
    disable_hard_limits : this disables hard limits RUN only
    """
    def __init__(self, config):
        self.xcol = 0
        self.yrow = 0
        self.samp = 0
        self.mx = 0
        self.my = 0
        self.mz = 0
        self.xmax = 160.
        self.ymax = 118.
        self.zmax = 29.3
        self.viewing = False
        self.running = False
        self.stopit = False
        self.fracbelow = 0.5
        self.camera_delay = 0.2
        self.disable_hard_limits = True
        # TODO: Maybe config could live inside microscope and GUI could pull config from here?
        self.config = config

        # Camera setup
        self.camera = PiCamera()
        self.camera.resolution = (1640, 1232) #TODO: make this a parameter?
        self.camera.iso = 50 # not sure this does anything TODO: make this a parameter?

        # GPIO Controls
        self.light1 = 17
        self.light1_stat = False
        self.light2 = 18
        self.light2_stat = False
        self.arduinopwr = 18
        self.arduinomvmnt = 27
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.light1, GPIO.OUT)
        GPIO.setup(self.light2, GPIO.OUT)
        GPIO.setup(self.arduinomvmnt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Connect to the arduino and set zero
        # TODO: maybe break this up into a separate CNC Machine module?
        if self.in_dev_machine:
            master, slave = pty.openpty()
            self._sname = os.ttyname(slave) # dummy name
        else:
            self._sname = '/dev/ttyUSB0' # real name
        self._baudrate = 115200
        self.s = serial.Serial(self._sname,self._baudrate) # open grbl serial port
        self.s.write(("\r\n\r\n").encode('utf-8')) # Wake up grbl
        sleep(2) # wait for grbl to initialize
        self.s.flushInput()  # Flush startup text in serial input
        self.s.write(('$21=1 \n').encode('utf-8')) # enable hard limits
        print(' ok so far...')
        self.s.write(('$H \n').encode('utf-8')) # tell grbl to find zero 
        self.grbl_response() # Wait for grbl response with carriage return
        self.s.write(('? \n').encode('utf-8')) # Send g-code block to grbl
        response = self.grbl_response().decode('utf-8') # Wait for grbl response with carriage return
        response = response.replace(":",",")
        response = response.replace(">","")
        response = response.replace("<","")
        a_list = response.split(",")
        self.wx = float(a_list[6])
        self.wy = float(a_list[7])
        self.wz = float(a_list[8])
        if self.wx == -199.0:
            self.s.write(('G10 L2 P1 X ' + str(self.wx) + ' Y ' + str(self.wy) + ' Z ' + str(self.wz) + ' \n').encode('utf-8')) # ensures that zero is zero and not -199.0, -199.0, -199.0 
            self.grbl_response() # Wait for grbl response with carriage return
        self.s.write(('m8 \n').encode('utf-8')) # set pin A3 high -used later to detect end of movement 
        print(' You\'ll probably want to click VIEW and turn on some lights at this point. \n Then you may want to check the alignment of the four corner samples')
        self.s.write(('$x \n').encode('utf-8')) # unlock so spindle power can engage for light2 
        self.grbl_response() # Wait for grbl response with carriage return
        self.s.write(('s1000 \n').encode('utf-8')) # set max spindle volocity
        self.grbl_response() # Wait for grbl response with carriage return

    def get_machine_position(self):
        return [self.mx, self.my, self.mz]

    def switch_camera_preview(self):
        if self.viewing:
            self.camera.stop_preview()
            self.viewing = False
        else:
            self.camera.start_preview(fullscreen=False, window=(0,-76,1597,1200)) # TODO: add dynamic window calculation
            self.viewing = True

    """
    Determines is program is running in dev mode not directly on the machine
    """
    def in_dev_machine(self):
        return os.getenv("DEV") == "true" and os.getenv("ONMACHINE") == "false"

    """
    Waits for response from grbl with carriage return
    """
    def grbl_response(self):
        if self.in_dev_machine:
            # "wait" for response
            sleep(1)
            # respond as if "?" had been requested
            return "<Idle,MPos:0.000,0.000,0.000,WPos:0.000,0.000,0.000>\r".encode('utf-8')
        else:
            return self.s.readline()

    """
    wait for grbl to complete movement -new version wait for pin A8 to go low 
    """
    def wait_for_Idle(self):
        self.s.write(('m9 \n').encode('utf-8')) # set pin A3 low
        sleep(0.2) #wait a little just in case
        while GPIO.input(self.arduinomvmnt):
            sleep(0.1)
        self.s.write(('m8 \n').encode('utf-8')) # set pin A3 high

    """
    Turns light1 on if it's off, off if it's on
    """
    def toggle_light1(self):
        if self.light1_stat:
            GPIO.output(self.light1, GPIO.LOW)
            self.light1_stat = False
            print("light1 turned off")
        else:
            GPIO.output(self.light1, GPIO.HIGH)
            self.light1_stat = True
            print("light1 turned on")

    """
    Turns light2 and arduino on if it's off, off if it's on
    """
    def toggle_light2_arduino(self):
        if self.light2_stat:
            GPIO.output(self.light2, GPIO.LOW)
            self.light2_stat = False
            self.s.write(('m5 \n').encode('utf-8')) # turn off the spindle power
            self.grbl_response() # Wait for grbl response with carriage return
            print("light2 turned off")
        else:
            GPIO.output(self.light2, GPIO.HIGH)
            self.light2_stat = True
            self.s.write(('m3 \n').encode('utf-8')) #turn on spindle power
            self.grbl_response() # Wait for grbl response with carriage return
            print("light2 turned on")

    def mcoords(self):
        print("called mcoords with yrow,xcol,samp:",self.yrow,self.xcol,self.samp)
        self.wait_for_Idle()
        x = self.xcol / float(self.config.nx - 1) + self.config.samp_coord[self.samp][0]
        y = self.yrow / float(self.config.ny - 1) + self.config.samp_coord[self.samp][1]
        self.mx = self.config.br[0] * x * y + self.config.bl[0] * (1.-x) * y + self.config.tr[0] * x * (1.-y) + self.config.tl[0] * (1.-x) * (1.-y)
        self.my = self.config.br[1] * x * y + self.config.bl[1] * (1.-x) * y + self.config.tr[1] * x * (1.-y) + self.config.tl[1] * (1.-x) * (1.-y)
        self.mz = self.config.br[2] * x * y + self.config.bl[2] * (1.-x) * y + self.config.tr[2] * x * (1.-y) + self.config.tl[2] * (1.-x) * (1.-y)
        print('mx,my,mz',self.mx,self.my,self.mz)
        self.s.write(('G0 x '+str(self.mx)+' y '+str(self.my)+' z '+ str(self.mz) + ' \n').encode('utf-8')) # g-code to grbl
        sleep(0.2)
        self.grbl_response() # Wait for grbl response with carriage return
        letnum = self.config.get_sample_name(self.yrow, self.xcol)
        if self.config.samps > 1:
            letnum += self.config.get_subsample_id(self.samp)
        #pose.delete(0,tk.END); pose.insert(0,letnum) TODO: figure out how to put this back in
        self.wait_for_Idle()
        """
        canvas.create_rectangle(2,2,318,60,fill='white')
        canvas.create_text(160,20,text=("showing "+letnum+'  position '+str(yrow*config.nx+xcol+1)),font="helvetica 11")
        canvas.create_text(160,39,text=('machine coordinates:  '+str(round(mx,3))+',  '+str(round(my,3))+',  '+str(round(mz,3))),font="helvetica 9",fill="grey")
        canvas.update()""" # TODO: figure out how to put this back in
