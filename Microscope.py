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
    

    Attributes
    ----------
    xcol        : Sample position (x)
    yrow        : Sample position (y)
    samp        : Sub-sample index (used when there is more than one sample in each well)
    mx          : Machine position (x)
    my          : Machine position (y)
    mz          : Machine position (z)
    viewing     : Live preview of machine camera
    running     : TODO: what is this?
    camera      : TODO: description for this
    light1      : GPIO channel for Light 1
    light2      : GPIO channel for Light 2
    arduinopwr  : GPIO channel for arduino power
    arduinomvmt : GPIP channel for arduino movement flag
    s           : TODO: description for this, serial port control?
    _sname      : serial port name
    _baudrate   : serial port bit rate
    wx          : CNC Work position (x)
    wy          : CNC Work position (y)
    wz          : CNC Work position (z)
    """
    def __init__(self):
        self.xcol = 0
        self.yrow = 0
        self.samp = 0
        self.mx = 0
        self.my = 0
        self.mz = 0
        self.viewing = False
        self.running = False

        # Camera setup
        self.camera = PiCamera()
        self.camera.resolution = (1640, 1232) #TODO: make this a parameter?
        self.camera.iso = 50 # not sure this does anything TODO: make this a parameter?

        # GPIO Controls
        self.light1 = 17
        self.light2 = 18
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
            # respond as if "?" had been requested
            return "<Idle,MPos:0.000,0.000,0.000,WPos:0.000,0.000,0.000>\r".encode('utf-8')
        else:
            return self.s.readline()

    def mcoords(self):
        print("Moving to cell")