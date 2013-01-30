#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup

setup(
  name='bpdiag',
  version=open('CHANGES.txt').readline().split()[0][1:-1],
  author='Brutus',
  author_email='brutus.dmc@googlemail.com',
  description='A Python script to visualize blood pressure data.',
  long_description=open('README.rst').read(),
  url='https://github.com/brutus/bpdiag/',
  download_url='https://github.com/brutus/bpdiag/zipball/master',
  license='LICENSE.txt',
  classifiers=[
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Programming Language :: Python',
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Healthcare Industry',
    'Natural Language :: English',
    'Topic :: Utilities'
  ],
  package_dir={'': 'bpdiag'},
  py_modules=['bpdiag'],
)
