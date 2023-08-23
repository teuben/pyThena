#! /usr/bin/env python
#
from PyQt5 import QtCore as qc, QtWidgets as qw, QtGui as qg

# utility imports
import os
from re import match
from aparser import parse_s as parse
from argparse import ArgumentParser
from os import getcwd, remove, environ, path
from subprocess import Popen, PIPE
from glob import glob
from sys import argv, exit

class MainWindow(qw.QMainWindow):

    def __init__(self, data, info):
        super(MainWindow, self).__init__()

        self.windows = []

        self.data = data
        self.info = info
        self.radio_groups = []
        self.sliders = {}
        self.input={}

        self.forced_slider = False

        self.initUI()

    # removes the trailing zeroes then the dot from a string float x, then returns an int
    # utility function used by build_layout
    def rm_dot(self, x):
        # being too precise causes problems, but hopefully this is enough
        s = '%.8g' % float(x)
        dot_pos = s.rfind('.')
        if dot_pos < 0:
            return int(s)
        s = s.replace('.', '')
        return int(s)

    def initUI(self):
        self.pagelayout = qw.QVBoxLayout()       # page layout
        self.dbtnlayout = qw.QHBoxLayout()       # layout for the default buttons
        self.elmtlayout = qw.QVBoxLayout()       # layout for the added widgets, stacks elements
        
        self.problayout = qw.QHBoxLayout()
        self.reflayout = qw.QHBoxLayout()
        self.outdirlayout = qw.QHBoxLayout()

        # run, save, load, quit, help buttons -> located in a toolbar
        toolbar = self.addToolBar("ToolBar")

        plot_action = qw.QAction('Run', self)
        plot_action.setToolTip('Run minik and Plot the output of the command ran under these configurations')

        run_action = qw.QAction('Dryrun', self)
        run_action.setToolTip('Output the command the would be ran when run')

        edit_action = qw.QAction('Edit', self)
        edit_action.setToolTip('Open the input file for editing')

        help_action = qw.QAction('Help', self)
        help_action.setToolTip('Display details about each configuration field')

        reset_action = qw.QAction('Reset', self)
        reset_action.setToolTip('Revert configuration options to default settings')

        quit_action = qw.QAction('Quit', self)
        quit_action.setToolTip('Exits the application')


        toolbar.addAction(plot_action)
        toolbar.addSeparator()
        toolbar.addAction(run_action)        
        toolbar.addSeparator()
        toolbar.addAction(edit_action)
        toolbar.addSeparator()
        toolbar.addAction(help_action)
        toolbar.addSeparator()
        toolbar.addAction(reset_action)
        toolbar.addSeparator()
        toolbar.addAction(quit_action)

        #add layouts to the page
        #self.pagelayout.addLayout(self.infolayout)
        self.pagelayout.addLayout(self.elmtlayout)
        #elf.pagelayout.addStretch()
        #self.pagelayout.addLayout(self.dbtnlayout) 

        # to set bold
        # self.label.setStyleSheet("font-weight: bold")

        l1 = qw.QLabel('Problem:')
        l1.setStyleSheet("font-weight: bold")
        l2 = qw.QLabel(info['problem'])
        self.problayout.addWidget(l1)
        self.problayout.addStretch()
        self.problayout.addWidget(l2)

        reference = info['reference']
        l1 = qw.QLabel('Layout:')
        l1.setStyleSheet("font-weight: bold")
        if reference:
            l2 = qw.QLabel(reference)
        else:
            l2 = qw.QLabel('N/A')
        self.reflayout.addWidget(l1)
        self.reflayout.addStretch()
        self.reflayout.addWidget(l2)

        l1 = qw.QLabel('Output Directory:')
        l1.setStyleSheet("font-weight: bold")
        l1.setToolTip('The directory where the output file will be dumped')
        self.outdirlayout.addWidget(l1)
        self.outdirlayout.addStretch()
        btn = qw.QPushButton(self)
        btn.setText("browse")
        def browse_dir(t):
            file = qw.QFileDialog.getExistingDirectory(self, "Select Directory", "")
            t.setText(file)
        txt = qw.QLineEdit(self)
        btn.clicked.connect(lambda: browse_dir(txt))
        txt.setFixedWidth(250)
        txt.setText(cwd)
        self.outdirlayout.addWidget(btn)
        self.outdirlayout.addWidget(txt)

        self.elmtlayout.addLayout(self.problayout)
        self.elmtlayout.addLayout(self.reflayout)
        self.elmtlayout.addLayout(self.outdirlayout)

        run_action.triggered.connect(lambda: self.run(txt, False))
        plot_action.triggered.connect(lambda: self.run(txt, True))
        edit_action.triggered.connect(self.view)
        help_action.triggered.connect(self.help)
        reset_action.triggered.connect(self.reset)
        quit_action.triggered.connect(self.quit)

        #run, save, load, quit, help button
        '''btn = qw.QPushButton(self)
        btn.setText("Run")
        btn.clicked.connect(lambda: self.run(txt, args.run))
        self.dbtnlayout.addWidget(btn)

        btn = qw.QPushButton(self)
        btn.setText("View File")
        btn.clicked.connect(self.view)
        self.dbtnlayout.addWidget(btn)

        btn = qw.QPushButton(self)
        btn.setText("Help")
        btn.clicked.connect(self.help)
        self.dbtnlayout.addWidget(btn)

        btn = qw.QPushButton(self)
        btn.setText("Reset")
        btn.clicked.connect(self.reset)
        self.dbtnlayout.addWidget(btn)
        
        btn = qw.QPushButton(self)
        btn.setText("Quit")
        btn.clicked.connect(self.quit)
        self.dbtnlayout.addWidget(btn)'''

        #set the main page layout
        widget = qw.QWidget()
        widget.setLayout(self.pagelayout) 
        scroll = qw.QScrollArea()    #add scrollbar
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.setGeometry(500, 100, 700, 500)
        self.setCentralWidget(scroll)

        self.createWidgetsFromGroups()
    
    def run(self, odir_input, plot):
        #print('run')
        cmd = f'cp {args.file} {odir_input.text()}'
        print(cmd)
        Popen(cmd.split())
        
        #cmd = f'{athena} -i {args.file} -d {odir_input.text()} output2/file_type=tab '
        cmd = f'{athena} -i {args.file} -d {odir_input.text()} '

        for k in self.data:
            e = data[k]
            t = e['gtype']

            if t == 'RADIO':
                for r in self.input[k]:
                    if r.isChecked():
                        cmd += f'{k}={r.text()} '
                        break
            elif t == 'CHECK' and self.input[k]:
                cmd += f'{k}='
                for c in self.input[k]:
                    if c.isChecked():
                        cmd += f'{c.text()},'
                cmd = cmd[:-1] + ' '
            else:
                cmd += '%s=%s ' % (k, self.input[k].text())

        print(cmd)
        # create odir (including intermediaries if needed)
        odir = odir_input.text()
        os.makedirs(odir,exist_ok=True)
        hname = f'{odir_input.text()}/history'
        with open(hname, 'w') as file:
            file.write(cmd)
        
        if plot:
            if not path.exists(athena):
                print('Athena not found\nExiting')
            # open the plot in a subprocess
            # remove the forward slash at the end if there is one
            if odir[-1] == '/':
                odir = odir[:-1]
            # remove the hst file since it always gets appended to
            # intentional?
            h = glob(odir + '/*.hst')
            if len(h) > 0:
                remove(h[0])
            # will the tlim variable always be like this?
            # display_pbar(cmd, values['time/tlim'])
            '''p = Popen(cmd.split())
            p.wait()'''
            w = LoadingWindow(cmd, float(self.input['time/tlim'].text()))
            self.windows.append(w)
            w.show()
            w.run()
            w.close()
            # @todo     only if tab files, fix for tab/vtk
            # @todo     solve when info['problem'] has spaces (as many do)
            #Popen(['python', 'plot1d.py', '-d', odir+'/tab',           '-n', info['problem']])
            #Popen(['python', 'plot1d.py', '-d', odir,         '--hst', '-n', info['problem'] + ' history'])
            cmd1 = 'python plot1d.py  -d %s/tab' % (odir)
            cmd2 = 'python plot1d.py  -d %s --hst' % (odir)
            print(cmd1)
            print(cmd2)
            Popen(cmd1.split())
            Popen(cmd2.split())
        else:
            w = DisplayWindow(cmd)
            self.windows.append(w)
            w.show()

    def view(self):
        #print('view')
        w = ViewerWindow()
        self.windows.append(w)
        w.show()
    
    def reset(self):
        for k in self.data:
            e = data[k]
            t = e['gtype']

            if t == 'RADIO':
                for r in self.input[k]:
                    if r.text() == e['value']:
                        r.setChecked(True)
                        break
            elif t == 'CHECK' and self.input[k]:
                defaults = e['value'].split(',')
                for c in self.input[k]:
                    c.setChecked(c.text() in defaults)
            elif t == 'SCALE':
                self.input[k].setText(str(e['value']))
                self.sliders[k]['key'].setValue(int(self.sliders[k]['factor'] * float(e['value'])))
            else:
                self.input[k].setText(str(e['value']))

    def quit(self):
        self.close()
        #print('quit')

    def help(self):
        #print('help')
        w = HelpWindow(self.data)
        size = w.main_layout.sizeHint()
        size.setWidth(size.width() + 10)
        size.setHeight(size.height() + 10)
        self.windows.append(w)
        w.show()

    def createWidgetsFromGroups(self):
        plabel = qw.QLabel('Parameters:')
        plabel.setStyleSheet("font-weight: bold")
        self.elmtlayout.addWidget(plabel)
        #self.elmtlayout.setSpacing(10)
        for k in data:
            e = data[k]
            t = e['gtype']
            tooltip = e['help'][1:].strip()
            if t == 'RADIO':
                new_group = qw.QButtonGroup()
                self.radio_groups.append(new_group)
                self.input[k] = []
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()

                for option in e['gparams'].split(','):
                    # option = option.strip()
                    radio_button = qw.QRadioButton(option)
                    self.input[k].append(radio_button)
                    new_group.addButton(radio_button)
                    group_layout.addWidget(radio_button)
                    if option == e['value']:
                        radio_button.setChecked(True)
                self.elmtlayout.addLayout(group_layout)

            elif t == "IFILE" or t == "OFILE":
                #print("browse files button created")
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()
                btn = qw.QPushButton(self)
                btn.setText("browse")
                txt = qw.QLineEdit(self)
                def browse_file(t):
                    file = qw.QFileDialog.getOpenFileName(self, "Select File", "")[0]
                    t.setText(file)
                btn.clicked.connect(lambda _, t=txt: browse_file(t))
                txt.setFixedWidth(250)
                txt.setText(e['value'])
                group_layout.addWidget(btn)
                group_layout.addWidget(txt)
                self.elmtlayout.addLayout(group_layout)
                self.input[k] = txt

            elif t == "IDIR" or t == 'ODIR':
                #print("browse directories button created")
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()
                btn = qw.QPushButton(self)
                btn.setText("browse")
                def browse_dir(t):
                    file = qw.QFileDialog.getExistingDirectory(self, "Select Directory", "")
                    t.setText(file)
                txt = qw.QLineEdit(self)
                btn.clicked.connect(lambda _, t=txt: browse_dir(t))
                txt.setFixedWidth(250)
                txt.setText(e['value'])
                group_layout.addWidget(btn)
                group_layout.addWidget(txt)
                self.elmtlayout.addLayout(group_layout)
                self.input[k] = txt

            elif t == "CHECK":
                #print("checkbox created")
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()
                values = e['value'].split(',')
                self.input[k] = []
                for option in e['gparams'].split(','):
                    #option = option.strip()
                    checkbox = qw.QCheckBox(option, self)
                    self.input[k].append(checkbox)
                    group_layout.addWidget(checkbox)
                    if option in values:
                        checkbox.setChecked(True)
                self.elmtlayout.addLayout(group_layout)

            
            elif t == "ENTRY":
                #print("textbox created")
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()
                txt = qw.QLineEdit(self)
                txt.setText(e['value'])
                txt.setFixedWidth(250)
                self.input[k] = txt
                group_layout.addWidget(txt)
                self.elmtlayout.addLayout(group_layout)

            elif t == "SCALE":
                group_layout = qw.QHBoxLayout()
                label = qw.QLabel(f'\t{k}:')
                label.setToolTip(tooltip)
                group_layout.addWidget(label)
                group_layout.addStretch()
                params = e['gparams'].split(':')

                #print("slider created")
                #creates a horizontal slider
                init = float(e['value'])
                label_slider = qw.QLineEdit(str(int(init) if init.is_integer() else init))
                label_slider.textEdited.connect(lambda value, key=k: self.update_slider(value, key))
                label_slider.setAlignment(qc.Qt.AlignRight)
                label_slider.setFixedWidth(85)
                # the label slider is unique to this slider
                # so we will use it to identify the slider
                factor = max([1 if float(x) == 0 else round(self.rm_dot(x) / float(x)) for x in params])
                slider = qw.QSlider(self)
                self.sliders[k] = {
                    'key':slider,
                    'factor':factor
                    #'is_int':params[0].isdigit() and params[1].isdigit() and params[2].isdigit()
                }
                [minimum, maximum, increment] = [float(x) for x in params]
                slider.setOrientation(qc.Qt.Horizontal)
                slider.setSingleStep(int(factor * increment))
                slider.setPageStep(int(factor * increment))       #moves the slider when clicking or up/down
                slider.setRange(int(factor * minimum), int(factor * maximum))
                slider.setValue(int(factor * init))

                slider.valueChanged.connect(lambda value, key=k, lbl=label_slider: self.updateLabel(key, lbl, value))
                
                slider.setFixedWidth(250)

                group_layout.addWidget(label_slider)
                group_layout.addWidget(slider)
                self.elmtlayout.addLayout(group_layout)
                self.input[k] = label_slider

    def update_slider(self, value, key):
        try:
            slider_info = self.sliders[key]
            slider = slider_info['key']
            minimum = slider.minimum()
            maximum = slider.maximum()
            fvalue = float(value) * slider_info['factor']
            if minimum <= fvalue <= maximum:
                self.forced_slider = True
                slider.setValue(int(fvalue))
        except:
            pass

    def updateLabel(self, key, label, value):
        if self.forced_slider:
            self.forced_slider = False
        else:
            slider_info = self.sliders[key]
            scaled = value/slider_info['factor']
            label.setText(str(int(scaled) if scaled.is_integer() else scaled))

