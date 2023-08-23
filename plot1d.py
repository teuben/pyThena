#! /usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button, Slider, CheckButtons, TextBox
from argparse import ArgumentParser
import glob
import os
import matplotlib.style as mplstyle
mplstyle.use(['ggplot', 'fast'])

# TODO list
# round buttons
# round check boxes
# nonlinear (logarithmic?) slider

# IMPORTING FROM ANIMATE2
# function that draws each frame of the animation
def animate(i):
    global xcol, ycol, current_frame, xlim, ylim
    # print(f[i])
    d = np.loadtxt(f[i]).T
    x = d[ixcol]
    y = d[iycol]
    if not args.hst:
        with open(f[i]) as file:
            # first line is target
            # terribly lazy but it works, maybe just use regex
            time = file.readline().split('=')[1].split(' ')[0]
    ax.clear()
    if xlim:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    ax.plot(x, y)
    if not xlim and args.fix: # just need to check one since its either both or none
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
    if not args.hst:
        ax.set_title(f'Time: {float(time)}', loc='left')
    else:
        ax.set_title(f'History', loc='left')
    ax.set_xlabel(xcol)
    ax.set_ylabel(ycol)
# END IMPORT

# hard-pauses the animation
# that is, the only way to unpause is by using the play or restart button
def hpause(self=None):
    global hard_paused, is_playing
    hard_paused = True
    is_playing = False
    #bpause.color = '0.5'
    bplay.label.set_text('$\u25B6$')
    pause()

def play(self=None):
    global is_playing
    if is_playing:
        hpause()
    else:
        resume()

# pauses the animation
def pause(self=None):
    global is_playing, fig
    if is_playing:
        fig.canvas.stop_event_loop()
        is_playing = False

# plays the animation (either starts or resumes)
def resume(self=None):
    global is_playing, current_frame, ax, length, frame_sliding, hard_paused
    if not is_playing:
        bplay.label.set_text('$\u25A0$')
        is_playing = True
        hard_paused = False
        #bpause.color = '0.85'
        while current_frame < length and is_playing:
            animate(current_frame)
            current_frame += 1
            fig.canvas.draw_idle()
            fig.canvas.start_event_loop(delay)
            frame_sliding = False
            fslider.set_val(current_frame)
        is_playing = False
        if loop and current_frame == length:
            restart()

# loops the animation
def loopf(self=None):
    global loop, bloop
    if loop:
        bloop.color = '0.85' # this is the default color
    else:
        bloop.color = '0.5' # highlighted color
    loop = not loop

# restarts the animation from the beginning
def restart(self=None):
    global current_frame, xlim
    xlim = None
    pause()
    current_frame=0
    resume()

# select the horizontal variable
def select_h(label):
    global current_frame, ycol, xlim
    update_cols(label, ycol)
    if not hard_paused:
        restart()
    else:
        xlim = None
        animate(current_frame)
        fig.canvas.draw_idle()

# select the verticle variable
def select_v(label):
    global current_frame, xcol, xlim
    update_cols(xcol, label)
    if not hard_paused:
        restart()
    else:
        xlim = None
        animate(current_frame)
        fig.canvas.draw_idle()

def update_cols(x, y):
    global xcol, ycol, ixcol, iycol
    xcol=x
    ycol=y
    ixcol = variables.index(x)
    iycol = variables.index(y)

def update_delay(x):
    global delay
    delay = x / 1000

def update_fslider(n):
    global frame_sliding, current_frame
    current_frame = n
    animate(current_frame - 1)
    fig.canvas.draw_idle()

'''def fix_axes(v):
    global xlim, ylim
    if v == 'Fix X':
        xlim = ax.get_xlim() if not xlim else None
    else:
        ylim = ax.get_ylim() if not ylim else None'''

def mouse_moved(e):
    if e.inaxes == fax:
        pause()
    elif not hard_paused:
        resume()

argparser = ArgumentParser(description='plots the athena tab files specified')
argparser.add_argument('-d', '--dir', help='the athena run directory containing tab/ or *.tab files', required=True)
argparser.add_argument('--hst', action='store_true', help='plots the hst file rather animating the tab files')
argparser.add_argument('-n', '--name', help='name of the problem being plotted') # primarily just used by the other gui
argparser.add_argument('-f', '--fix', action='store_true', help='fixes the x and y axes of the animation based on the animation\'s first frame')
args = argparser.parse_args()

# fnames='run1/tab/LinWave*tab'
if args.hst:
    f = glob.glob(args.dir + '/*.hst')
else:
    if os.path.exists(args.dir + '/tab'):
        # athena++/athenak style
        f = glob.glob(args.dir + '/tab/*.tab')
    else:
        # athenac style
        f = glob.glob(args.dir + '/*.tab')
f.sort()
length = len(f)
#print('DEBUG: %s has %d files' % (fnames,len(f)))

# global vars
current_frame = 0
is_playing = False
hard_paused = True
loop = False
frame_sliding = False
xlim = None
ylim = None

# plot settings
left = 0.34
bottom = 0.25
top = 0.85

# change plot settings if plotting a hst file
if args.hst:
    top = 0.9
    bottom = 0.1

# the time in seconds between frames
delay = 100 / 1000

