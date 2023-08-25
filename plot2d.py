#! /usr/bin/env python
#
#     plot2d:    animate images
#
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button, Slider, CheckButtons, TextBox
from argparse import ArgumentParser
import athena_read
import glob
import os
import sys
import matplotlib.style as mplstyle
from mpl_toolkits.axes_grid1 import make_axes_locatable
#mplstyle.use(['ggplot', 'fast'])

# TODO list
# round buttons
# round check boxes
# nonlinear (logarithmic?) slider

kwargs = {}
kwargs['variable'] = 'dens'
kwargs['dimension'] = 'z'
kwargs['location'] = 0
kwargs['vmin'] = None
kwargs['vmax'] = None
kwargs['norm'] = 'linear'
kwargs['cmap'] = 'rainbow'
kwargs['cmap'] = 'gist_rainbow'
kwargs['cmap'] = 'viridis'
kwargs['x1_min'] = None
kwargs['x1_max'] = None
kwargs['x2_min'] = None
kwargs['x2_max'] = None
kwargs['output_file'] = None

zvar = 'dens'

# https://saturncloud.io/blog/how-to-animate-the-colorbar-in-matplotlib-a-guide/

def animate(i):
    global xcol, ycol, current_frame, xlim, ylim, kwargs
    kwargs['variable'] = zvar
    if False:
        d = athena_read.bin(f[i],False,**kwargs)
    else:
        d = data[i][zvar][0]
    time = data[i]['time']
    xlim = data[i]['xlim']
    ylim = data[i]['ylim']
    extent=[xlim[0],xlim[1],ylim[0],ylim[1]]
    #sax.set_xlim((-0.5,0.5))
    

    ax.clear()
    #ax.set_xlim(xlim)
    #ax.set_ylim(ylim)
    if True:
        im = ax.imshow(d,cmap=kwargs['cmap'],  # norm=norm, vmin=vmin, vmax=vmax,
                       interpolation='none', origin='lower', extent=extent)
                       
        
        # @todo    this fig.colorbar() will recursively die
        # fig.colorbar(im, cax=cax, orientation='vertical')
    else:
        # now broken after using extent=
        im = ax.imshow(d,cmap=kwargs['cmap'],  # norm=norm, vmin=vmin, vmax=vmax,
                       interpolation='none', origin='lower', extent=extent)
        x = np.arange(d.shape[0])
        y = np.arange(d.shape[1])
        cs = ax.contour(x,y,d,extent=extent)
                       
    if not xlim and args.fix: # just need to check one since its either both or none
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
    ax.set_title(f'{zvar}  Time: {float(time)}', loc='left')
    ax.set_xlabel('x')
    ax.set_ylabel('y')

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

# select the variable
def select_v(label):
    global current_frame, xcol, xlim, zvar
    update_cols(xcol, label)
    if not hard_paused:
        restart()
    else:
        xlim = None
        animate(current_frame)
        fig.canvas.draw_idle()
    print('select_v',label)
    zvar = label
    kwargs['variable'] = zvar
    reload_data()

def update_cols(x, y):
    global xcol, ycol, ixcol, iycol
    xcol=x
    ycol=y
    ixcol = variables.index(x)
    iycol = variables.index(y)

def update_delay(x):
    global delay
    delay = x / 1000
    #  something odd about setting the delay
    # print("DELAY:",delay)

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

def reload_data():
    global data
    print("Reading %d data-frames for %s" % (length,zvar))
    for i in range(len(f)):
        data[i] = athena_read.bin(f[i],False,**kwargs)
    

argparser = ArgumentParser(description='plots the athena tab files specified')
argparser.add_argument('-d', '--dir', help='the athena run directory containing tab/ or *.tab files', required=True)
argparser.add_argument('-n', '--name', help='name of the problem being plotted') # primarily just used by the other gui
argparser.add_argument('-f', '--fix', action='store_true', help='fixes the x and y axes of the animation based on the animation\'s first frame')
args = argparser.parse_args()

f = glob.glob(args.dir + '/bin/*.bin')
f.sort()
length = len(f)

if length==0:
    print("No bin data found")
    sys.exit(0)

data = list(range(len(f)))
reload_data()


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

# the time in seconds between frames
delay = 100 / 1000

# getting the variable names
variables = athena_read.bin(f[0],True)
print("bin variables detected:",variables)
var_len = len(variables)

# 0-based, change from animate2
xcol=variables[0]
ycol=variables[0]
ixcol = 0
iycol = 0

# plotting configuration
fig, ax = plt.subplots()
fig.subplots_adjust(left=left, bottom=bottom, top=top) # old bottom was 0.34
divider = make_axes_locatable(ax)
cax = divider.append_axes('right', size='5%', pad=0.05)
sax = ax.secondary_xaxis('bottom')
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


# use same axes to add text in order to make it easier to adjust
# rax.text(-0.055, 0.05, 'X')
rax.text(0.055, 0.05, 'Y')

# rax = fig.add_axes([rdleft + 0.015, rbot, 0.25, rheight])
radio2 = RadioButtons(rax, 
                      tuple(variables), 
                      radio_props={'color': ['#1f77b4' for _ in variables], 'edgecolor': ['black' for _ in variables]}
                      )
rax.axis('off')
radio2.on_clicked(select_v)

if True:

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
        valmin=1,
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


    # in order to pause the animation when using the frame slider
    fig.canvas.mpl_connect('motion_notify_event', mouse_moved)

plt.show()
