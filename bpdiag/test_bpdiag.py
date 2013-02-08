# -*- coding: UTF-8 -*-

from nose.tools import assert_equal, assert_raises

from bpdiag import (
  BpdiagError,
  Measurement, Stats,
  parse_simple
)


cases_measurement = (
  # args, kwargs, expected result as dict
  ((123, 83, 65), {}, {'sys': 123, 'dia': 83, 'pulse': 65}),
  (
    (132, 86, 72), {'date': '2013-01-23'},
    {'sys': 132, 'dia': 86, 'pulse': 72, 'date': '2013-01-23'}
  ),
)

cases_stats = {
  # expected results for *cases_measurement*
  'sys': [123, 132], 'dia': [83, 86], 'pulse': [65, 72],
  'sys_min': 123, 'sys_max': 132, 'sys_avg': 127,
  'dia_min': 83, 'dia_max': 86, 'dia_avg': 84,
  'pulse_min': 65, 'pulse_max': 72, 'pulse_avg': 68
}

cases_parse_simple = (
  # empty list
  ([], []), ([''], []), (['', '   ', '', ' '], []), (['', '\n  \n', '  ', '\n'], []),
  # one per line
  (['136/83/65'], [(136, 83, 65)]),
  (['136/83/65', '132/82/70', '144/82/86'], [(136, 83, 65), (132, 82, 70), (144, 82, 86)]),
  (['136/83/65', ' 132/82/70 ', ' 144/82/86'], [(136, 83, 65), (132, 82, 70), (144, 82, 86)]),
  (['136/83/65', ' ', '144/82/86'], [(136, 83, 65), (144, 82, 86)]),
  # more on one line
  (['136/83/65, 144/82/86'], [(136, 83, 65), (144, 82, 86)]),
  (['136/83/65,144/82/86'], [(136, 83, 65), (144, 82, 86)]),
  (['136/83/65  , 144/82/86'], [(136, 83, 65), (144, 82, 86)]),
  (['136/83/65 , 144/82/86 , 132/82/70 '], [(136, 83, 65), (144, 82, 86), (132, 82, 70)]),
  # combined
  (['136/83/65, 132/82/70', '144/82/86'], [(136, 83, 65), (132, 82, 70), (144, 82, 86)]),
)

cases_parse_simple_errors = (
  ['asd'], ['136/83/65 132/82/70'], ['136/8365, 132/82/70'], ['136/83/e65'],
  ['136/83/65, w132/82/70'], ['136/83/65, asd, 132/82/70']
)

cases_parse_simple_entries = (  # data, entries, expected
  # empty list
  ([], 1, []), ([], 2, []), ([], 3, []),
  # one line, one token
  (['123/78/67'], 1, [(123, 78, 67)]),
  (['123/78/67'], 2, [(123, 78, 67), None]),
  (['123/78/67'], 3, [(123, 78, 67), None, None]),
  (['123/78/67, 136/83/65, 132,82,70'], 1, [(123, 78, 67)]),
  (['123/78/67, 136/83/65'], 1, [(123, 78, 67)]),
  (['123/78/67, 136/83/65, 132,82,70'], 2, [(123, 78, 67), (136, 83, 65)]),
  (['123/78/67, 136/83/65'], 2, [(123, 78, 67), (136, 83, 65)]),
  (['123/78/67, 136/83/65'], 3, [(123, 78, 67), (136, 83, 65), None]),
  (['123/78/67, 136/83/65'], 4, [(123, 78, 67), (136, 83, 65), None, None]),
  # multiple line, multiple tokens
  (['123/78/67', '123/78/67'], 1, [(123, 78, 67), (123, 78, 67)]),
  (['123/78/67', '123/78/67'], 2, [(123, 78, 67), None, (123, 78, 67), None]),
  (['123/78/67', '123/78/67, 123/78/67'], 1, [(123, 78, 67), (123, 78, 67)]),
  (['123/78/67', '123/78/67, 123/78/67'], 2, [(123, 78, 67), None, (123, 78, 67), (123, 78, 67)]),
  (['123/78/67', '123/78/67, 123/78/67'], 3, [(123, 78, 67), None, None, (123, 78, 67), (123, 78, 67), None]),
)


def test_measurement():
  # check ``as_tuple`` & ``as_dict``:
  for args, kwargs, exp_dict in cases_measurement:
    exp_tup = args
    m = Measurement(*args, **kwargs)
    assert_equal(m.as_tuple(), exp_tup)
    assert_equal(m.as_dict(), exp_dict)