# getting the variable names
with open(f[0]) as file:
    file.readline()
    # regular tab file have as 2nd line
    # i       x1v         rho ...               for athena
    # gid   i       x1v         dens ...        for athenak
    line2 = file.readline()
    variables = line2.split()[1:]

    # history files have as 2nd line
    # [1]=time      [2]=dt       [3]=mass ...
    # @todo  AthenaC has spaces in the column names, would need a different parsers
    if args.hst:
        print("DEBUG hst",line2)
        variables = [v.split('=')[1] for v in variables]
    print("tab variables detected:",variables)

var_len = len(variables)

# 0-based, change from animate2
xcol=variables[0]
ycol=variables[0]
ixcol = 0
iycol = 0

# plotting configuration
fig, ax = plt.subplots()
fig.subplots_adjust(left=left, bottom=bottom, top=top) # old bottom was 0.34
# plt.rcParams['font.family'] = 'Arial'
# pause on close otherwise we might freeze
fig.canvas.mpl_connect('close_event', pause)
# fig.set_size_inches(10, 10)

plt.get_current_fig_manager().set_window_title(args.name if args.name else f[0].split('.')[0])

rheight = var_len / 25
rwidth = 0.045
rdleft = 0.03
rbot = (bottom + top - rheight) / 2

rax = fig.add_axes([rdleft, rbot, rwidth, rheight])

# @todo   label_props and radio_props don't appear until python 3.10.x 

radio = RadioButtons(rax, 
                     tuple(variables), 
                     label_props={'color': ['white' for _ in variables]},
                     radio_props={'color': ['#1f77b4' for _ in variables], 'edgecolor': ['black' for _ in variables]}
                     )
rax.axis('off') # removes the border around the radio buttons
radio.on_clicked(select_h)

# use same axes to add text in order to make it easier to adjust
rax.text(-0.055, 0.05, 'X')
rax.text(0.055, 0.05, 'Y')

rax = fig.add_axes([rdleft + 0.015, rbot, 0.25, rheight])
radio2 = RadioButtons(rax, 
                      tuple(variables), 
                      radio_props={'color': ['#1f77b4' for _ in variables], 'edgecolor': ['black' for _ in variables]}
                      )
rax.axis('off')
radio2.on_clicked(select_v)

if not args.hst:

    bwidth = 0.04
    bheight = 0.05
    bspace = 0.02
    bstart = 0.05

    brestart = Button(fig.add_axes([bstart, 0.125, bwidth, bheight]), '$\u21A9$')
    brestart.on_clicked(restart)

    bplay = Button(fig.add_axes([bstart + bwidth + bspace, 0.125, bwidth, bheight]), '$\u25B6$')
    bplay.on_clicked(play)

    bloop = Button(fig.add_axes([bstart + 2 * bwidth + 2 * bspace, 0.125, bwidth, bheight]), '$\u27F3$')
    bloop.on_clicked(loopf)

    # make slider nonlinear
    delay_slider = Slider(
        ax=fig.add_axes([0.18, 0.05, 0.65, 0.03]),
        label='Delay (ms)',
        valmin=0,
        valmax=20,
        valinit=5,
    )

    delay_slider.on_changed(update_delay)

    fax = fig.add_axes([0.18, 0.95, 0.65, 0.03])
    fslider = Slider(
        ax=fax,
        label='Frame',
        valmin=1,
        valmax=length,
        valinit=1,
        valstep=1
    )

    fslider.on_changed(update_fslider)

    '''cbax = fig.add_axes([bstart + 3 * bwidth + 3 * bspace, 0.09, 0.1, 0.125])
    fix_cbox = CheckButtons(
    ax=cbax,
    labels=[' Fix X', ' Fix Y']
    )
    cbax.axis('off')

    fix_cbox.on_clicked(fix_axes)'''

    '''twidth = 0.1
    theight = 0.04
    txstart=0.35
    tspace = 0.075
    tystart1 = 0.11
    tystart2 = tystart1 + 0.05
    
    xmin_ax = fig.add_axes([txstart, tystart1, twidth, theight])
    xmin_box = TextBox(
        ax=xmin_ax,
        label='min '
    )

    xmin_ax.text(-0.9, 0.25, 'X:')

    xmax_box = TextBox(
        ax=fig.add_axes([txstart + twidth + tspace, tystart1, twidth, theight]),
        label='max '
    )

    xscale_box = TextBox(
        ax=fig.add_axes([txstart + 2*twidth + 2*tspace, tystart1, twidth, theight]),
        label='scale '
    )

    ymin_ax = fig.add_axes([txstart, tystart2, twidth, theight])
    ymin_box = TextBox(
        ax=ymin_ax,
        label='min '
    )

    ymin_ax.text(-0.9, 0.25, 'Y:')

    ymax_box = TextBox(
        ax=fig.add_axes([txstart + twidth + tspace, tystart2, twidth, theight]),
        label='max '
    )

    yscale_box = TextBox(
        ax=fig.add_axes([txstart + 2*twidth + 2*tspace, tystart2, twidth, theight]),
        label='scale '
    )'''

    # in order to pause the animation when using the frame slider
    fig.canvas.mpl_connect('motion_notify_event', mouse_moved)

plt.show()
