#! /usr/bin/env python
#
from PyQt5 import QtWidgets as qw, QtGui as qg
from argparse import ArgumentParser
from json import load
from subprocess import Popen, PIPE
from re import match
from sys import argv
from os import path
from glob import glob

# parse arguments
argparser = ArgumentParser(description='Runs the GUI for configuring an athinput file')
argparser.add_argument('-r', '--run',
                       action='store_true',
                       help='executes the athena command and plots the tab files on run',
                       default=False)
args = argparser.parse_args()

athena_problems = {}

# building gui
if False:
    with open('athena_problems.json') as problems_json:
        problems = load(problems_json)
    athena_problems = list(problems['athenak'])
else:
    for file in glob('./athenak/inputs/*.athinput'):
        athena_problems[file.split('/')[-1]] = file

class MainWindow(qw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.radio_groups = []
        self.windows = []

        self.plot = True

        page_layout = qw.QVBoxLayout()
        radio_layout = qw.QVBoxLayout()
        exe_layout = qw.QHBoxLayout()
        load_layout = qw.QHBoxLayout()
        predef_layout = qw.QHBoxLayout()
        self.current_athena = 'athena'

        toolbar = self.addToolBar('ToolBar')

        launch_action = qw.QAction('Launch', self)
        launch_action.setToolTip('Launch the parameter configurator')
        launch_action.triggered.connect(self.launch)
        toolbar.addAction(launch_action)
        toolbar.addSeparator()

        help_action = qw.QAction('Help', self)
        help_action.setToolTip('Open help menu')
        help_action.triggered.connect(self.help)
        toolbar.addAction(help_action)
        toolbar.addSeparator()

        clear_action = qw.QAction('Clear', self)
        clear_action.setToolTip('Clears all Athena problem directories')
        clear_action.triggered.connect(self.clear)
        toolbar.addAction(clear_action)
        toolbar.addSeparator()

        quit_action = qw.QAction('Quit', self)
        quit_action.setToolTip('Exit the program')
        quit_action.triggered.connect(self.quit)
        toolbar.addAction(quit_action)

        def browse(t):
            file = qw.QFileDialog.getOpenFileName(self, "Select File", "")[0]
            t.setText(file)

        if False:
            label = qw.QLabel('Athena Version: [deprecating]')
            radio_layout.addWidget(label)
            label.setStyleSheet("font-weight: bold")
            radio_layout.addStretch()
        
            rbtn = qw.QRadioButton('Athena')
            rbtn.toggled.connect(lambda: self.switch('athena'))
            radio_layout.addWidget(rbtn)
            rbtn = qw.QRadioButton('AthenaK')
            rbtn.setChecked(True)        
            rbtn.toggled.connect(lambda: self.switch('athenak'))
            radio_layout.addWidget(rbtn)
            rbtn = qw.QRadioButton('AthenaC')
            rbtn.toggled.connect(lambda: self.switch('athenac'))
            radio_layout.addWidget(rbtn)

        if False:
            label = qw.QLabel('Athena Executable: [deprecating]')
            exe_layout.addWidget(label)
            label.setStyleSheet("font-weight: bold")
            btn = qw.QPushButton(self)
            btn.setText("browse")
            self.exe = qw.QLineEdit(self)
            btn.clicked.connect(lambda: browse(self.exe))
            self.exe.setFixedWidth(250)
            self.exe.setText('athenak/build/src/athena')
            exe_layout.addStretch()
            exe_layout.addWidget(btn)
            exe_layout.addWidget(self.exe)
            self.athena = self.exe.text()
        else:
            self.athena = 'athenak/build/src/athena'
        print("athena:",self.athena)

        btn_group = qw.QButtonGroup()

        '''self.load_radio = qw.QRadioButton('Load Problem:')
        self.load_radio.setStyleSheet('font-weight: bold')
        self.load_radio.setChecked(True)
        load_layout.addWidget(self.load_radio)
        load_layout.addStretch()
        btn = qw.QPushButton(self)
        btn.setText("browse")
        self.problem = qw.QLineEdit(self)
        btn.clicked.connect(lambda: browse(self.problem))
        self.problem.setFixedWidth(250)
        self.problem.setText('athenak/inputs/linear_wave_hydro.athinput')
        load_layout.addWidget(btn)
        load_layout.addWidget(self.problem)'''

        self.l1 = qw.QLabel('Problems:')
        self.l1.setStyleSheet('font-weight: bold')
        predef_layout.addWidget(self.l1)
        self.combo = qw.QComboBox()
        self.combo.addItems(list(athena_problems))
        #predef_layout.addStretch()
        predef_layout.addWidget(self.combo)
    
        rbtn = qw.QRadioButton('Configure New')
        rbtn.toggled.connect(lambda: self.set_plot(True))
        rbtn.setChecked(True)  
        radio_layout.addWidget(rbtn)
        rbtn = qw.QRadioButton('Plot Existing')      
        rbtn.toggled.connect(lambda: self.set_plot(False))
        radio_layout.addWidget(rbtn)

        # btn_group.addButton(self.load_radio)
        #btn_group.addButton(self.predef_radio)
        self.radio_groups.append(btn_group)

        page_layout.addLayout(exe_layout)
        page_layout.addLayout(load_layout)
        page_layout.addLayout(predef_layout)
        page_layout.addLayout(radio_layout)
        # checkbox

        if False:
            self.reconfig = qw.QCheckBox('Reconfigure Executable')
            page_layout.addWidget(self.reconfig)
        else:
            print("no reconfig needed for athenak")

        widget = qw.QWidget()
        widget.setLayout(page_layout) 
        scroll = qw.QScrollArea()    #add scrollbar
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.resize(700, 300)
        self.setCentralWidget(scroll)

    def set_plot(self, b):
        self.plot = b

    def switch(self, type):
        self.combo.clear()
        if type == 'athena':
            self.combo.addItems(athena_problems)
            self.reconfig.setVisible(True)
        elif type == 'athenak':
            self.combo.addItems(athenak_problems)
            self.reconfig.setVisible(False)
        else:
            self.combo.addItems(athenac_problems)
            self.reconfig.setVisible(True)
        self.current_athena = type
        print("Current athena:",type)

    def clear(self):
        directories = glob('./*/')
        for d in directories:
            if path.exists(d + '.athena_prob_dir'):
                Popen(['rm', '-rf', d])

    def rebuild(self, problem):
        config = None
        with open(problem) as file:
            line = file.readline()
            while line:
                m = match('config[^=]+=(.+)', line)
                if m:
                    config = m.group(1)
                    break
                line = file.readline()
        w = ConfigWindow(config)
        w.show()
        w.run()
        w.close()

    def launch(self):
        if self.plot:
            problem = athena_problems[self.combo.currentText()]
            cmd = './pythena_run.py %s -x %s %s' % (problem, 
                                                    self.athena,
                                                    '-r' if args.run else '')
            print(cmd)
            try:
                if not path.exists(problem):
                    raise FileNotFoundError
                Popen(cmd.split())
            except Exception as e:
                print(e)
        else:
            folder = qw.QFileDialog.getExistingDirectory(self, "Select Problem Directory", "")
            if folder:
                cmd1 = 'python plot1d.py  -d %s/tab' % folder
                cmd2 = 'python plot1d.py  -d %s --hst' % folder
                print(cmd1)
                print(cmd2)
                Popen(cmd1.split())
                Popen(cmd2.split())

    def help(self):
        w = HelpWindow()
        self.windows.append(w)
        w.show()

    def quit(self):
        self.close()

# deprecate        
class ConfigWindow(qw.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle('Rebuilding Executable')
        self.main_layout = qw.QVBoxLayout()
        bash_label = qw.QLabel('./reconfig.sh ' + self.config)
        bash_label.setStyleSheet('font-weight: bold')
        bash_label.setFont(qg.QFont('Courier New', 10))
        self.main_layout.addWidget(bash_label)
        self.txt = qw.QLabel()
        self.txt.setFont(qg.QFont('Courier New', 10))
        self.main_layout.addWidget(self.txt)
        self.setLayout(self.main_layout)

    def run(self):
        p = Popen(['./reconfig.sh', self.config], stdout=PIPE)
        line = p.stdout.readline()
        while line:
            self.txt.setText(line.decode())
            qg.QGuiApplication.processEvents()
            line = p.stdout.readline()

class HelpWindow(qw.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Help')
        self.main_layout = qw.QVBoxLayout()
        self.add_label('Athena Version:', '\tThe version of Athena (must match the version of the executable) to be used')
        self.add_label('Athena Executable:', '\tEither the path or the name of the Athena executable. If only a name is given, then it is assumed that the executable is in /usr/bin.')
        self.add_label('Selecting Problems:', '\tA problem can either be selected from the list of predefined problems or a custom problem can be chosen. Use the radio buttons to choose which method to use.')
        self.setLayout(self.main_layout)

    def add_label(self, s1, s2):
        txt = qw.QLabel(s1)
        txt.setStyleSheet('font-weight: bold')
        self.main_layout.addWidget(txt)
        self.main_layout.addWidget(qw.QLabel(s2))


app = qw.QApplication(argv)

main = MainWindow()
main.show()

try:
    #print('opening window')
    exit(app.exec())
except:
    #print('closing window')
    pass
