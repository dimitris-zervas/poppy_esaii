__author__ = 'Zervas Dimitris'


from PyQt4 import QtGui

class knobDialog(QtGui.QDialog):

    def __init__(self, parent = None, letter=None):
        super(knobDialog, self).__init__(parent)

        self.letter = letter

        self.range_label = QtGui.QLabel('Select range (+/-) :')
        self.range_line = QtGui.QLineEdit()


        self.variance_label = QtGui.QLabel('Select variance: ')
        self.variance_line = QtGui.QLineEdit()

        self.ok_button = QtGui.QPushButton('Ok')

        # Signal to accept()
        self.ok_button.clicked.connect(self.on_clicked)

        grid = QtGui.QGridLayout()

        grid.addWidget(self.range_label, 1,0)
        grid.addWidget(self.range_line, 1,1)
        grid.addWidget(self.variance_label, 2,0)
        grid.addWidget(self.variance_line, 2,1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(self.ok_button)

        self.setLayout(vbox)

        self.setGeometry(500,300,200,100)
        self.setWindowTitle(self.letter + ' Knob configuration')

    def on_clicked(self):
        self.accept()