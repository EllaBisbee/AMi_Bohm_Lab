"""Controls interactions with the adapted CNC Machine.

This file contains the classes to control interactions with the adapted
CNC Machine for AMi.
"""

import pty
import os
from time import sleep
import RPi.GPIO as GPIO
from picamera import PiCamera

from GRBL import GRBL

class Microscope():
    """Handles all external interactions with the CNC Machine.

    This class provides all the necessary functions to interact with the CNC
    Machine and attached hardware.

    Attributes:
        config: Configuration object for information on the tray/
        xcol: An Integer indicating the current sample position (x)
        yrow: An Integer indicating the current sample position (y)
        samp: An Integer indicating the current sub-sample index within well
        mx: An Integer indicating the current machine position (x)
        my: An Integer indicating the current machine position (y)
        mz: An Integer indicating the current machine position (z)
        xmax: A Float indicating the translation limit (x) in mm
        ymax: A Float indicating the translation limit (y) in mm
        zmax: A Float indicating the translation limit (z) in mm
        viewing: A Boolean indicating whether live preview is active
        running: A Boolean indicating whether the program is collecting images
        stopit: A Boolean that cancels the collection of images
        camera: Camera object for interacting with the microscope camera
        light1: An integer for the GPIO channel for Light 1
        light1_stat: A Boolean indicating the On/Off state of light 1
        light2: An integer for the GPIO channel for Light 2
        light2_stat: A Boolean indicating the On/Off state of light 2
        arduinopwr: An integer for the GPIO channel for 24V arduino power
        arduinomvmt: An integer for the GPIO channel for arduino movement flag
        s: Serial object for sending GRBL commands to the arduino
        wx: A Float indicating the CNC Work position (x)
        wy: A Float indicating the CNC Work position (y)
        wz: A Float indicating the CNC Work position (z)
        fracbelow: A Float indicating the fraction of zrange below the
            expected plane of focus
        camera_delay: A Float indicating the delay, in seconds, that the system
            should sit idle before each image
        disable_hard_limits: A Boolean indicating whether to disable
            hard limits of the CNC Machine during RUN only
        camera_window: 4 Tuple indicate x,y location and width,height of camera
            window when previewing
    """
    def __init__(self, config, xmax, ymax, zmax, fracbelow, camera_delay):
        """Inits Microscope with given config object"""
        self.xcol = 0
        self.yrow = 0
        self.samp = 0
        self.mx = 0
        self.my = 0
        self.mz = 0
        self.xmax = xmax
        self.ymax = ymax
        self.zmax = zmax
        self.viewing = False
        self.running = False
        self.stopit = False
        self.fracbelow = fracbelow
        self.camera_delay = camera_delay
        self.disable_hard_limits = True
        self.config = config
        self.camera_window = None

        # Camera setup. Change if new camera is purchased
        self.camera = PiCamera()
        self.camera.resolution = (1640, 1232)
        self.camera.iso = 50 # not sure this does anything

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
        portname = None
        baudrate = 115200
        if self._in_dev_machine():
            _, slave = pty.openpty()
            portname = os.ttyname(slave) # dummy name (DEVELOMENT)
        else:
            portname = '/dev/ttyUSB0' # real name (PRODUCTION)
        baudrate = 115200
        self.grbl = GRBL(portname, baudrate)
        if self._in_dev_machine():
            self.grbl.custom_wait_for_response(self.grbl_response)

        self.grbl.hard_limits(True)
        print(' ok so far...')
        self.grbl.run_homing_cycle() # tell grbl to find zero
        self.wx, self.wy, self.wz = self.grbl.get_work_position()
        if self.wx == -199.0:
            # ensures that zero is zero and not -199.0, -199.0, -199.0
            self.grbl.set_coordinate_system(1, self.wx, self.wy, self.wz)
        # set pin A3 high -used later to detect end of movement
        self.grbl.coolant_control(flood=True)
        print(" You\'ll probably want to click VIEW and turn on some lights " +
              "at this point. \n Then you may want to check the alignment of " +
              "the four corner samples")
        # unlock so spindle power can engage for light2
        self.grbl.kill_alarm_lock()
        self.grbl.set_spindle_speed(1000) # set max spindle volocity

    def get_machine_position(self):
        """Returns the current position of the machine as [x, y, z]

        Returns the current position of the machine as a python list
        ordered in the usual manner --> x, y, z
        """
        return [self.mx, self.my, self.mz]

    def switch_camera_preview(self):
        """Alters the live preview state of the camera.

        Changes the live preview state of the program. If live preview is on,
        this function turns it off and vice versa.
        """
        if self.viewing:
            self.camera.stop_preview()
            self.viewing = False
        else:
            self.camera.start_preview(
                fullscreen=False, window=self.camera_window)
            self.viewing = True

    def _in_dev_machine(self):
        """Determines if program is in development

        Determines if the program is running in development on a machine not
        connected to the microscope. This is determined by environment
        variables DEV and ONMACHINE set by the user.

        Returns:
            A boolean indicating whether this program is running in development
        """
        return os.getenv("DEV") == "true" and os.getenv("ONMACHINE") == "false"

    def grbl_response(self):
        """Waits for a response from grbl

        Waits for Grbl to respond with an OK or ERROR message. This
        signals that Grbl has completed parsing and executing the command
        send immediately before calling this. If the program is in dev
        mode, this function simulates a fake response as if the "?" query
        had been sent.

        Returns:
            A carriage-return terminated response from grbl or a dummy
            response if the program is in development.
        """
        if self._in_dev_machine():
            sleep(1)
            return "<Idle,MPos:0.0,0.0,0.0,WPos:0.0,0.0,0.0>".encode('utf-8')
        else:
            return self.grbl.default_wait_for_response()

    def wait_for_idle(self):
        """Waits for Arduino to complete movement
        """
        self.grbl.coolant_control(flood=False) # set pin A3 low
        while GPIO.input(self.arduinomvmnt):
            sleep(0.1)
        self.grbl.coolant_control(flood=True) # set pin A3 high

    def toggle_light1(self):
        """Light switch for light1

        Turns light1 on/off depending on its current state
        """
        if self.light1_stat:
            GPIO.output(self.light1, GPIO.LOW)
            self.light1_stat = False
            print("light1 turned off")
        else:
            GPIO.output(self.light1, GPIO.HIGH)
            self.light1_stat = True
            print("light1 turned on")

    def toggle_light2_arduino(self):
        """Light switch for light2

        Turns light2 on/off depending on its current state.
        Also controls the 24V output of the arudino.
        """
        if self.light2_stat:
            GPIO.output(self.light2, GPIO.LOW)
            self.light2_stat = False
            self.grbl.spindle_control(running=False) # turn off spindle power
            print("light2 turned off")
        else:
            GPIO.output(self.light2, GPIO.HIGH)
            self.light2_stat = True
            self.grbl.spindle_control(clockwise=True) # turn on spindle power
            print("light2 turned on")

    def mcoords(self):
        """Sends a movement message to grbl to match internal settings

        Calculates the desired machine location based on internal sample
        location and sends a move signal to grbl.

        Returns:
            The new mx, my, mz machine positions
        """
        print("called mcoords with yrow,xcol,samp:",
              self.yrow, self.xcol, self.samp)
        self.wait_for_idle()
        self.mx, self.my, self.mz = self.calculate_machine_position(
            self.xcol, self.yrow, self.samp)
        print('mx,my,mz', self.mx, self.my, self.mz) # TODO: does this need to be here?
        self.grbl.rapid_move(self.mx, self.my, self.mz)
        self.wait_for_idle()
        return self.mx, self.my, self.mz

    def calculate_machine_position(self, col, row, samp):
        """Returns the x,y,z machine positions based on the given sample coords

        Uses bilinear interpolation to calculate the x,y,z machine poisition
        for the given sample coordinates.
        https://en.wikipedia.org/wiki/Bilinear_interpolation

        Returns:
            The [x,y,z] machine positions
        """
        # Pull in necessary variables
        br, bl = self.config.br, self.config.bl
        tr, tl = self.config.tr, self.config.tl

        # Calculate fractional location of sample
        x = (col / float(self.config.nx - 1) +
             self.config.samp_coord[samp][0])
        y = (row / float(self.config.ny - 1) +
             self.config.samp_coord[samp][1])

        # Interpolate
        mx = br[0]*x*y + bl[0]*(1.-x)*y + tr[0]*x*(1.-y) + tl[0]*(1.-x)*(1.-y)
        my = br[1]*x*y + bl[1]*(1.-x)*y + tr[1]*x*(1.-y) + tl[1]*(1.-x)*(1.-y)
        mz = br[2]*x*y + bl[2]*(1.-x)*y + tr[2]*x*(1.-y) + tl[2]*(1.-x)*(1.-y)
        return mx, my, mz
