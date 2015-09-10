__author__ = 'Zervas Dimitris'



import Queue
import threading
import time
import serial, struct



class command:
    startCx_f = 0xf0
    startCx_e = 0xf1
    stopCx = 0xf2
    p = 0xf3
    i = 0xf4
    d = 0xf5
    x = 0xf6    # when you send just reference

class ComThread(threading.Thread):

    def __init__(self, reference,
                 frameLen,
                 data_q, error_q, gain_q,
                 port_num,
                 port_baud,
                 port_stopbits=serial.STOPBITS_ONE,
                 port_parity=serial.PARITY_NONE,
                 port_timeout=None):

        threading.Thread.__init__(self)

        self.arduino = None
        self.serial_arg = dict( port=port_num,
                                baudrate=port_baud,
                                stopbits=port_stopbits,
                                parity=port_parity,
                                timeout=0.01)

        print "Thread init"

        self.reference = reference
        self.data_q = data_q
        self.error_q = error_q
        self.gain_q = gain_q
        self.frameLen = frameLen
        self.eol = 'cXrC'
        self.ref_counter = 0
        self.position = 0

        self.prev_gain = 0
        self.new_gain = 0
        self.command_gain = command.x

        self.txOn = False   # flag to send data or not (decided by arduino)
        self.time = 0

        # Create an event object
        self.alive = threading.Event()
        self.alive.set()
        self.dummy = True
        self.readOnce = True
        self.c = 0
        self.prev_clk = time.clock()

    def run(self):

        try:
            if self.arduino:
                self.arduino.close()
            # Open the port and restart the Arduino
            self.arduino = serial.Serial(**self.serial_arg)
            self.arduino.setDTR(False)
            time.sleep(0.022)   # Time used by arduino IDE
            self.arduino.setDTR(True)
        except serial.SerialException, e:
            self.error_q.put(e.message)
            print "OP"
            return

        time.sleep(2)
        dummy_flag = True
        print "Thread is alive"
        # tt = time.time()
        while self.alive.is_set():
            ''' Thread executes until the run() method stops - So as long as alive.isSet,
                thread is running. alive.clear() happens with the stop button, or end of reference signal'''
            # t = time.time()
            kar = self.arduino.read(1)
            if kar == 's':
                self.arduino.write('HelloWorld')
            # print time.time()-tt
            # tt = time.time()
            # Clear any remaining in the input buffer
            # trash = self.arduino.flushInput()
            # if self.dummy:
            #     tt = time.time()
            #     self.dummy = False

            # Arduino triggers the "talking"
            if kar == 's' and self.readOnce==True:
                # self.txOn = True


                self.dummy = True

                self.readOnce == False
                # t1 = time.time()-t
                # t = time.time()
            if self.txOn == True:
                '''update the gains: gains_q is FIFO so first element is which gain to update,
                    second element is the gain value'''
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
                if not self.new_gain == self.prev_gain:
                    print "Send: ", let, self.new_gain
                    self.prev_gain = self.new_gain
                    command_start = command.startCx_f
                    value2 = struct.pack('%sf' %1, self.new_gain)
                else:
                    command_start = command.startCx_e
                    self.command_gain = command.x
                    # value2 is the second float to be send (the gain)
                    value2 = struct.pack('%sf' %1, float(0))

                # the reference value to send
                self.ref = self.reference[self.ref_counter]
                # value1 is the first float to be send (the reference)
                value1 = struct.pack('%sf' %1,self.ref)
                # Construct the buffer
                buffer = bytearray([command_start, ord(value1[0]),ord(value1[1]),ord(value1[2]),ord(value1[3]),
                                    self.command_gain, ord(value2[0]), ord(value2[1]), ord(value2[2]), ord(value2[3])])
                # And send it
                self.arduino.write(buffer)
                # t2 = time.time()-t
                # t = time.time()
                # print self.ref, buffer
                '''you sent the data, now wait for the response'''
                # once arduino will receive the data, will have to do calculations so you have time to enter the while
                # before arduino send back data

                input_buffer = bytearray()
                receive_flag = False
                # try:

                while True:
                    data = self.arduino.read(1)
                    input_buffer.append(data)
                    if input_buffer[-4:] == self.eol: #verifies if EOF has been received
                        break
                    # if self.arduino.inWaiting()>10 and receive_flag == False:
                    #     print "Epep", time.time()-t
                    #     receive_flag = True
                    # if receive_flag:
                    #     t = time.time()
                    #     data = self.arduino.read(1)
                    #     input_buffer.append(data)
                    #     if input_buffer[-4:] == self.eol: #verifies if EOF has been received
                    #         break
                    #         receive_flag = False

                # print "ep"
                # while True:
                #     data = self.arduino.read(1)
                #     input_buffer.append(data)
                #     if input_buffer[-1] == 'C':
                #         break;
                # print "Op"

                # t3 = time.time()-t
                # t = time.time()
                input_buffer = input_buffer[0:-4] #removes EOF

                # self.arduino.write(bytearray([0x65]))

                self.ref_counter += 1   #TODO maybe here is not proper to increase the counter
                self.txOn = False
                self.readOnce = True
                # except  KeyboardInterrupt:
                #     print "Exiting..."
                # self.arduino.write(bytearray([0x65]))
                if len(input_buffer) == self.frameLen:

                    self.position = struct.unpack('f', input_buffer[0:4])
                    self.position = self.position[0]
                    self.position =  "%.2f" % self.position

                    # self.time = struct.unpack('f', input_buffer[4:8])
                    # self.time = self.time[0]
                    # self.time = "%2f" % self.time
                    self.time += 0.015

                    # Add the data to the Queue
                    self.data_q.put((self.time, self.position))
                else:
                    self.c += 1
                # t4 = time.time()-t
                if self.ref_counter == len(self.reference):
                    self.txOn = False
                    self.alive.clear()  #It terminates the run() therefore ends the thread
                    buffer = bytearray([command.stopCx,0,0,0,0,0,0,0,0,0])
                    self.arduino.write(buffer)
                    # threading.Thread.join(self,0.01)
                    print "Numnber of data received: ", self.ref_counter
                    print "Number of wrong data: ",self.c
                    # print "total time: ", time.time()-tt
                # if t1+t2+t3+t4 > 0.02:
                #     print t1, "   ", t2, "    ", t3, "    ", t4,"      ", t1+t2+t3+t4

            else:
                if dummy_flag:
                    print 'Waiting arduino...'
                    dummy_flag = False


        if self.arduino:
            self.arduino.close()

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)