class LoadingWindow(qw.QMainWindow):
    def __init__(self, cmd, tlim):
        super().__init__()

        self.setWindowTitle('Loading')
        self.cmd = cmd
        self.tlim = tlim
        self.pbar = qw.QProgressBar(self)
        self.setCentralWidget(self.pbar)

    def run(self):
        p = Popen(self.cmd.split(), stdout=PIPE)

        line = p.stdout.readline()

        while line:
            m = match('.*cycle=.* time=(.*) dt=.*', line.decode())
            if m:
                i = int(100 * float(m.group(1)) / self.tlim)
                self.pbar.setValue(i)
                # print(i, self.pbar.value())
                qg.QGuiApplication.processEvents()
            line = p.stdout.readline()

class ConfirmWindow(qw.QWidget):
    def __init__(self, parent):
        super().__init__()

        self.setWindowTitle('Confirm')

        self.par = parent

        layout = qw.QVBoxLayout()
        btn_layout = qw.QHBoxLayout()

        text = qw.QLabel('WARNING: You are about to override ' + args.file)
        layout.addWidget(text)

        btn = qw.QPushButton()
        btn.setText('Ok')
        btn.clicked.connect(self.ok)
        btn_layout.addWidget(btn)

        btn = qw.QPushButton()
        btn.setText('Cancel')
        btn.clicked.connect(self.cancel)
        btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def ok(self):
        self.par.ok = True
        self.close()

    def cancel(self):
        self.par.ok = False
        self.close()

