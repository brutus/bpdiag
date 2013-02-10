#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
BP Diag
=======

**BP Diag** parses blood preasure statistics from data files, generates some
statistics and prints them to *STDERR*. You can export the data (and the
gathered statistics) to **JSON** (dump to *STDOUT*). And you can also generate
**SVG** or **PNG** charts from it.

Internals
---------

The **Measurement** class represent blood preasure measurements. Depending on
the kind of parser used, it contains various information; at least *SYS*,
*DIA*, and *PULSE* values.

The **Statistic** class collects all the parsed measurements as a list of
*Measurement* instances in the *data* attribute. It also calculates some
statistics over those measurements and makes them available as attributes.

Parsers
~~~~~~~

The :func:`read_files` function returns an iterater over all non-empty lines
in all provided files. This is the first argument to each parser. A parser
iterates over it and returns a list of *Measurement* instances.

Information on the available parsers (which function to call and which
arguments betsides the first one are needed) has to be collected in the
**PARSERS** dictionary.

It's quiete easy to write your own parsers: Just write a function that accepts
an *iterator* as its first argument and return a *list* of ``Measurement``
instances with the parsed data. To let **BP Diag** know about your parser you
also need to to fill the appropriate info into the *PARSERS* dictionary.


Dependencies
------------

PyGal_ is used to generate the charts. You can install it like this::

    pip install --user pygal

If you want to export to PNG files, you need CairoSVG_, tinycss_ and
cssselect_ too. You can install them like this::

    pip install --user CairoSVG tinycss cssselect

.. _PyGal: http://pygal.org/
.. _CairoSVG: http://cairosvg.org/
.. _tinycss: http://packages.python.org/tinycss/
.. _cssselect: http://packages.python.org/cssselect/

