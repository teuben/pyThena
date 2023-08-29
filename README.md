# pyThena

**pyThena** is a simple athena (Athena-miniK) execution helper via a GUI
that loads an athinput file, where selected parameters can be changed.
Only handles simple 1D and 2D problem from selected athinput files
from **Athena-miniK**.

**pyThena** is derived from the
more generic [agui](https://github.com/teuben/agui), which is still under
development.


## Installation

After having obtained the source code for **pyThena**, Athena-miniK needs
to be installed within this source tree.  Here is an example for
a generic install:

      make build_athenak

and here an example install for a specific Mac/M1 case we encountered:

      make arm

If all of this fails to build athena, study the Makefile **ARM=** macro and find a good
compile option for your case. More to follow here on installation guidelines, link to
athenak wiki, etc.



## anaconda3 python

Few words on installing anaconda3? Of you don't have something running already,
this could be done within **pyThena** as well. 

      make build_python
      source anaconda3/python_start.sh

this works for both Linux and Mac (I/M)

## Running

For the GUI to work, your system needs to support the Qt graphics library, in addition
to this, its python interface. The **anaconda3** python distribution includes this, and
it known to work on both Linux and Mac (both Intel and M1/M2).

An example run to certify everything is running fine. Of course at each of these steps
something *could* fail:

1.  Run the command **./pythena.py**, and a window should appear. Do this from a terminal
    with the correct python environment.
 
2.  Click on **Launch** (top left) to start the default **linear_wave_hydro.athinput**. This
    will bring up a window with a number of Parameters than can be changed, as well as an
    output directory (set to **run1** by default). We leave everything as is.

3.  Click on **Run** (top left), and within a second two matplotlib windows should appear.

4.  The "hst" (history) window plots a selected X (usually **time**) vs. a selected Y. Pick
    **1-mom** for the Y variable and you should see a graph.   There is also a **Use Points**
    select button on the lower left to toggle between lines and dots.

5.  The "tab" (tables) window plots a selected X (usually **x1v**) vs. a selected Y. Pick
    **X=x1v** and **Y=dens** and you should see a sine-wave with an amplitude of 1e-3, as
    was one of the parameters (**problem/amp**)
    Click on the movie button to animate the tables and the wave should move to the left.

Notice that at several stages the actual terminal commands that are being executed are written to the screen.

