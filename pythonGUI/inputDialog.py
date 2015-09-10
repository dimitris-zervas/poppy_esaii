from hgext.mq import select

__author__ = 'Zervas Dimitris'


from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np




class new_inputDialog(QtGui.QDialog):

    def __init__(self, lista):
        super(new_inputDialog,self).__init__()

        self.list = lista
        self.prev_x = 0
        self.prev_y = 0
        self.time = 0
        self.num_of_inputs = 0

        self.xs = list()
        self.ys = list()
        self.xs.append(0)
        self.ys.append(0)
        self.lim_x_axis = 2
        self.lim_y_axis = 20
        self.init_name = "Give a name of the new reference signal"
        self.Ts = 0

        self.onlyOnce = True    # Flag to solve the press_enter and next_button problem

        self.input_name = QtGui.QLineEdit()
        self.input_name.setText(self.init_name)
        self.input_name.returnPressed.connect(self.on_input_name_entered)
        # ---------------Next button--------------------
        self.next_button = QtGui.QPushButton('Next')
        self.next_button.setEnabled(False)
        self.next_button.setDefault(False)      # To prevent the enterPressed of a lineEdit to click the button
        self.next_button.setAutoDefault(False)  # .same.
        # ----------------Ok button---------------------
        self.ok_button = QtGui.QPushButton('Ok')
        self.ok_button.setEnabled(False)
        self.ok_button.setDefault(False)
        self.ok_button.setAutoDefault(False)
        # -------------Point label/text-----------------
        point_label = QtGui.QLabel('time,angle')
        self.point_text = QtGui.QLineEdit()
        self.point_text.setText('0,0')
        self.point_text.setEnabled(False)
        self.point_text.textChanged.connect(self.on_point_text_changed)
        # -------------Sampling label/text--------------
        sampling_label = QtGui.QLabel('Sampling Time')
        self.sampling = QtGui.QLineEdit()
        self.sampling.setEnabled(False)
        # -------------Buttons Signals ------------------
        self.next_button.clicked.connect(self.next_clicked)
        self.sampling.returnPressed.connect(self.on_sampling_enter)
        self.ok_button.clicked.connect(self.ok_clicked)

        # ------------- Figure/Canvas ------------------
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)

        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.set_xlabel('time')
        self.ax.set_ylabel('angle')
        self.ax.axis([0,self.lim_x_axis,-self.lim_y_axis,self.lim_y_axis])
        self.ax.grid()

        self.ref_line = Line2D([0, self.lim_y_axis],[0, 0], color='red', linewidth=2)
        self.ax.add_line(self.ref_line)

        # ----------------- Layout ---------------------
        grid = QtGui.QGridLayout()
        grid.addWidget(self.input_name, 1, 1)
        grid.addWidget(self.canvas, 2, 1, 4, 1)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(sampling_label)
        vbox.addWidget(self.sampling)
        vbox.addWidget(point_label)
        vbox.addWidget(self.point_text)
        vbox.addWidget(self.next_button)
        vbox.addWidget(self.ok_button)

        grid.addLayout(vbox, 5, 2)
        self.setLayout(grid)
        # ------------ Dialog Size/Title ---------------
        self.setGeometry(500, 300, 800, 450)
        self.setWindowTitle('New Reference Signal Design')

    def next_clicked(self):

        if not self.point_text.text() == "":
            # Decompose the point string
            values = map(float, self.point_text.text().split(','))
            point_x = values[0]
            point_y = values[1]
            self.ok_button.setEnabled(True)


            if point_x < self.prev_x:
                print "Give a valid point"
            elif self.prev_x == point_x and self.prev_y == point_y:
                print "You gave the same point"
            else:
                # change -if necessary- the axis limits
                if point_x >= self.lim_x_axis:
                    self.lim_x_axis = point_x + 1
                    self.ax.axis([0, self.lim_x_axis, -self.lim_y_axis, self.lim_y_axis])
                if point_y >= self.lim_y_axis and point_x > 0:
                    self.lim_y_axis = point_y + 5
                    self.ax.axis([0, self.lim_x_axis, -self.lim_y_axis, self.lim_y_axis])
                elif point_y <= self.lim_y_axis and point_y < 0:
                    self.lim_y_axis = -point_y + 5
                    self.ax.axis([0, self.lim_x_axis, -self.lim_y_axis, self.lim_y_axis])

                # ----   Line "sampling" ----#

                # The vertical case
                if point_x == self.prev_x:
                    self.xs.append(point_x+self.Ts)
                    self.ys.append(point_y)
                    self.prev_x = point_x
                    self.prev_y = point_y
                    # self.time += self.Ts
                else:
                    # Slope
                    m = (point_y - self.prev_y) / (point_x - self.prev_x)
                    # Line
                    for i in np.linspace(self.prev_x+self.Ts, point_x, num=(point_x-self.prev_x)/self.Ts):
                        self.time += self.Ts
                        self.xs.append(round(self.time, 4))
                        dummy = round(m*(i-self.prev_x)+self.prev_y, 4)
                        self.ys.append(dummy)
                        self.prev_x = i
                        self.prev_y = dummy

                # -------------------------- #

                # Update the line
                self.ref_line.set_data(self.xs, self.ys)
                # Draw
                self.canvas.draw()

                # Reconfigure for the next point
                self.point_text.setText('')
                self.point_text.setFocus()

        else:
            print 'Give a valid point'

    def ok_clicked(self):
        # Add here the reference name to the list
        self.list.append(self.ref_name)
        self.accept()

    def on_input_name_entered(self):

        self.name_is_good = True
        self.ref_name = self.input_name.text()

        if self.ref_name == self.init_name:
            print 'Please give a name for the signal'
            self.name_is_good = False
        for i in range(len(self.list)):
            if self.ref_name == self.list[i]:
                print 'Name already Exists'
                self.name_is_good = False

        if self.name_is_good:
            # self.list.append(self.ref_name)
            self.sampling.setEnabled(True)
            self.input_name.setEnabled(False)

    def on_sampling_enter(self):
        self.Ts = float(self.sampling.text())
        self.point_text.setEnabled(True)
        self.next_button.setEnabled(True)
        self.sampling.setEnabled(False)

    def on_point_text_changed(self):
        # Not the smartest solution but it works
        if self.onlyOnce:
            self.next_button.setDefault(True)
            self.onlyOnce = False


