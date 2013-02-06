#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
BP Diag

**BP Diag** parses blood preasure statistics from data files, generates some
statistics and prints them to *STDERR*. You can export the data (and the
gathered statistics) to **JSON** (dump to *STDOUT*). And you can also generate
**SVG** or **PNG** charts from it.

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

__version__ = '0.3'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'

import sys
import argparse
import json

try:
  import pygal
  from pygal.style import DefaultStyle, LightSolarizedStyle
except ImportError:
  pass


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


class Stats(object):

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


def parse_simple(lines, entries=0, skip='-', seperator='/', delimeter=',', check=False):
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
  reported. If set to ``False`` only errors through missing or skipped entries
  while *entries* is set are ignored.

  """
  data = []
  for line in [line.strip() for line in lines]:
    if not line:
      continue
    tokens = line.split(delimeter)  # get each token from the line
    # if *entries* is set, parse that much tokens, else parse all:
    for i in range(entries if entries else len(tokens)):
      try:
        token = tokens[i].strip()
        data.append(Measurement(*token.split(seperator)))
      except IndexError:
        if entries and not check:
          # ``None`` for missing entries on the line
          data.append(None)
          continue
        if check is None:
          continue
        msg = "not enough measurements on line, needed {} got {} from '{}'"
        msg = msg.format(entries, len(line.split(delimeter)), line)
        raise BpdiagError(msg)
      except TypeError:
        if entries and not check:
          # ``None`` for skipped entries on the line or trailing whitespace
          if (skip and token == skip) or (len(token) == 0 and len(tokens) - 1 == i):
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


def generate_chart(
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
  style = LightSolarizedStyle if light else DefaultStyle
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


def parse_args(args):
  """
  Return arguments parsed from *args*.

  If *args* is ``None``, ``sys.argv`` is used (the commandline).

  """
  ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[1])
  ap.add_argument(
    'filenames', nargs='+', metavar="FILENAME",
    help="files containing the raw data"
  )
  g_out = ap.add_argument_group('Output')
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
  g_chart = ap.add_argument_group('Chart')
  g_chart.add_argument(
    '-f', '--filename', default='bp.svg',
    help="filename of the chart (default: 'bp.svg')"
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
  g_json = ap.add_argument_group('JSON')
  g_json.add_argument(
    '--indent', type=int, metavar='INT', default=None,
    help="set the number of spaces used as indent (default=none, 0=newline)"
  )
  g_json.add_argument(
    '--compact', action='store_const', dest='separators',
    const=(',', ':'), default=(', ', ': '),
    help="skip emty spaces after `,` and `:`."
  )
  g_json.add_argument(
    '--sort', action='store_true',
    help="sort JSON dicts by key."
  )
  g_parse = ap.add_argument_group('Parsing')
  g_parse.add_argument(
    '--check', dest='check', action='store_true', default=False,
    help="break on any parsing errors and report them"
  )
  g_parse.add_argument(
    '--no-check', dest='check', action='store_const', default=False, const=None,
    help="ignore all parsing errors"
  )
  g_psimple = ap.add_argument_group('Parsing - Simple')
  g_psimple.add_argument(
    '-e', '--entries', metavar='INT', type=int, default=0,
    help="number of measures per line (default: 0=all)"
  )
  g_psimple.add_argument(
    '--skip', metavar='STRING', default='-',
    help="denotes skipped values (default: '-')"
  )
  g_psimple.add_argument(
    '--delimeter', metavar='STRING', default=',',
    help="splits multiple measures on one line (default: ',')"
  )
  g_psimple.add_argument(
    '--seperator', metavar='STRING', default='/',
    help="splits measure string to sys/dia/pulse values (default: '/')"
  )
  return ap.parse_args(args)


def main(args=None):
  # parse commandline
  args = parse_args(args)
  # collect data from all given files
  lines = []
  bad_files = 0
  for filename in args.filenames:
    try:
      with open(filename) as fh:
        lines.extend(fh.readlines())
    except IOError:
      print >> sys.stderr, "WARN: Can't read from '{}'".format(filename)
      bad_files += 1
      continue
  # parse data
  try:
    data = parse_simple(
      lines, args.entries, args.skip, args.seperator, args.delimeter, args.check
    )
    print >> sys.stderr, "Read {} value(s) from {} file(s)...".format(
      len(data), len(args.filenames) - bad_files
    )
    # delete some stuff we don't need anymore...
    del lines
    del bad_files
  except BpdiagError as e:
    print >> sys.stderr, "[ERROR] while parsing '{}': {}".format(filename, e)
    return 2  # parsing error
  # generate stats
  stats = Stats(data)
  del data  # we no longer need this
  if stats:
    print >> sys.stderr,\
      "Statistics (min, max, avg):\n"\
      ":: SYS...: {0.sys_min:3}, {0.sys_max:3}, {0.sys_avg:3}\n"\
      ":: DIA...: {0.dia_min:3}, {0.dia_max:3}, {0.dia_avg:3}\n"\
      ":: PULSE.: {0.pulse_min:3}, {0.pulse_max:3}, {0.pulse_avg:3}".format(stats)
  # do some stuff
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
    try:
      generate_chart(
        stats, args.filename, args.png, args.light,
        not args.no_dots, not args.no_lines, args.fill
      )
      print >> sys.stderr, "Generated chart: '{}'".format(args.filename)
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
