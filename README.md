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

and here an example install for a Mac M1:

      make arm

If all of this fails to build athena, study the Makefile ARM= macro and find a good
compile option. More to follow here on installation guidelines, link to
athenak wiki, etc.



## anaconda3 python

Few words on installing anaconda3. This can be done within **pyThena**, here's an example

      make build_python
      source anaconda3/python_start.sh


## Running

For the GUI to work, your system needs to support the Qt graphics library, in addition
to this, its python interface. The **anaconda3** python distribution includes this, and
it known to work on both Linux and Mac (both Intel and M1/M2).