def test_stats():
  # check if calculated correct:
  data = [Measurement(*args, **kwargs) for args, kwargs, exp_dict in cases_measurement]
  stats = Stats(data)
  for attr, exp in cases_stats.items():
    assert_equal(getattr(stats, attr), exp)


def test_stats_empty():
  # empty data should result in empt stats and not in error:
  stats = Stats([])
  stats.evaluate_data()
  assert_equal(len(stats.sys), 0)
  assert_equal(len(stats.dia), 0)
  assert_equal(len(stats.pulse), 0)


def test_stats_none_values():
  # check that ``None`` values don't interfere with stat calculations
  # but show up in the lists correct:
  # build two lists of Measurement instances
  d1 = [Measurement(*args, **kwargs) for args, kwargs, exp_dict in cases_measurement]
  d2 = [Measurement(*args, **kwargs) for args, kwargs, exp_dict in cases_measurement]
  assert_equal(len(d1), len(cases_measurement))
  assert_equal(len(d2), len(cases_measurement))
  # add some ``None`` values to 2nd
  d2.insert(1, None)
  assert_equal(d2[1], None)
  assert_equal(len(d2), len(d1) + 1)
  d2.insert(3, None)
  assert_equal(d2[3], None)
  assert_equal(len(d2), len(d1) + 2)
  # get stats from both list
  d1 = Stats(d1).__dict__
  d2 = Stats(d2).__dict__
  # base list may not be equal due to ``None`` values
  for attr in ('sys', 'dia', 'pulse'):
    assert_equal(len(d2[attr]), len(d1[attr]) + 2)
  # those need to be the same, ``None`` values are filtered out
  for attr in (
    'sys_min', 'sys_max', 'sys_avg',
    'dia_min', 'dia_max', 'dia_avg',
    'pulse_min', 'pulse_max', 'pulse_avg'
  ):
    assert_equal(d1[attr], d2[attr])


def test_parse_simple():
  # check that parsing returns the expected values:
  for case, exp in cases_parse_simple:
    res = parse_simple(case)
    assert_equal([m.as_tuple() for m in res], exp)


def test_parse_simple_errors():
  # check that errors are raised correctly:
  for case in cases_parse_simple_errors:
    with assert_raises(BpdiagError):
      parse_simple(case)
  for case in cases_parse_simple_errors:
    parse_simple(case, check=None)


def test_parse_simple_parseopts():
  # check if pasing options (``seperator`` & ``delimeter``) are working:
  for sep in ('-', '--', ':', ' - '):
    for case, exp in cases_parse_simple:
      new_case = [line.replace('/', sep) for line in case]
      res = [m.as_tuple() for m in parse_simple(new_case, seperator=sep)]
      assert_equal(res, exp)
  for deli in ('-', '--', ':', ' - '):
    for case, exp in cases_parse_simple:
      new_case = [line.replace(',', deli) for line in case]
      res = [m.as_tuple() for m in parse_simple(new_case, delimeter=deli)]
      assert_equal(res, exp)
  # check *skip*
  lines = ('123/78/67, - , 123/78/67', '-, 123/78/67, -')
  exp = [(123, 78, 67), (123, 78, 67), (123, 78, 67)]
  res = [m.as_tuple() for m in parse_simple(lines, skip='-')]
  assert_equal(res, exp)


def test_parse_simple_entries():
  # check that parsing with ``entries`` set gets the expected results:
  for data, entries, exp in cases_parse_simple_entries:
    res = parse_simple(data, entries=entries)
    assert_equal(len(res) % entries, 0)
    res = [(m.as_tuple() if m is not None else None) for m in res]
    assert_equal(res, exp)
  # check *skip*
  lines = ('123/78/67, - , 132/87/67', '-, 123/78/67, -')
  exp = [(123, 78, 67), None, None, (123, 78, 67)]
  res = [m.as_tuple() if m else None for m in parse_simple(lines, skip='-', entries=2)]
  assert_equal(res, exp)


def test_parse_simple_entries_errors():
  # check that errors on ``entries`` are reported / ignored correctly:
  for data, entries, exp in cases_parse_simple_entries:
    if None in exp:
      with assert_raises(BpdiagError):
        parse_simple(data, entries=entries, check=True)