class ViewerWindow(qw.QMainWindow):
    def __init__(self):
        super().__init__()
        global lines
        self.ok = False
        self.windows = []
        self.setWindowTitle(args.file)
        self.resize(750, 750)

        toolbar = self.addToolBar('ToolBar')

        load_action = qw.QAction('Load', self)
        load_action.setToolTip('Reload the GUI with this file')
        load_action.triggered.connect(self.load)
        toolbar.addAction(load_action)
        toolbar.addSeparator()

        save_as_action = qw.QAction('Save As', self)
        save_as_action.setToolTip('Save as a new file (Ctrl+Shift+s)')
        save_as_action.triggered.connect(self.save_as)
        save_as_action.setShortcut('Ctrl+Shift+s')
        toolbar.addAction(save_as_action)
        toolbar.addSeparator()

        save_action = qw.QAction('Save', self)
        save_action.setToolTip('Save changes to the original input file (Ctrl+s)')
        save_action.triggered.connect(self.save)
        save_action.setShortcut('Ctrl+s')
        toolbar.addAction(save_action)
        toolbar.addSeparator()

        quit_action = qw.QAction('Quit', self)
        quit_action.setToolTip('Closes the editor')
        quit_action.triggered.connect(self.quit)
        toolbar.addAction(quit_action)
        toolbar.addSeparator()

        layout = qw.QVBoxLayout()
        self.box = qw.QPlainTextEdit(''.join(lines), self)
        self.box.resize(750, 700)
        self.box.setFont(qg.QFont('Courier New', 10))
        layout.addWidget(self.box)

        #set the main page layout
        widget = qw.QWidget()
        widget.setLayout(layout) 
        # self.setGeometry(500, 100, 700, 500)
        self.setCentralWidget(widget)

        '''btn_layout = qw.QHBoxLayout()

        btn = qw.QPushButton()
        btn.setText('Load')
        btn.clicked.connect(self.load)
        btn_layout.addWidget(btn)

        btn = qw.QPushButton()
        btn.setText('Save As')
        btn.clicked.connect(self.save_as)
        btn.setShortcut('Ctrl+Shift+s')
        btn_layout.addWidget(btn)

        btn = qw.QPushButton()
        btn.setText('Save')
        btn.clicked.connect(self.save)
        btn.setShortcut('Ctrl+s')
        btn_layout.addWidget(btn)

        btn = qw.QPushButton()
        
        btn.setText('Quit')
        btn.clicked.connect(self.quit)
        btn_layout.addWidget(btn)
    
        layout.addLayout(btn_layout)'''

    def load(self):
        global data, info, lines, main
        lines = [line + '\n' for line in self.box.toPlainText().split('\n')]
        data, info, _ = parse(lines, silent=True)
        main.close()
        build_main(data, info)
        self.close()

    def save_as(self):
        filename, _ = qw.QFileDialog.getSaveFileName(self,
                                       'Save File',
                                       '',
                                       'All Files(*);;Text Files(*.txt);;AthenaK Input(*.athinput);;Athena Input(athinput.*)')
        if filename:
            with open(filename, 'w') as file:
                file.write(self.box.toPlainText())

    def save(self):
        w = ConfirmWindow(self)
        self.windows.append(w)
        w.setAttribute(qc.Qt.WA_DeleteOnClose)
        w.setWindowModality(qc.Qt.ApplicationModal)
        w.show()
        loop = qc.QEventLoop()
        w.destroyed.connect(loop.quit)
        loop.exec()
        if self.ok:
            with open(args.file, 'w') as file:
                file.write(self.box.toPlainText())

    def quit(self):
        self.close()

