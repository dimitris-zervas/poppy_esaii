__author__ = 'esaii'


import sys, glob
import serial
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import PyQt4.Qwt5 as Qwt
from matplotlib.lines import Line2D
import multiprocessing
import Queue
import numpy as np
from pycharm_arduino import com_thread
import inputDialog, knobDialog
from thread_COM1 import ComThread
from process_COM1 import ComProcess


class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.port_num = 'select port'
        self.r = 0

        self.monitor_active = False
        self.com_monitor = None
        self.com_data_q = None
        self.com_error_q = None
        self.gain_q = multiprocessing.Queue(2)
        self.data_q = multiprocessing.Queue()
        self.error_q = multiprocessing.Queue()

        self.position = list()
        self.time = list()

        self.inputs_list = list()
        self.ports_list = []


        # Timer to create a periodic event and update the plot
        self.timer = QtCore.QTimer()
        # Value and range of each potentiometer - Limits are [value-range, value+range]
        self.p_value = 10
        self.p_range = 10
        self.p_step = 0.1
        # -----------------
        self.i_value = 10
        self.i_range = 10
        self.i_step = 0.1
        # -----------------
        self.d_value = 10
        self.d_range = 10
        self.d_step = 0.1

        self.initUI()


    def initUI(self):

        # Create StatusBar
        statusBar = QtGui.QStatusBar()
        
        self.input_names = list()

        self.active_reference_x = list()
        self.active_reference_y = list()
        self.active_reference_x1 = list()


        self.xs_list = list()
        self.ys_list = list()

        self.thread = QtCore.QThread()

        # Create frames
        self.plot_frame = QtGui.QFrame(self)
        self.plot_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.knobs_frame = QtGui.QFrame(self)
        self.knobs_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame3 = QtGui.QFrame(self)
        self.frame3.setFrameShape(QtGui.QFrame.StyledPanel)

        # Ports Combo Box
        self.port_combo = QtGui.QComboBox(self)
        self.port_combo.setEnabled(False)
        self.port_combo.addItem('Select port')
        # Reference signals Combo box
        self.ref_signals_combo = QtGui.QComboBox(self)
        self.ref_signals_combo.setEnabled(False)
        self.ref_signals_combo.addItem('Choose a Reference Signal')
        self.ref_signals_combo.activated[str].connect(self.on_reference_choice)

        '''--------------- Buttons ----------------'''
        # Start button
        self.start_button = QtGui.QPushButton('Start')
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_onClicked)
        #Stop button
        self.stop_button = QtGui.QPushButton('Stop')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_onClicked)
        # Scan Button
        self.scan_button = QtGui.QPushButton('Scan')
        self.scan_button.setEnabled(True)
        self.scan_button.clicked.connect(self.scan_onClicked)

        ''' ----------- FIGURE LAYOUT ------------'''
        # a figure instance to plot on
        self.figure = plt.figure() #figsize=(3.0,2.0)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        self.ax = self.figure.add_subplot(1,1,1)
        self.ax.set_xlabel('time (sec)')
        self.ax.set_ylabel('angle (deg)')
        self.ax.axis([0,5,-20,20])
        self.ax.grid()

        self.active_reference = Line2D([0,5],[0,0], linewidth=1.0, color='red')
        self.ax.add_line(self.active_reference)

        self.position_line = Line2D([0,0],[0,0],linewidth=1.0, color='black')

        # Figure with frame
        self.topLeft = QtGui.QHBoxLayout()
        self.topLeft.addWidget(self.canvas)
        self.plot_frame.setLayout(self.topLeft)

        ''' ----------- KNOBS LAYOUT ------------'''
        # Knobs
        self.knob1 = self.create_knob('P')
        self.knob2 = self.create_knob('I')
        self.knob3 = self.create_knob('D')

        # Input P
        self.textP = QtGui.QLineEdit()
        self.textP.setMaxLength(5)
        self.textP.setText(str(self.knob1.value()))
        self.labelP = QtGui.QLabel('P Gain:')

        # Input I
        self.textI = QtGui.QLineEdit()
        self.textI.setMaxLength(5)
        self.textI.setText(str(self.knob2.value()))
        self.labelI = QtGui.QLabel('I Gain:')

        # Input D
        self.textD = QtGui.QLineEdit()
        self.textD.setMaxLength(5)
        self.textD.setText(str(self.knob3.value()))
        self.labelD = QtGui.QLabel('D Gain:')

        # P/I/D Gain Layouts
        self.p_layout = self.create_knob_layout('P')
        self.i_layout = self.create_knob_layout('I')
        self.d_layout = self.create_knob_layout('D')

        # Final knobs layout
        self.knobs_layout = QtGui.QHBoxLayout()
        self.knobs_layout.addLayout(self.p_layout)
        self.knobs_layout.addLayout(self.i_layout)
        self.knobs_layout.addLayout(self.d_layout)
        self.knobs_frame.setLayout(self.knobs_layout)

        # Add LineEdit signals
        self.textP.returnPressed.connect(lambda: self.on_entered_pressed('P'))
        self.textI.returnPressed.connect(lambda: self.on_entered_pressed('I'))
        self.textD.returnPressed.connect(lambda: self.on_entered_pressed('D'))

        ''' ----------- Buttons/Combos LAYOUT ------------'''

        # port_combo plus start/stop buttons
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.start_button)
        hbox.addWidget(self.stop_button)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.scan_button)

        grid3 = QtGui.QGridLayout()
        grid3.addWidget(self.port_combo, 3, 0)
        grid3.addWidget(self.ref_signals_combo, 4, 0)
        grid3.addLayout(vbox, 5, 0)
        self.frame3.setLayout(grid3)

        ''' ----------- FINAL LAYOUT ------------'''
        grid = QtGui.QGridLayout()
        grid.addWidget(self.plot_frame,0,0,3,2)
        grid.addWidget(self.knobs_frame,3,0,2,2)
        grid.addWidget(self.frame3,0,3,5,1)

        ''' ----------- CENTRAL WIDGET ----------'''
        self.main_frame = QtGui.QWidget()
        self.main_frame.setLayout(grid)
        self.setCentralWidget(self.main_frame)

        self.create_menu()

        self.setGeometry(1000,300,700,450)
        self.setWindowTitle('ServoTune')
        self.show()


    def create_knob(self,letter):

        self.knob = Qwt.QwtKnob(self)
        self.knob.setRange(0, 20, 0, 0.1)
        self.knob.setScaleMaxMajor(10)
        self.knob.setKnobWidth(40)
        self.knob.setValue(self.p_value)
        self.knob.setStep(self.p_step)
        self.knob.valueChanged.connect(lambda: self.on_slider_moved(letter))
        return self.knob

    def create_knob_layout(self,letter):
        layout = QtGui.QVBoxLayout()
        dummy_layout = QtGui.QHBoxLayout()

        if letter == 'P':
            layout.addWidget(self.knob1)
            dummy_layout.addWidget(self.labelP)
            dummy_layout.addWidget(self.textP)
        elif letter == 'I':
            layout.addWidget(self.knob2)
            dummy_layout.addWidget(self.labelI)
            dummy_layout.addWidget(self.textI)
        elif letter == 'D':
            layout.addWidget(self.knob3)
            dummy_layout.addWidget(self.labelD)
            dummy_layout.addWidget(self.textD)

        layout.addLayout(dummy_layout)
        return layout

    def scan_onClicked(self):
        # Search for connected Devices
        ports = glob.glob('/dev/tty[A-Za-z]*')
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                self.ports_list.append(port)
            except (OSError, serial.SerialException):
                pass

        self.port_combo.clear() # Clear the combo list
        if len(self.ports_list) == 0:
            self.port_combo.addItem('No devices detected')
        else:
            self.port_combo.addItem('Select port')
            self.port_combo.setEnabled(True)

        for i in range(0,len(self.ports_list)):
            self.port_combo.addItem(str(self.ports_list[i]))
        # Signal
        self.port_combo.activated[str].connect(self.on_port_combo_Activated)

    def on_port_combo_Activated(self, text):

        self.port_num = text
        if text != 'select port':
            print 'You selected' , self.port_num
            self.port_combo.setEnabled(False)
        if not self.port_combo.currentText() == "Select port" and not \
                        self.ref_signals_combo.currentText() == "Choose a Reference Signal":
            self.start_button.setEnabled(True)

    def start_onClicked(self):

        """
        Start button pressed. Starts the communication between arduino and GUI.
        """
        if self.port_num == 'select port':
            print "Error! Select a port"
        else:
            self.active_reference_x1 = self.active_reference_x[1:]
            print self.active_reference_x1
            print "length: ",len(self.active_reference_x1)
            print "type: ", type(self.active_reference_x[1])
            # Create the instance of the Object
            self.com_monitor = ComProcess(self.active_reference_y, 8,
                                          self.data_q, self.error_q, self.gain_q,
                                          str(self.port_num), 115200)
            self.com_monitor.start()
            # Connect the timeout signal
            self.timer.timeout.connect(self.on_timer)
            # Start the timer
            self.timer.start(30)    # TODO: when you will read the Ts to change this '30' (to 2xTs?)

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    def on_timer(self):

        """Reads every 30 ms the data queue and updates the response Line2D."""

        qdata = list(self.get_all_from_Queue(self.data_q))
        for i in range(0, len(qdata)):
            # Get time and position from the Queue
            self.time.append(qdata[i][0])
            self.position.append(qdata[i][1])
            # Add them to the response Line2D
            self.position_line.set_data(self.time, self.position)
        # Add the response Line2D to the canvas and draw
        self.ax.add_line(self.position_line)
        self.canvas.draw()
        # Stop the timer after the reference signal is all sent
        if len(self.time) >= len(self.active_reference_x1):
            self.timer.stop()
            print "Sent all"


    def stop_onClicked(self):
        """
        Stop button clicked. Kills the process.
        """

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.port_combo.setEnabled(True)
        # Kill the COM process
        self.com_monitor.join(0.01)

    def on_entered_pressed(self, letter):

        """
        Chane of value of knob by pressing enter.
            - Put the slider in the given value and set the limits to +/- range.
        """

        if letter == 'P':
            self.p_value = float(self.textP.text())
            self.knob1.setRange(self.p_value-self.p_range, self.p_value+self.p_range, 0, 1)
            self.knob1.setStep(self.p_step)
            self.knob1.setValue(self.p_value)
        elif letter == 'I':
            self.i_value = float(self.textI.text())
            self.knob2.setRange(self.i_value-self.i_range, self.i_value+self.i_range, 0, 1)
            self.knob2.setStep(self.i_step)
            self.knob2.setValue(self.i_value)
        elif letter == 'D':
            self.d_value = float(self.textD.text())
            self.knob3.setRange(self.d_value-self.d_range, self.d_value+self.d_range, 0, 1)
            self.knob3.setStep(self.d_step)
            self.knob3.setValue(self.d_value)

    def on_slider_moved(self, letter):
        """
        On knob change:
            - update the according text line.
            - Clear the 'gain_q' Queue and update it.
        """

        if letter == 'P':
            val = self.knob1.value()
            self.textP.setText(str(val))
            # clear the gain queue
            self.clear_queue(self.gain_q)
            # Add let + value
            self.gain_q.put('P')
            self.gain_q.put(val)
        elif letter == 'I':
            val = self.knob2.value()
            self.textI.setText(str(val))
            # clear the gain queue
            self.clear_queue(self.gain_q)
            # Add let + value
            self.gain_q.put('I')
            self.gain_q.put(val)
        elif letter == 'D':
            val = self.knob3.value()
            self.textD.setText(str(val))
            # clear the gain queue
            self.clear_queue(self.gain_q)
            # Add let + value
            self.gain_q.put('D')
            self.gain_q.put(val)

    def create_menu(self):
        # create Action (for now manually - later with method)
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'),'&Exit',self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit Application')
        exitAction.triggered.connect(QtGui.qApp.quit)
        # <Tools>
        p_knob = QtGui.QAction('&Knob(P)', self)
        p_knob.setShortcut('Ctrl+P')
        i_knob = QtGui.QAction('&Knob(I)', self)
        i_knob.setShortcut('Ctrl+I')
        d_knob = QtGui.QAction('&Knob(D)', self)
        d_knob.setShortcut('Ctrl+D')
        # Connect the signals/slots
        p_knob.triggered.connect(lambda: self.show_knobs_dialog('P'))
        i_knob.triggered.connect(lambda: self.show_knobs_dialog('I'))
        d_knob.triggered.connect(lambda: self.show_knobs_dialog('D'))
        # Input Signal creation - actions
        create_input = QtGui.QAction('&New Reference Signal',self)
        create_input.triggered.connect(self.create_new_signal)
        # Periodic Signal creation - actions
        create_periodic_input = QtGui.QAction('&New Periodic Reference Signal', self)
        create_periodic_input.triggered.connect(self.create_new_periodic_signal)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        toolsMenu = menubar.addMenu('&Tools')
        toolsMenu.addAction(p_knob)
        toolsMenu.addAction(i_knob)
        toolsMenu.addAction(d_knob)
        input_signal_menu = menubar.addMenu('&Signal')
        input_signal_menu.addAction(create_input)
        input_signal_menu.addAction(create_periodic_input)
        # fileMenu.addAction(toolsAction)

    def show_knobs_dialog(self,let):
        '''
        Opens the dialog to reconfigure the knob's range and/or variance
        '''
        #TODO fix this "bad" name
        self.knob_config = knobDialog.knobDialog(self,let)
        self.knob_config.show()  # with show it is modeless dialog (doesn't block the mainWindow)
        self.knob_config.ok_button.clicked.connect(lambda: self.update_knob(let))

    def update_knob(self, let):
        if let == 'P':
            # print 'ep'
            self.p_range = float(self.knob_config.range_line.text())
            self.p_step = float(self.knob_config.variance_line.text())
            self.knob1.setRange(self.p_value-self.p_range, self.p_value+self.p_range, 0, 1)
            self.knob1.setStep(self.p_step)
            self.knob1.setValue(self.knob1.value())
            # print rng, var
        elif let == 'I':
            self.i_range = float(self.knob_config.range_line.text())
            self.i_step = float(self.knob_config.variance_line.text())
            self.knob2.setRange(self.i_value-self.i_range, self.i_value+self.i_range, 0, 1)
            self.knob2.setStep(self.i_step)
            self.knob2.setValue(self.knob2.value())
        elif let == 'D':
            self.d_range = float(self.knob_config.range_line.text())
            self.d_step = float(self.knob_config.variance_line.text())
            self.knob3.setRange(self.d_value-self.d_range, self.d_value+self.d_range, 0, 1)
            self.knob3.setStep(self.d_step)
            self.knob3.setValue(self.knob3.value())

    def create_new_signal(self):
        self.input_config = inputDialog.new_inputDialog(self.inputs_list)
        self.input_config.show()
        self.input_config.ok_button.clicked.connect(self.get_input_data)

    def create_new_periodic_signal(self):
        self.input_periodic_config = inputDialog.new_periodic_dialog(self.inputs_list)
        self.input_periodic_config.show()
        self.input_periodic_config.ok_button.clicked.connect(self.get_input_periodic_data)

    def get_input_data(self):
        """
        Get from the new input dialog class, the x_data and the y_data
        """

        xs = self.input_config.xs
        ys = self.input_config.ys

        self.xs_list.append(xs)
        self.ys_list.append(ys)

        self.inputs_list = self.input_config.list
        self.ref_signals_combo.addItem(self.inputs_list[-1])

        # Enable the reference combo box
        if not self.ref_signals_combo.isEnabled():
            self.ref_signals_combo.setEnabled(True)

    def get_input_periodic_data(self):

        xs = self.input_periodic_config.xs
        ys = self.input_periodic_config.ys

        self.xs_list.append(xs)
        self.ys_list.append(ys)

        self.inputs_list = self.input_periodic_config.list
        self.ref_signals_combo.addItem(self.inputs_list[-1])

        # Enable the reference combo box
        if not self.ref_signals_combo.isEnabled():
            self.ref_signals_combo.setEnabled(True)

    def on_reference_choice(self, text):

        for i in range(len(self.inputs_list)):
            if self.inputs_list[i] == text:
                self.active_reference_x = self.xs_list[i]
                self.active_reference_y = self.ys_list[i]
                # Final signal to be sent to arduino
                self.active_reference.set_data(self.active_reference_x,self.active_reference_y)
                # Change the limits of the axis
                xmax = max(self.active_reference_x)
                ymax = max(self.active_reference_y)
                ymin = min(self.active_reference_y)
                self.ax.axis([0, xmax, ymin-10, ymax+10])
                self.canvas.draw()
                # Debugging
                print self.active_reference_x
                print "Length of reference to be sent: ", len(self.active_reference_x)
        if not self.port_combo.currentText() == "Select port" and not \
                        self.ref_signals_combo.currentText() == "Choose a Reference Signal":
            self.start_button.setEnabled(True)


    def clear_queue(self, q):
        # if q.qsize()
        while q.qsize()>0:
            trash = q.get()

    def get_all_from_Queue(self, Q):
        try:
            while True:
                yield Q.get_nowait()
        except Queue.Empty:
            raise StopIteration


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()