BP Diag - ToDo List
===================

General
-------

* Add date & time handling

* Parse only x lines


Parsing
-------

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

* daily min / max / avg

* min / max tuples (sys/dia/pulse)

* values that are too high (> 130/85 70)

  * and way to high (> 140/90 100)


Output
------

* plaint text output


Charts
------

* specify wich lines to draw: sys, dia, pulse

* show some lines bold (130/135, 80/85)

* spread chart (min/max area)