class new_periodic_dialog(QtGui.QDialog):
    def __init__(self, lista):
        super(new_periodic_dialog,self).__init__()

        self.list = lista
        self.name = 0
        self.time_flag = 0
        self.sampling_flag = 0
        self.Ts = 0
        self.apply_flag = 0
        self.amp = 0
        self.freq = 0
        self.dummy_sum = 0
        self.ref_name = ""
        self.total_time = 0
        self.amplitude = 0
        self.frequency = 0
        self.x_points = list()
        self.y_points = list()
        self.xs = list()
        self.ys = list()
        self.xs.append(0)
        self.ys.append(0)
        self.time = 0
        self.xx = list()
        self.yy = list()
        self.xx.append(0)
        self.yy.append(0)

        # Info
        info_lbl = QtGui.QLabel(self)
        info_lbl.setText("Matlab-like periodic signal Generator\n\nY(t)=Amp*Waveform(Freq, t)")
        info_lbl.setWordWrap(True)
        # Name
        name_lbl = QtGui.QLabel(self)
        name_lbl.setText("Signal Name: ")
        self.name_line = QtGui.QLineEdit()
        self.name_line.textChanged.connect(self.name_changed)
        hbox_name = QtGui.QHBoxLayout()
        hbox_name.addWidget(name_lbl)
        hbox_name.addWidget(self.name_line)
        # Waveform
        wave_lbl = QtGui.QLabel(self)
        wave_lbl.setText("Waveform: ")
        self.wave_combo = QtGui.QComboBox(self)
        self.wave_combo.addItem('square')
        self.wave_combo.addItem('sawtooth')
        self.hbox_wave = QtGui.QHBoxLayout()
        self.hbox_wave.addWidget(wave_lbl)
        self.hbox_wave.addWidget(self.wave_combo)
        # Time
        time_lbl = QtGui.QLabel(self)
        time_lbl.setText("Time (sec): ")
        self.time_line = QtGui.QLineEdit()
        self.time_line.textChanged.connect(self.time_changed)
        hbox_time = QtGui.QHBoxLayout()
        hbox_time.addWidget(time_lbl)
        hbox_time.addStretch(1)
        hbox_time.addWidget(self.time_line)
        # Sampling Time
        sampling_lbl = QtGui.QLabel(self)
        sampling_lbl.setText("Sampling Time (sec): ")
        self.sampling_line = QtGui.QLineEdit()
        self.sampling_line.textChanged.connect(self.sampling_changed)
        hbox_sampling = QtGui.QHBoxLayout()
        hbox_sampling.addWidget(sampling_lbl)
        hbox_sampling.addStretch(1)
        hbox_sampling.addWidget(self.sampling_line)
        # Amplitude
        amp_lbl = QtGui.QLabel(self)
        amp_lbl.setText("Amplitude: ")
        self.amp_line = QtGui.QLineEdit()
        self.amp_line.textChanged.connect(self.amp_changed)
        vbox_amp = QtGui.QVBoxLayout()
        vbox_amp.addWidget(amp_lbl)
        vbox_amp.addWidget(self.amp_line)
        # Frequency
        freq_lbl = QtGui.QLabel(self)
        freq_lbl.setText("Frequency (Hz): ")
        self.freq_line = QtGui.QLineEdit()
        # Signal: text changed
        self.freq_line.textChanged.connect(self.freq_changed)
        vbox_freq = QtGui.QVBoxLayout()
        vbox_freq.addWidget(freq_lbl)
        vbox_freq.addWidget(self.freq_line)
        vbox_freq.addStretch(1)

        # OK Button
        self.ok_button = QtGui.QPushButton('OK')
        self.ok_button.clicked.connect(self.ok_clicked)
        self.ok_button.setEnabled(False)
        # Cancel Button
        self.cancel_button = QtGui.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.cancel_clicked)
        # Apply Button
        # self.apply_button = QtGui.QPushButton('Apply')
        # self.apply_button.clicked.connect(self.apply_clicked)
        # self.apply_button.setEnabled(False)
        # Buttons Layout
        hbox_buttons = QtGui.QHBoxLayout()
        hbox_buttons.addStretch(1)  # push them to the right
        # hbox_buttons.addWidget(self.apply_button)
        hbox_buttons.addWidget(self.ok_button)
        hbox_buttons.addWidget(self.cancel_button)

        # Info layout
        vbox_info = QtGui.QVBoxLayout()
        vbox_info.addWidget(info_lbl)
        # Parameters layout
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox_name)
        vbox.addLayout(self.hbox_wave)
        vbox.addLayout(hbox_time)
        vbox.addLayout(hbox_sampling)
        vbox.addLayout(vbox_amp)
        vbox.addLayout(vbox_freq)

        # Info GroupBox
        info_group = QtGui.QGroupBox('Periodic Signal Generator')
        info_group.setLayout(vbox_info)
        # Parameters GroupBox
        param_group = QtGui.QGroupBox('Parameters')
        param_group.setLayout(vbox)

        # Main Layout
        main_layout = QtGui.QGridLayout()
        main_layout.addWidget(info_group, 0, 0)
        main_layout.addWidget(param_group, 1, 0, 2, 0)
        main_layout.addLayout(hbox_buttons, 3, 0)

        self.setLayout(main_layout)
        self.setGeometry(800, 300, 400, 500)
        self.setWindowTitle('Periodic Signal Generator')
        self.setWindowFlags(QtCore.Qt.Drawer)   # No max/min window button

    def ok_clicked(self):
        if not self.apply_flag:
            self.signal_gen()
            self.list.append(self.ref_name)
        self.accept()

    # def apply_clicked(self):
    #     self.signal_gen()
    #     self.list.append(self.ref_name)
    #     self.apply_flag = True
    #     self.name_line.setText("")
    #     self.time_line.setText("")
    #     self.name_line.setFocus(True)
    #
    #     self.xs = []
    #     self.ys = []

    def cancel_clicked(self):
        self.accept()

    def signal_gen(self):
        x_points = list()
        y_points = list()

        signal = str(self.wave_combo.currentText())
        num_of_periods = self.total_time*self.frequency
        period = self.total_time/num_of_periods

        if signal == "square" and not self.total_time == -1:
            for i in range(1, int(num_of_periods)+1):
                period_end = i*period
                period_start = period_end-period
                x_points.extend([period_start, period_start+period/2, period_start+period/2, period_end])
                y_points.extend([self.amplitude, self.amplitude, 0, 0])

            # ----   Line "sampling" ---- #
            idx = 0
            prev_x = 0
            prev_y = 0
            for i in range(1, len(x_points)+1):
                # The vertical case
                if x_points[idx] == prev_x:
                    self.xs.append(x_points[idx]+self.Ts)
                    self.ys.append(y_points[idx])
                    prev_x = self.xs[-1]
                    prev_y = self.ys[-1]
                    idx += 1
                else:
                    # The parallel case
                    for i in np.linspace(prev_x+self.Ts, x_points[idx], num=(x_points[idx]-prev_x)/self.Ts):
                        self.xs.append(self.xs[-1]+self.Ts)
                        self.ys.append(y_points[idx])
                        prev_x = self.xs[-1]
                        prev_y = self.ys[-1]
                    idx += 1
            # --------------------------- #

        elif signal == "sawtooth" and not self.total_time == -1:
            for i in range(1, int(num_of_periods)+1):
                period_end = round(i*period, 4)
                period_start = round(period_end-period, 4)
                x_points.extend([period_start, period_end])
                y_points.extend([self.amplitude, 0])

            # ----   Line "sampling" ---- #
            idx = 0
            prev_x = 0
            prev_y = 0
            for i in range(1, len(x_points)+1):
                # The vertical case
                if prev_x == x_points[idx]:
                    self.xs.append(round(x_points[idx]+self.Ts, 4))
                    self.ys.append(y_points[idx])
                    prev_x = self.xs[-1]
                    prev_y = self.ys[-1]
                else:
                    # Slope
                    m = (y_points[idx] - prev_y) / (x_points[idx] - prev_x)
                    for i in np.linspace(prev_x+self.Ts, x_points[idx], num=(x_points[idx]-prev_x)/self.Ts):
                        # print i
                        self.xs.append(round(self.xs[-1]+self.Ts, 4))
                        dummy = round(m*(i-prev_x)+prev_y, 4)
                        self.ys.append(dummy)
                        prev_x = self.xs[-1]
                        prev_y = self.ys[-1]
                idx += 1
            # --------------------------- #

    #   --------------------------------------------------
    def name_changed(self):
        ref_name = str(self.name_line.text())
        # Check if name exists
        for i in range(len(self.list)):
            if ref_name == self.list[i]:
                print 'Name already Exists'
                self.time_line.setEnabled(False)
                self.freq_line.setEnabled(False)
                self.sampling_line.setEnabled(False)
                self.amp_line.setEnabled(False)
            else:
                self.time_line.setEnabled(True)
                self.freq_line.setEnabled(True)
                self.sampling_line.setEnabled(True)
                self.amp_line.setEnabled(True)

        if not self.name_line.text() == "":
            self.name = 1
            # Get the reference name
            self.ref_name = str(self.name_line.text())
        else:
            self.name = 0
        self.all_filled()

    def time_changed(self):
        if not self.time_line.text() == "":
            self.time_flag = 1
            # Get the total time of the signal
            self.total_time = float(self.time_line.text())
            # print type(self.total_time), self.total_time
        else:
            self.time_flag = 0
        self.all_filled()

    def sampling_changed(self):
        if not self.sampling_line.text() == "":
            self.sampling_flag = 1
            # Get the sampling time
            self.Ts = float(self.sampling_line.text())
        else:
            self.sampling_flag = 0
        self.all_filled()

    def amp_changed(self):
        if not self.amp_line.text() == "":
            self.amp = 1
            # Get the amplitude
            self.amplitude = float(self.amp_line.text())
        else:
            self.amp = 0
        self.all_filled()

    def freq_changed(self):
        if not self.freq_line.text() == "":
            self.freq = 1
            # Get the frequency
            self.frequency = float(self.freq_line.text())
        else:
            self.freq = 0
        self.all_filled()

    def all_filled(self):
        self.dummy_sum = self.name+self.time_flag+self.amp+self.freq+self.sampling_flag
        if self.dummy_sum == 5:
            self.ok_button.setEnabled(True)
            # self.apply_button.setEnabled(True)
            self.dummy_sum = 0
    #   --------------------------------------------------