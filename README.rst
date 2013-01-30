=======
BP Diag
=======

Parse blood preasure statistics from data files and print them to STDERR.
You can also generate SVG charts from the data and export it to JSON.

To see a list of possible command line options run::

    bpdiag.py --help


Examples
========

Lets say we got a file called ``bp.csv`` containing the following values::

    136/83/65, 132/82/70
    144/82/86, 137/81/75, -,         143/80/68
    131/82/60, 144/82/64, 136/79/67, 140/80/62
    136/83/68, 138/80/99, -,         133/74/65
    136/79/67, 131/76/64, 135/81/72, 136/75/61
    127/79/72

**BP Diag** first tries to split multiple entries on each line using the
string given with the ``--delimiter`` option (default is ``,``). Each entry
found  is then split into *sys*, *dia* and *pulse* values with the string
given with the ``--seperator`` option (default: ``/``).

So if we run **BP Diag** on the file like this ``bpdiag.py bp.csv``, we got
the following results::

    Read 17 value(s) from 1 file(s)...
    Statistics (min, max, avg):
    :: SYS...: 127, 144, 136
    :: DIA...:  74,  83,  79
    :: PULSE.:  60,  99,  69

Dump JSON
---------

As you see parsing errors are ignored. We can dump JSON with the ``--json``
option. Only the JSON dump is written to *STDOUT*, other output goes to
*STDERR*, so we can redirect the dump to a file (use ``--compact`` to
prevent spaces after ``,`` and ``:``)::

    bpdiag.py --json --compact bp.csv > bp.json

The file ``bp.json`` will then contain one long line with the JSON data. You
can also dump the statistic gatherd from the data to JSON with the ``--json-
stats`` option.  Use the ``--sort`` and ``--indent 2`` options if you want a
more readable output.

Generate Charts
---------------

To generate SVG charts, you need to have PyGal_ installed (see below). Other
than that, just use the ``--chart`` option to have an chart called ``bp.svg``
generated in your current directory. There are more options to this, take a
look at the ``--help`` output.

Instead of the interactive SVG charts you can use PNG as output format. Just
use the ``--png`` option along with ``--chart``. You need a couple more
depnedensiec for that though, take a look below.


Install
=======

You can install **BP Diag** with pip_ or from source.

Install with pip
----------------

pip_ is "*a tool for installing and managing Python packages*". If you don't
have it installed, see the `pip install instructions`_::

    pip install --user bpdiag

Install from source
-------------------

You can fetch the latest sourceball_ from github and unpack it, or just clone
this repository: ``git clone git://github.com/brutus/bpdiag``. If you
got the source, change into the directory and use ``setup.py``::

    python setup.py install


Dependencies
============

PyGal_ is used to generate the charts. If you want to generate charts,
you need to install it. With pip_ it's as easy as this::

    pip install --user pygal

If you want to export to PNG files, you need CairoSVG_, tinycss_ and
cssselect_ too. You can install them like this::

    pip install --user CairoSVG tinycss cssselect


Bugs  and Contribution
======================

**BP Diag** is at home at: https://github.com/brutus/bpdiag/

If you find any bugs, issues or anything, please use the `issue tracker`_.


.. _home: https://github.com/brutus/bpdiag/
.. _sourceball: https://github.com/brutus/bpdiag/zipball/master
.. _`issue tracker`: https://github.com/brutus/bpdiag/issues
.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _`pip install instructions`: http://www.pip-installer.org/en/latest/installing.html
.. _PyGal: http://pygal.org/
.. _CairoSVG: http://cairosvg.org/
.. _tinycss: http://packages.python.org/tinycss/
.. _cssselect: http://packages.python.org/cssselect/
