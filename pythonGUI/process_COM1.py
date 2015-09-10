__author__ = 'Zervas Dimitris'



import Queue
import threading
import time
import serial
import struct
import multiprocessing
from multiprocessing import Queue



class command:
    startCx_f = 0xf0
    startCx_e = 0xf1
    stopCx = 0xf2
    p = 0xf3
    i = 0xf4
    d = 0xf5
    x = 0xf6    # when you send just reference

class ComProcess(multiprocessing.Process):

    def __init__(self, reference,
                 frameLen,
                 data_q, error_q, gain_q,
                 port_num,
                 port_baud,
                 port_stopbits=serial.STOPBITS_ONE,
                 port_parity=serial.PARITY_NONE,
                 port_timeout=None):

        multiprocessing.Process.__init__(self)

        self.arduino = None
        self.serial_arg = dict(port=port_num,
                               baudrate=port_baud,
                               stopbits=port_stopbits,
                               parity=port_parity,
                               timeout=port_timeout)

        print "Process init"

        self.reference = reference
        self.data_q = data_q
        self.error_q = error_q
        self.gain_q = gain_q
        self.frameLen = frameLen
        self.eol = 'cXrC'
        self.ref = 0    # Instance of the reference signal
        self.ref_counter = 0
        self.position = 0
        self.prev_gain = 0
        self.new_gain = 0
        self.command_gain = command.x

        ''' Flags '''
        self.txOn = False   # flag to send data or not (decided by arduino)
        self.rxOn = False   # flag to receive data (raises after the sent of ref+gain)
        self.validData = False
        self.time = 0
        self.readOnce = True
        self.dummy = True
        self.c = 0

        # Create an event object
        self.alive = multiprocessing.Event()
        self.alive.set()

    def run(self):

        try:
            if self.arduino:
                self.arduino.close()
            # Open the port and restart the Arduino
            self.arduino = serial.Serial(**self.serial_arg)
            self.arduino.setDTR(False)
            time.sleep(0.022)   # Time used also by arduino IDE
            self.arduino.setDTR(True)
        except serial.SerialException, e:
            self.error_q.put(e.message)
            print "OP"
            return

        time.sleep(2)   # Give some time to arduino to get ready
        dummy_flag = True   # TODO: needed?
        print "Process is alive"

        while self.alive.is_set():
            ''' Process executes until the run() method stops - So as long as alive.isSet,
                process is running. alive.clear() happens with the stop button, or end of reference signal'''

            if self.readOnce:
                kar = self.arduino.read(1)  # timeout=None
                if self.dummy:
                    # Start of timing
                    t = time.time()
                    self.dummy = False
                self.readOnce = False
            if kar == 's':
                self.txOn = True
                # Clear any -possible- remaining in the input buffer
                trash = self.arduino.flushInput()

            ''' CONSTRUCT THE BUFFER:
                    -update the gains: gains_q is FIFO so first element is which gain to update (P,I or D),
                     second element is the gain value
            '''

            # the reference value to send
            self.ref = self.reference[self.ref_counter]
            # value1 is the first float to be send (the reference)
            value1 = struct.pack('%sf' % 1, self.ref)

            # Update the gains
            if self.gain_q.qsize() == 2:
                let = self.gain_q.get()
                self.new_gain = self.gain_q.get()

                if let == 'P':
                    self.command_gain = command.p
                elif let == 'I':
                    self.command_gain = command.i
                elif let == 'D':
                    self.command_gain = command.d
            elif self.gain_q.qsize == 1:    # if size less than 2 (smth went wrong!), clear the queue
                trash = self.gain_q.get()

            # If the knobs didn't change, send just the reference (startCx_e)
            if self.new_gain == self.prev_gain:
                command_start = command.startCx_e
                self.command_gain = command.x
                # value2 is the second float to be send (the gain), in that case, 0.
                value2 = struct.pack('%sf' % 1, float(0))
            else:
                self.prev_gain = self.new_gain
                command_start = command.startCx_f
                value2 = struct.pack('%sf' % 1, self.new_gain)

            # Construct the buffer
            buf = bytearray([command_start, ord(value1[0]), ord(value1[1]), ord(value1[2]), ord(value1[3]),
                             self.command_gain, ord(value2[0]), ord(value2[1]), ord(value2[2]), ord(value2[3])])

            if self.txOn:
                # Send the buffer
                self.arduino.write(buf)
                self.txOn = False
                self.rxOn = True

            if self.rxOn:
                # Read the input buffer - blocks until frameLen bytes are received (no timeout on serial)
                input_buffer = self.arduino.read(8)    # frameLen = 8 -> position (4 bytes) + eof (4bytes)
                # Check if the received data is correct,
                if input_buffer[-4:] == self.eol:
                    self.validData = True
                    # and Remove eol
                    input_buffer = input_buffer[0:-4]
                else:
                    print "Wrong data received"
                    trash = self.arduino.flushInput()
                    self.c += 1

            if self.validData:
                self.rxOn = False
                self.ref_counter += 1
                # Translate data to float
                self.position = struct.unpack('f', input_buffer[0:4])   # Returns a tuple
                self.position = self.position[0]                        # Take the first element of the tuple
                self.position = "%.2f" % self.position                  # Round it up
                # If for every control loop the COM is complete, no need to send the Ts from arduino to here
                self.time += 0.015

                # Add the data to the Queue
                self.data_q.put((self.time, self.position))
                # Look for 's' character again
                self.readOnce = True
                self.validData = False

            # When all the reference signal is sent
            if self.ref_counter == len(self.reference):
                self.alive.clear()  # It terminates the run()
                # Tell arduino that process is finished
                buf = bytearray([command.stopCx,0,0,0,0,0,0,0,0,0])
                self.arduino.write(buf)
                # End the process   #TODO !
                # multiprocessing.Process.join(self,0.01)
                print "Number of data received: ", self.ref_counter
                print "Number of wrong data: ", self.c
                print "total time: ", time.time()-t

            if dummy_flag:
                print 'Waiting arduino...'
                dummy_flag = False

        # Clean it up
        if self.arduino:
            self.arduino.close()

    def join(self, timeout=None):
        self.alive.clear()
        multiprocessing.Process.join(self, timeout)
