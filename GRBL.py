"""A GRBL interface to interact with the CNC Machine

A GRBL Interface to abstractly interact with the CNC Machine
This is currently not an all-encompassing GRBL interface and includes
methods necessary for the interactions needed for this program in particular.
It is based on information gathered from the following guides and sources:
http://www.diymachining.com/downloads/GRBL_Settings_Pocket_Guide_Rev_B.pdf
https://diymachining.com/grbl-settings-101-a-how-to-guide/
https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface
http://linuxcnc.org/docs/html/gcode.html

As noted in the URLs above, this interface is based on GRBL v1.1
"""

import serial
from time import sleep

# Real-Time Commands
CYCLE_START = "~"
FEED_HOLD = "!"
CURRENT_STATUS = "?"
SOFT_RESET = "0x18" #ctrl-x

# '$' Commands
COMMAND_PREFIX = "$"
VIEW_SETTINGS = "$$"
STEP_PULSE_TIME = 0
STEP_IDLE_DELAY = 1
STEP_PULSE_CONFIG = 2
AXIS_DIRECTION = 3
STEP_ENABLE_INVERT = 4
LIMIT_PINS_INVERT = 5
PROBE_PIN_INVERT = 6
STATUS_REPORT = 10
JUNCTION_DEVIATION = 11
ARC_TOLERANCE = 12
FEEDBACK_UNITS = 13
SOFT_LIMITS = 20
HARD_LIMITS = 21
HOMING_CYCLE = 22
HOMING_CYCLE_DIRECTION = 23
HOMING_FEED = 24
HOMING_SEEK = 25
HOMING_DEBOUNCE = 26
HOMING_PULL_OFF = 27
MAX_SPINDLE = 30
MIN_SPINGLE = 31
LASER_MODE = 32
X_STEPS = 100
Y_STEPS = 101
Z_STEPS = 102
X_MAX_RATE = 110
Y_MAX_RATE = 111
Z_MAX_RATE = 112
X_ACCELERATION = 120
Y_ACCELERATION = 121
Z_ACCELERATION = 122
X_MAX_TRAVEL = 130
Y_MAX_TRAVEL = 131
Z_MAX_TRAVEL = 132

VIEW_GCODE_PARAMETERS = "#"
VIEW_GCODE_PARSER_STATE = "G"
VIEW_BUILD_INFO = "I"
VIEW_STARTUP_BLOCKS = "N"
CHECK_GCODE_MODE = "C"
KILL_ALARM_LOCK = "X"
RUN_HOMING_CYCLE = "H"
RESET_SETTINGS = "RST=$"
RESET_WORK_COORDINATES = "RST=#"
RESET_ALL_EEPROM = "RST=*"
ENABLE_SLEEP_MODE = "SLP"