"""

__version__ = '0.5'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'

import sys
import argparse
import json
import itertools

try:
  import pygal
  from pygal.style import (
    DefaultStyle as DarkStyle,
    LightSolarizedStyle as LightStyle
  )
except ImportError:
  pass


PARSERS = {
  'plain': {
    'func': 'parse_plaintext',
    'args': ('entries', 'skip', 'seperator', 'delimeter', 'check')
  },
}


class BpdiagError(Exception):
  pass


class Measurement(object):

  """
  Represents a blood preasure measurement.

  The needed attributes are *sys* (systolic, maximum), *dia* (diastolic,
  minimum) - both in mm Hg - and *pulse* (arterial pulse per minute).

  You can set additional arbitrary attributes trough keywords, eg: date, time,
  or flags for irregular heartbeat or excessive movement, etc.

  """

  def __init__(self, sys, dia, pulse, **kwargs):
    self.sys = int(sys)
    self.dia = int(dia)
    self.pulse = int(pulse)
    for key, value in kwargs.items():
      setattr(self, key, value)

  def as_tuple(self):
    return (self.sys, self.dia, self.pulse)

  def as_dict(self):
    return self.__dict__.copy()

  def __str__(self):
    return "{0.sys:3}/{0.dia:3}/{0.pulse:3}".format(self)


class Statistic(object):

  """
  Collects and calculates statistics from *data*.

  *data* needs to be a list of :cls:`Measurement` instances.

  The main attributes are the following three lists: **sys** (all systolic
  values), **dia** (all diastolic values) and **pulse** (all pulse values).
  All three in the order of the measures in *data*.

  For each list (sys, dia, pulse) there are attributes for the min, max and
  avarage values: sys_min, sys_max, sys_avg, dia_min, dia_max, etc.

  """

  def __init__(self, data):
    self.data = data
    self.evaluate_data()

  def evaluate_data(self):
    """Build sys / dia / pulse list."""
    self.sys = []
    self.dia = []
    self.pulse = []
    for measure in self.data:
      for attr in ('sys', 'dia', 'pulse'):
        getattr(self, attr).append(getattr(measure, attr, None))
    # calculate statistics
    for attr, values in (
      ('sys', self.sys), ('dia', self.dia), ('pulse', self.pulse)
    ):
      values = filter(None, values)
      if values:
        setattr(self, attr + '_min', min(values))
        setattr(self, attr + '_max', max(values))
        setattr(self, attr + '_avg', sum(values) / len(values))
      else:
        for ending in ('_min', '_max', '_avg'):
          setattr(self, attr + ending, None)

  def as_dict(self):
    data = {}
    data['data'] = [m.as_dict() if m else None for m in self.data]
    for attr in self.__dict__:
      if attr != 'data':
        data[attr] = getattr(self, attr)
    return data

  def __nonzero__(self):
    return True if self.data else False


def parse_plaintext(
  lines,
  entries=0, skip='-', seperator='/', delimeter=',', check=False
):
  """
  Return a list of :cls:`Measurement` instances parsed from *lines*.

  *lines* can contain any number of sys/dia/pulse strings on each line.

  For each line **delimeter** is used to split multiple tokens on the line.
  And **seperator** is used to split the tokens into the sys, dia and
  pulse values.

  If **entries** is set to a value greather than 0, only that much tokens are
  used per line (even if there are more). If there are not enogh tokens on the
  line (less than *entries*), ``None`` values are used for those. If
  **skipped** is set too, entries that consist only of this string are also
  ignored and stored as ``None`` values.

  If *check* is ``None`` all errors are ignored. If ``True``, all errors are
  reported. If set to ``False`` only errors through skipped entries or missing
  ones (while *entries* is set) are ignored.

  """
  data = []
  # iterate over all non-empty lines
  for line in itertools.ifilter(None, (line.strip() for line in lines)):
    tokens = line.split(delimeter)  # get each token from the line
    # if *entries* is set, parse that much tokens, else parse all:
    for i in range(entries if entries else len(tokens)):
      try:
        token = tokens[i].strip()
        data.append(Measurement(*token.split(seperator)))
      except IndexError:
        # ``None`` for missing entries on the line if *entries*
        if not check and entries:
          data.append(None)
          continue
        if check is None:
          continue
        msg = "not enough measurements on line, needed {} got {} from '{}'"
        msg = msg.format(entries, len(line.split(delimeter)), line)
        raise BpdiagError(msg)
      except TypeError:
        # skipped entry or trailing whitespace?
        if not check and (
          (skip and token == skip) or
          (len(token) == 0 and len(tokens) - 1 == i)
        ):
          # store ``None`` if *entries*
          if entries:
            data.append(None)
          continue
        if check is None:
          continue
        msg = "wrong number of values in token, needed 3 got {} from '{}'"
        msg = msg.format(len(token.split(seperator)), token)
        raise BpdiagError(msg)
      except ValueError:
        if check is None:
          continue
        msg = "can't convert all values to INT: SYS: '{}', DIA: '{}', PULSE: '{}'"
        msg = msg.format(*token.split(seperator))
        raise BpdiagError(msg)
  return data


def output_chart(
  stats, filename='bpdiag.svg', png=False, light=False,
  dots=True, lines=True, fill=False
):
  """
  Generate a line-chart from *stats*.

  *stats* needs to be an instance of :cls:`Stats` (or similar).

  Per default an interactive SVG chart is generated under *filename*. If you
  set *png*, an PNG image is exported instead. If *light* is set, a light
  background is used, instead of the default dark one.

  If *dots* is set, each value is marked by a dot. If *lines* is set, the
  values are connected by lines. And if *fill* is set, the area between the
  floor and the lines is filled with the same color as the line.

  """
  style = LightStyle if light else DarkStyle
  chart = pygal.Line(
    show_dots=dots, stroke=lines, fill=fill, style=style
  )
  chart.add('sys', stats.sys)
  chart.add('dia', stats.dia)
  chart.add('pulse', stats.pulse)
  if png:
    if filename.endswith('.svg'):
      filename = filename[:-4] + '.png'
    chart.render_to_png(filename)
  else:
    chart.render_to_file(filename)


def get_argument_parser():
  """Return an ``ArgumentsParser`` instance."""
  ap = argparse.ArgumentParser(
    description=__doc__.split('\n\n')[1],
    usage="%(prog)s [OPTIONS] [OUTPUT [OUTPUT OPTIONS]].. [PARSER [PARSER OPTIONS]] FILENAME..",
  )
  # positionals
  ap.add_argument(
    'parser', choices=PARSERS.keys(), nargs='?', default='plain',
    help="select the parser to use (default: %(default)s)"
  )
  ap.add_argument(
    'filenames', nargs='+', metavar="FILENAME",
    help="files containing the raw data"
  )
  # options
  g_check = ap.add_mutually_exclusive_group()
  g_check.add_argument(
    '-N', '--check', dest='check', action='store_true', default=False,
    help="break on any parsing errors and report them"
  )
  g_check.add_argument(
    '-n', '--no-check', dest='check', action='store_const', default=False, const=None,
    help="ignore all parsing errors"
  )
  # output
  g_out = ap.add_argument_group('output')
  g_out.add_argument(
    '-c', '--chart', action='store_true',
    help="export data to chart"
  )
  g_out.add_argument(
    '-j', '--json', action='store_true',
    help="export to JSON as array of SYS, DIA, PULS arrays"
  )
  g_out.add_argument(
    '-J', '--json-obj', action='store_true',
    help="export to JSON as array of objects"
  )
  g_out.add_argument(
    '--json-stats', action='store_true',
    help="export statistics to JSON as object"
  )
  # charts
  g_chart = ap.add_argument_group('chart options')
  g_chart.add_argument(
    '-f', '--filename', default='bp.svg',
    help="filename of the chart (default: '%(default)s')"
  )
  g_chart.add_argument(
    '--png', action='store_true',
    help="render to PNG instead of interactive SVG"
  )
  g_chart.add_argument(
    '--light', action='store_true',
    help="render to a white background"
  )
  g_chart.add_argument(
    '--no-dots', action='store_true',
    help="don't draw dots"
  )
  g_chart.add_argument(
    '--no-lines', action='store_true',
    help="don't draw lines"
  )
  g_chart.add_argument(
    '--fill', action='store_true',
    help="fill lines"
  )
  # json
  g_json = ap.add_argument_group('json options')
  g_json.add_argument(
    '--indent', type=int, metavar='INT', default=None,
    help="set the number of spaces used as indent; 0 = newline (default: none)"
  )
  g_json.add_argument(
    '--compact', action='store_const', dest='separators',
    const=(',', ':'), default=(', ', ': '),
    help="skip emty spaces after `,` and `:`"
  )
  g_json.add_argument(
    '--sort', action='store_true',
    help="sort JSON dicts by key"
  )
  # parser :: plain
  g_plain = ap.add_argument_group(
    '[PARSER] plain',
    "Each line of a file is parsed for one or more SYS, DIA and PULSE value(s). "
    "A *seperator* and a *delimeter* is used for that. The *seperator* "
    "seperates the three values and the *delimeter* multiple entires on a line."
  )
  g_plain.add_argument(
    '-e', '--entries', metavar='INT', type=int, default=0,
    help="number of measures per line; 0 = all (default: '%(default)s')"
  )
  g_plain.add_argument(
    '--skip', metavar='STRING', default='-',
    help="denotes skipped values (default: '%(default)s')"
  )
  g_plain.add_argument(
    '--delimeter', metavar='STRING', default=',',
    help="splits multiple measures on one line (default: '%(default)s')"
  )
  g_plain.add_argument(
    '--seperator', metavar='STRING', default='/',
    help="splits measure string to sys/dia/pulse values (default: '%(default)s')"
  )
  return ap


def read_files(filenames):
  """Generator that yields every non-empty line of each fiel in *filenames*."""
  for filename in filenames:
    try:
      with open(filename) as fh:
        for line in fh:
          yield line
    except IOError:
      print >> sys.stderr, "WARN: Can't read from '{}'".format(filename)
      continue


def parse_data(lines, args):
  """
  Return the results of the given parser function.

  Use the global **PARSERS** data and *args* to determin wich parser to
  call and which arguments to use (as keywords). *lines* will always be the
  first positional argument to the call.

  """
  parser = PARSERS[args.parser]
  func = globals()[parser['func']]
  kwargs = {
    name: getattr(args, name) for name in parser['args'] if name in args
  }
  return func(lines, **kwargs)


def stats_as_string(stats):
  """Return a string containing the info from *stats*."""
  statstr =\
    "Statistics (min, max, avg):\n"\
    ":: SYS...: {0.sys_min:3}, {0.sys_max:3}, {0.sys_avg:3}\n"\
    ":: DIA...: {0.dia_min:3}, {0.dia_max:3}, {0.dia_avg:3}\n"\
    ":: PULSE.: {0.pulse_min:3}, {0.pulse_max:3}, {0.pulse_avg:3}"
  return statstr.format(stats)


def main(args=None):
  """
  Read from all given *filenames*, use the specified *parser*, generate
  *statistics* and print the requested *output*.

  All arguments are parsed from **args**. If *args* is ``None``, ``sys.argv``
  is used (the commandline).

  """
  try:
    # parse commandline
    args = get_argument_parser().parse_args(args)
    # parse data from all given files (iterative) and build statistics
    stats = Statistic(parse_data(read_files(args.filenames), args))
    print >> sys.stderr, "Parsed {} value(s)...".format(len(stats.data))
    if stats:
      print >> sys.stderr, stats_as_string(stats)
    # output: do some stuff
    if args.json:
      print json.dumps(
        [m.as_tuple() if m else None for m in stats.data],
        indent=args.indent, separators=args.separators, sort_keys=args.sort
      ), "\n\n"
    if args.json_obj:
      print json.dumps(
        [m.as_dict() if m else None for m in stats.data],
        indent=args.indent, separators=args.separators, sort_keys=args.sort
      ), "\n\n"
    if args.json_stats:
      print json.dumps(
        stats.as_dict(),
        indent=args.indent, separators=args.separators, sort_keys=args.sort
      ), "\n\n"
    if args.chart:
      output_chart(
        stats, args.filename, args.png, args.light,
        not args.no_dots, not args.no_lines, args.fill
      )
      print >> sys.stderr, "Generated chart: '{}'".format(args.filename)
  except BpdiagError as e:
    print >> sys.stderr,\
      "[ERROR] while parsing:", e
    return 2  # parsing error
  except NameError:
    print >> sys.stderr,\
      "[ERROR] For chart export you need to have PyGal installed."
    return 1  # library error
  except ImportError:
    print >> sys.stderr,\
      "[ERROR] For PNG export you need CairoSVG, tinycss and cssselect installed."
    return 1   # library error
  return 0  # no errors


if __name__ == '__main__':
  sys.exit(main())
