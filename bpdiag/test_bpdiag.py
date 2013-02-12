# -*- coding: UTF-8 -*-

import json

from nose.tools import assert_equal, assert_raises

from bpdiag import (
  BpdiagError,
  Measurement, Statistic,
  parse_plaintext, parse_json
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

cases_parse_plaintext = (
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

cases_parse_plaintext_errors = (
  ['asd'], ['136/83/65 132/82/70'], ['136/8365, 132/82/70'], ['136/83/e65'],
  ['136/83/65, w132/82/70'], ['136/83/65, asd, 132/82/70']
)

cases_parse_plaintext_entries = (  # data, entries, expected
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
  stats = Statistic(data)
  for attr, exp in cases_stats.items():
    assert_equal(getattr(stats, attr), exp)


def test_stats_empty():
  # empty data should result in empty stats and not in error:
  stats = Statistic([])
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
  d1 = Statistic(d1).__dict__
  d2 = Statistic(d2).__dict__
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


def test_parse_plaintext():
  # check that parsing returns the expected values:
  for case, exp in cases_parse_plaintext:
    res = parse_plaintext(case)
    assert_equal([m.as_tuple() for m in res], exp)


def test_parse_plaintext_errors():
  # check that errors are raised correctly:
  for case in cases_parse_plaintext_errors:
    with assert_raises(BpdiagError):
      parse_plaintext(case)
  for case in cases_parse_plaintext_errors:
    parse_plaintext(case, check=None)


def test_parse_plaintext_parseopts():
  # check if parsing options (``separator`` & ``delimiter``) are working:
  for sep in ('-', '--', ':', ' - '):
    for case, exp in cases_parse_plaintext:
      new_case = [line.replace('/', sep) for line in case]
      res = [m.as_tuple() for m in parse_plaintext(new_case, separator=sep)]
      assert_equal(res, exp)
  for deli in ('-', '--', ':', ' - '):
    for case, exp in cases_parse_plaintext:
      new_case = [line.replace(',', deli) for line in case]
      res = [m.as_tuple() for m in parse_plaintext(new_case, delimiter=deli)]
      assert_equal(res, exp)
  # check *skip*
  lines = ('123/78/67, - , 123/78/67', '-, 123/78/67, -')
  exp = [(123, 78, 67), (123, 78, 67), (123, 78, 67)]
  res = [m.as_tuple() for m in parse_plaintext(lines, skip='-')]
  assert_equal(res, exp)


def test_parse_plaintext_entries():
  # check that parsing with ``entries`` set gets the expected results:
  for data, entries, exp in cases_parse_plaintext_entries:
    res = parse_plaintext(data, entries=entries)
    assert_equal(len(res) % entries, 0)
    res = [(m.as_tuple() if m is not None else None) for m in res]
    assert_equal(res, exp)
  # check *skip*
  lines = ('123/78/67, - , 132/87/67', '-, 123/78/67, -')
  exp = [(123, 78, 67), None, None, (123, 78, 67)]
  res = [m.as_tuple() if m else None for m in parse_plaintext(lines, skip='-', entries=2)]
  assert_equal(res, exp)


def test_parse_plaintext_entries_errors():
  # check that errors on ``entries`` are reported / ignored correctly:
  for data, entries, exp in cases_parse_plaintext_entries:
    if None in exp:
      with assert_raises(BpdiagError):
        parse_plaintext(data, entries=entries, check=True)


def test_parse_json():
  # check empty list
  with assert_raises(BpdiagError):
    parse_json((), check=False)
  with assert_raises(BpdiagError):
    parse_json((), check=True)
  res = parse_json((), check=None)
  assert_equal(res, [])
  # test data
  json_line = '[[136,83,65],[132,82,70],[144,82,86],[137,81,75],[143,80,68],'\
    '[131,82,60],[144,82,64],[136,79,67],[140,80,62],[136,83,68],[138,80,99],'\
    '[133,74,65],[136,79,67],[131,76,64],[135,81,72],[136,75,61],[127,79,72]]'
  json_lines = (
    '[[136,83,65],[132,82,70],[144,82,86],[137,81,75],[143,80,68],',
    '[131,82,60],[144,82,64],[136,', '79,67],[140,80,62],[136,83,68],',
    '[138,80,99],', '[133,74,65],[136,79,67],[131,76,64],[135,81,72],',
    '[136,75,61],[127,79,72]]'
  )
  exp = [tuple(l) for l in json.loads(json_line)]
  # check JSON tuples
  res = parse_json(json_line)
  assert_equal([m.as_tuple() for m in res], exp)
  res = parse_json(json_lines)
  assert_equal([m.as_tuple() for m in res], exp)
  # check JSON dics
  bp_dict = [Measurement(*m).as_dict() for m in exp]
  json_obj_str = json.dumps(bp_dict)
  res = parse_json(json_obj_str, as_obj=True)
  assert_equal([m.as_dict() for m in res], bp_dict)
  assert_equal([m.as_tuple() for m in res], exp)