class GRBL():
    """Opens a GRBL connection to the the given serial port

    Opens and controls a GRBL connection to the given seril port
    with the given bit rate.

    Attributes:
        portname: a String with serial port with a connected GRBL device
        baudrate: an Integer bit rate for the serial port
        s: Serial connection to the specified port
    """
    def __init__(self, portname, baudrate):
        self.portname = portname
        self.baudrate = baudrate
        self.s = serial.Serial(self.portname,self.baudrate)

        # Wake up GRBL, wait for GRBL to initialize, and flush startup text
        self.s.write(("\r\n\r\n").encode('utf-8'))
        sleep(2)
        self.s.flushInput()
    
    def custom_wait_for_response(self, cb=None):
        """Specify custom method for waiting for a response from grbl.

        Replaces the built-in method for waiting for a response from grbl with
        the function specified. If the specified function is None, it reset
        the object to use the built-in function
        
        Args:
            cb: the custom method to use
        """
        if cb:
            self.wait_for_response = cb
        else:
            self.wait_for_response = self._wait_for_response

    def _wait_for_response(self):
        """Waits for a response from GRBL and returns response

        Waits for Grbl to respond with an OK or ERROR message. This
        signals that Grbl has completed parsing and executing the command
        send immediately before calling this.
        """
        return self.s.readline()

    def _send_settings_message(self, code, val):
        """Writes a settings ($) message to the serial port

        Send a settings message to the serial port and waits for a 
        response. Returns the response.

        Args:
            code: the $x setting code
            val: value to set the code to
        """
        self.s.write(("${}={} \n").format(code,val).encode("utf-8"))
        return self.wait_for_response()

    def close(self):
        """Closes the grbl connection
        """
        self.s.close()

    def hard_limits(self, val):
        """Sets hard limits to the given value

        Args:
            val: Boolean indicating hard_limits setting

        Returns:
            the response from grbl after executing the command or the response
            from the custom "wait for response" method
        """
        if val:
            return self._send_settings_message(HARD_LIMITS, 1)
        else:
            return self._send_settings_message(HARD_LIMITS, 0)

    def run_homing_cycle(self):
        """Sends the homing cycle command

        Returns:
            The response from the "wait for response" method
        """
        self.s.write("${} \n".format(RUN_HOMING_CYCLE).encode('utf-8'))
        return self.wait_for_response()

    def kill_alarm_lock(self):
        """Sends the kill alarm lock command and returns response
        """
        self.s.write(('${} \n').format(KILL_ALARM_LOCK).encode('utf-8'))
        return self.wait_for_response()

    def get_current_status(self):
        """Returns the current status, as obtained from grbl
        """
        self.s.write(('? \n').encode('utf-8'))
        return self.wait_for_response()

    def get_work_position(self):
        """Returns the [x,y,z] work position as given by GRBL
        """
        response = self.get_current_status().decode('utf-8')
        response = response.replace(":",",")
        response = response.replace(">","")
        response = response.replace("<","")
        a_list = response.split(",")
        return [float(a_list[i]) for i in range(6,9)]

    def get_machine_position(self):
        """Returns the [x,y,z] machine position as given by GRBL
        """
        response = self.get_current_status().decode('utf-8')
        response = response.replace(":",",")
        response = response.replace(">","")
        response = response.replace("<","")
        a_list = response.split(",")
        return [float(a_list[i]) for i in range(2,4)]

    def set_coordinate_system(self, coord_system, x=None, y=None, z=None):
        """Offsets the origin of the axes ub the coordinate system specified

        Offsets the origin of the axes in the coordinate system specified to
        the value of the axis word. The offset is from the machine origin
        established during homing. The offset value will replace any current
        offsets in effect for the coordinate system specified. Axis words not
        used will not be changed.

        Args:
            coord_system: A Digit 0-9 specifying the coordinate system to use
            x: A Float offset for the x-axis
            y: A Float offset for the y-axis
            z: A Float offset for the z-axis
        
        Returns:
            The response from the "wait for response" method
        """
        cmd = "G10 L2 P{} ".format(coord_system)
        if x:
            cmd += "X{} ".format(x)
        if y:
            cmd += "Y{} ".format(y)
        if z:
            cmd += "Z{} ".format(z)
        cmd += "\n"
        self.s.write(cmd.encode('utf-8'))
        return self.wait_for_response()

    def coolant_control(self, mist=False, flood=False):
        """Controls the mist and flood coolant pins

        Args:
            mist: Boolean for iocontrol.o.coolant-mist pin (M7)
            flood: Boolean for iocontrol.o.coolant-flood pin (M8)
        
        Returns:
            The response from the "wait for response" method
        """
        if mist and not flood:
            self.s.write(('M9 \n').encode('utf-8'))
            self.wait_for_response()
            self.s.write(('M7 \n').encode('utf-8'))
        elif flood and not mist:
            self.s.write(('M9 \n').encode('utf-8'))
            self.wait_for_response()
            self.s.write(('M8 \n').encode('utf-8'))
        elif mist and flood:
            self.s.write(('M7 \n').encode('utf-8'))
            self.wait_for_response()
            self.s.write(('M8 \n').encode('utf-8'))
        else:
            self.s.write(('M9 \n').encode('utf-8'))
        return self.wait_for_response()

    def set_spindle_speed(self, x):
        """Sets the speed of the spindle to x revolutions per minute

        Args:
            x: An Integer revolutions per minute
        
        Returns:
            the response the "wait for response" method

        Throws:
            Exception if x < 0
        """
        assert(x >= 0)
        self.s.write(('S{} \n').format(x).encode('utf-8'))
        return self.wait_for_response()

    def spindle_control(self, clockwise=True, running=True):
        """Controls the spindle.
        
        M3 for clockwise, M3 for counterclockwise, M5 to stop

        Args:
            clockwise: Boolean to determine spin direction
            running: Boolean to start/stop the spindle
        
        Returns:
            The response from the "wait for response" method
        """
        if running:
            if clockwise:
                self.s.write(('M3 \n').encode('utf-8'))
            else:
                self.s.write(('M4 \n').encode('utf-8'))
        else:
            self.s.write(('M5 \n').encode('utf-8'))
        return self.wait_for_response()

    def rapid_move(self, x=None, y=None, z=None):
        """Performs rapid motion in the axis words specified.

        Args:
            x: Float motion in the x direction
            y: Float motion in the y direction
            z: Float motion in the z direction
        
        Returns:
            The response from the "wait for response" method
        """
        cmd = "G0 "
        if x:
            cmd += "X{} ".format(x)
        if y:
            cmd += "Y{} ".format(y)
        if z:
            cmd += "Z{} ".format(z)
        cmd += "\n"
        self.s.write(cmd.encode('utf-8'))
        return self.wait_for_response()