#!/usr/bin/env python
# $Id: $

from distutils.core import setup
import PPA

setup(name='PPA',
      version=PPA.__version__,
      description='Python Publishing Accessories (PPA) is a library of '\
                  'python modules useful to build web publication systems',
      url='http://ppa.sf.net/',
      author='Denis S. Otkidach',
      author_email='ods@users.sf.net',
      license='Python-like',
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: '\
                'CGI Tools/Libraries',
      ],
      download_url='http://prdownloads.sourceforge.net/ppa/'\
                   'PPA-%s.tar.gz?download' % PPA.__version__,
      packages=['PPA', 'PPA.HTTP', 'PPA.Template', 'PPA.Template.Engines'])
      
