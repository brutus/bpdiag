BP Diag - ToDo List
===================

General
-------

* Add ``Measurement`` class

* Add date & time handling


Parsing
-------

* simple parser: add "skip-char"

* Add a JSON parser

* Add a RegEx Parser

  Each line will be parsed by a given regular expression, eg::

    import re
    line = '2013-01-23:12:34:124/75/67:0:1:0:0:1'
    regex = ur'^\d{4}-\d{1,2}-\d{1,2}:\d{1,2}:\d{1,2}:(?P<sys>\d{2,3})/(?P<dia>\d{2,3})/(?P<pulse>\d{2,3})(:[01]){5}$'
    regex = re.compile(regex)
    m = regex.match(line)
    m.groupdict()  # {u'dia': '75', u'pulse': '67', u'sys': '124'}

* Add a CSV parser

  Use `unicodecsv<https://github.com/jdunck/python-unicodecsv>` to parse
  CSV files (options = *delimiter*, *quotechar* & *restkey*)::

    import unicodecsv
    from cStringIO import StringIO
    # setup file
    f = StringIO()
    w = unicodecsv.writer(f, encoding='utf-8')
    w.writerow((u'é', u'ñ'))
    f.seek(0)
    r = unicodecsv.reader(f, encoding='utf-8')
    row = r.next()
    print row[0], row[1]

  Use http://docs.python.org/2/library/csv.html ::

    DictReader(csvfile, fieldnames=None, restkey=None, restval=None, dialect='excel', *args, **kwds)


statistics
----------

* check if stats are ``True`` (have data)

* daily min / max / avg

* values that are too high (> 130/85 70)

  * and way to high (> 140/90 100)


Output
------

* JSON full dict output

* plaint text output


Charts
------

* *width* & *height* for charts

* spread chart (min/max area)
