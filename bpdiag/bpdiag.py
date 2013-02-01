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


class Stats(object):

  """
  Collects and calculates statistics from *data*.

  *data* needs to be a list of sys/dia/pulse tuples.

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
    self.sys = []
    self.dia = []
    self.pulse = []
    for measure in self.data:
      try:
        sys, dia, pulse = measure
      except TypeError:
        sys = dia = pulse = None
      for attr, value in ((self.sys, sys), (self.dia, dia), (self.pulse, pulse)):
        attr.append(value)
    for attr, values in (('sys', self.sys), ('dia', self.dia), ('pulse', self.pulse)):
      values = filter(None, values)
      setattr(self, attr + '_min', min(values))
      setattr(self, attr + '_max', max(values))
      setattr(self, attr + '_avg', sum(values) / len(values))

  def as_dict(self):
    return self.__dict__


def parse_data(filename, entries=0, delimeter=',', seperator='/', check=False):
  """
  Return a list of sys/dia/pulse tuples parsed from *filename*.

  *deli* is used to split multiple maesurements on one line,
  *seperator* is used to split the sys/dia/pulse tokens into the three values.

  If *entries* is set, only that much measures are used per line (even if
  there are more). If a line contains less than *entries* measures, the
  remaining ones are filled with ``None`` values.

  """
  data = []
  with open(filename) as fh:
    for line in fh:
      # get each mesurement / token from the line
      tokens = line.split(delimeter)
      # if *entries* is set parse that much tokens else parse all
      for i in range(entries if entries else len(tokens)):
        try:
          sys, dia, pulse = [int(x) for x in tokens[i].split(seperator)]
          data.append((sys, dia, pulse))
        except (IndexError, ValueError):
          # if *check* report any parsing errors
          if check:
            raise
          # if *entries* store ``None`` value
          if entries:
            data.append(None)
          # else just ignore the error and go on
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
    '-j', '--json', action='store_true',
    help="if set, export data to JSON"
  )
  g_out.add_argument(
    '-J', '--json-stats', action='store_true',
    help="if set, export statistics to JSON"
  )
  g_out.add_argument(
    '-c', '--chart', action='store_true',
    help="if set, export data to chart"
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
  g_parse = ap.add_argument_group('Parsing')
  g_parse.add_argument(
    '--check', action='store_true',
    help="break on any parsing errors and report them"
  )
  g_parse.add_argument(
    '-e', '--entries', metavar='INT', type=int, default=0,
    help="max. number of measures per line (default: 0=all)"
  )
  g_parse.add_argument(
    '-d', '--delimeter', metavar='STRING', default=',',
    help="splits multiple measures on one line (default: ',')"
  )
  g_parse.add_argument(
    '-s', '--seperator', metavar='STRING', default='/',
    help="splits measure string to sys/dia/pulse values (default: '/')"
  )
  return ap.parse_args(args)


def main(args=None):
  # parse commandline
  args = parse_args(args)
  # collect data from all given files
  data = []
  try:
    for filename in args.filenames:
      data.extend(parse_data(
        filename, args.entries, args.delimeter, args.seperator, args.check
      ))
  except (IndexError, ValueError) as e:
    print >> sys.stderr, "ERROR while parsing '{}': {}".format(filename, e)
    return 2  # parsing error
  print >> sys.stderr, "Read {} value(s) from {} file(s)...".format(
    len(data), len(args.filenames)
  )
  # generate stats
  stats = Stats(data)
  print >> sys.stderr,\
    "Statistics (min, max, avg):\n"\
    ":: SYS...: {0.sys_min:3}, {0.sys_max:3}, {0.sys_avg:3}\n"\
    ":: DIA...: {0.dia_min:3}, {0.dia_max:3}, {0.dia_avg:3}\n"\
    ":: PULSE.: {0.pulse_min:3}, {0.pulse_max:3}, {0.pulse_avg:3}\n".format(stats)
  # do some stuff
  if args.json:
    print json.dumps(
      data,
      indent=args.indent, separators=args.separators, sort_keys=args.sort
    )
  if args.json_stats:
    print json.dumps(
      stats.as_dict(),
      indent=args.indent, separators=args.separators, sort_keys=args.sort
    )
  if args.chart:
    try:
      generate_chart(
        stats, args.filename, args.png, args.light,
        not args.no_dots, not args.no_lines, args.fill
      )
      print >> sys.stderr, "Generated chart: '{}'".format(args.filename)
    except NameError:
      print >> sys.stderr,\
        "ERROR: For chart export you need to have PyGal installed."
      return 1  # library error
    except ImportError:
      print >> sys.stderr,\
        "ERROR: For PNG export you need: CairoSVG, tinycss and cssselect installed."
      return 1   # library error
  return 0  # no errors


if __name__ == '__main__':
  sys.exit(main())
