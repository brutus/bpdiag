=======
BP Diag
=======

--------------------------------
Parses Blood Pressure Statistics
--------------------------------

**BP Diag** parses blood pressure statistics from data files, generates some
statistics and prints them to *STDERR*. You can export the data (and the
gathered statistics) to **JSON** (dump to *STDOUT*). And you can also generate
**SVG** or **PNG** charts from it::

    bpdiag [OPTIONS] [OUTPUT [OUTPUT OPTIONS]].. [PARSER [PARSER OPTIONS]] FILENAME..

To see a list of possible command line options run::

    bpdiag.py --help


Examples
========

Lets say we got a file called ``bloodpressure.txt`` containing the following
values in a simple format. This is a good job for our *default parser* (there
are other **parsers**, but more on this later)::

    136/83/65, 132/82/70
    144/82/86, 137/81/75, -,         143/80/68
    131/82/60, 144/82/64, 136/79/67, 140/80/62
    136/83/68, 138/80/99, -,         133/74/65
    136/79/67, 131/76/64, 135/81/72, 136/75/61
    127/79/72

So if we run **BP Diag** over the file like this::

    bpdiag.py bloodpressure.txt

We got the following results::

    Parsed 17 value(s)...
    Statistics (min, max, avg):
    :: SYS...: 127, 144, 136
    :: DIA...:  74,  83,  79
    :: PULSE.:  60,  99,  69

We can also dump the results to **JSON** with ``--json`` or generate a line
chart from it with ``--chart`` (for more options see below).


Features
========

Modular Input: Parsers
----------------------

**Parsers** define how the input from the given files is transformed into
*Measurements* instances containing the data for each parsed measurement.

**BP Diag** comes with a couple of parsers, but it's easy to write your own if
they don't fit your needs (just take a look at the source documentation of
the module).

Parser: Plaintext
~~~~~~~~~~~~~~~~~

The *plaintext parser* is good to grab values from simple text files, like
copied from a note taking app or whatever. It's for files that just store a
couple of *SYS*, *DIA* and *PULSE* values.

For each line the ``--delimiter`` (default is ``,``) is used to split multiple
entries on the line. And ``--separator`` (default: ``/``) is used to split the
entries into the *SYS*, *DIA* and *PULSE* values. Entries that just contain
the ``--skip`` string (default: ``-``) are skipped.

Number of measurements per line
+++++++++++++++++++++++++++++++

Per default all values are gathered one after the other. But you can use the
``--entries`` option to set a fixed number of measurements per line.

What this means is that only that much values are used per line (even if there
are more) and if a line contains less than *entries* values, the remaining
ones are filled with ``None`` values. Also values that are the *skip* string
are not ignored but stored as a `None` value too.

This can be helpful in cases where you have a given number of measurements per
line and you want to keep them aligned even if sometimes a measurement is
skipped / missing.::

    bpdiag.py --json --compact --entries 4 bloodpressure.txt

Will result in the following JSON:

.. code:: json

    [[136,83,65],[132,82,70],null,null,[144,82,86],[137,81,75],null,[143,80,68],[131,82,60],[144,82,64],[136,79,67],[140,80,62],[136,83,68],[138,80,99],null,[133,74,65],[136,79,67],[131,76,64],[135,81,72],[136,75,61],[127,79,72],null,null,null]

Output
------

As we already seen, you will always get some statistics-output to *STDERR*.
But you can also export the gathered data to a number of formats:

Export JSON
~~~~~~~~~~~

There are a couple of ways to do this, but always the JSON dump is written to
*STDOUT*, so you can redirect the dump to a file.

You can dump the data as an array of SYS, DIA, PULS arrays with the ``--json``
option. Or as an array of objects with the ``--json-obj`` option (this will
include all attributes of the *Measurement* instances, not just *SYS*, *DIA*
and *PULSE*). If you want the gathered statistics too, use ``--json-stats``.

There are a couple of options to govern how the dump is formated, see the
``--help`` output for info on that.

Export Chart
~~~~~~~~~~~~

To generate SVG charts, you need to have PyGal_ installed (see below). Other
than that, just use the ``--chart`` option to have a chart called ``bp.svg``
generated in your current directory. There are more options to this, take a
look at the ``--help`` output.

Instead of the interactive SVG charts you can use PNG as output format. Just
use the ``--png`` option along with ``--chart``. You need a couple more
dependencies for that though, take a look below.


Install
=======

You can install **BP Diag** with pip_ or from source.

**Install with pip**

pip_ is "*a tool for installing and managing Python packages*". If you don't
have it installed, see the `pip install instructions`_::

    pip install --user bpdiag

**Install from source**

You can fetch the latest sourceball_ from github and unpack it, or just clone
this repository: ``git clone git://github.com/brutus/bpdiag``. If you
got the source, change into the directory and use ``setup.py``::

    python setup.py install

Dependencies
------------

PyGal_ is used to generate the charts. If you want to generate charts,
you need to install it. With pip_ it's as easy as this::

    pip install --user pygal

If you want to export to PNG files, you need CairoSVG_, tinycss_ and
cssselect_ too. You can install them like this::

    pip install --user CairoSVG tinycss cssselect


Bugs  and Contribution
======================

**BP Diag** is at home at: https://github.com/brutus/bpdiag/

If you want to run the test cases, see that you got nose_ installed and run
``nosetests`` from the ``bpdiag`` directory (the one containing the module).
If you got **bpdiag** already installed, run them like this: ``nosetest
test_bpdiag``.

If something fails, please get in touch.

If you find any bugs, issues or anything, please use the `issue tracker`_.


.. _home: https://github.com/brutus/bpdiag/
.. _sourceball: https://github.com/brutus/bpdiag/zipball/master
.. _`issue tracker`: https://github.com/brutus/bpdiag/issues
.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _`pip install instructions`: http://www.pip-installer.org/en/latest/installing.html
.. _nose: https://nose.readthedocs.org/en/latest/
.. _PyGal: http://pygal.org/
.. _CairoSVG: http://cairosvg.org/
.. _tinycss: http://packages.python.org/tinycss/
.. _cssselect: http://packages.python.org/cssselect/