class DisplayWindow(qw.QWidget):
    def __init__(self, cmd):
        super().__init__()
        self.setWindowTitle('Athena Output')
        self.resize(500, 200)
        layout = qw.QVBoxLayout()
        line = qw.QPlainTextEdit(cmd, self)
        line.setFont(qg.QFont('Courier New', 10))
        layout.addWidget(line)
        self.setLayout(layout)

class HelpWindow(qw.QWidget):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle('Help')
        self.main_layout = qw.QVBoxLayout()
        for k in data:
            sublayout = qw.QHBoxLayout()
            l1 = qw.QLabel(k + ': ')
            l1.setStyleSheet("font-weight: bold")
            l2 = qw.QLabel(data[k]['help'][1:].strip())
            sublayout.addWidget(l1)
            sublayout.addWidget(l2)
            sublayout.addStretch()
            self.main_layout.addLayout(sublayout)
        self.setLayout(self.main_layout)

# building the gui

def build_main(data, info):
    global main
    main = MainWindow(data, info)

    # additions to the hint are needed to prevent the scrollbar from showing up
    size = main.pagelayout.sizeHint()
    size.setWidth(size.width() + 100)
    size.setHeight(size.height() + 50)

    main.resize(size)
    main.show()

cwd = getcwd()

# parse arguments
argparser = ArgumentParser(description='Runs the GUI for configuring an athinput file')
'''argparser.add_argument('-r', '--run',
                       action='store_true',
                       help='executes the athena command and plots the tab files on run',
                       default=False)'''
argparser.add_argument('-x', '--exe', help='the path to the athena executable')
argparser.add_argument('file', help='the athinput file to configure')
args = argparser.parse_args()

athena = args.exe if args.exe else (environ['AGUI'] if 'AGUI' in environ else cwd) + '/athena/bin/athena'

# parse the input files
with open(args.file) as file:
    lines = file.readlines()

data, info, _ = parse(lines, silent=True)

app = qw.QApplication(argv)

main = None

build_main(data, info)

try:
    #print('opening window')
    exit(app.exec())
except:
    #print('closing window')
    pass
