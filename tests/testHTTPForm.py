#!/usr/bin/env python

import unittest, sys, os

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(dir))

from PPA.HTTP.Adapters.CGI import Adapter
from PPA.HTTP.Form import Form
from cStringIO import StringIO


import logging
logging.basicConfig()


class FormTest(unittest.TestCase):

    class CGIApp(Adapter):
        def handle(self, request, response):
            self.form = Form(request)
        def getFormDict(self):
            result = {}
            for name in self.form.keys():
                result[name] = self.form.getStringList(name)
            return result

    def runCGI(self, method='GET', query_string=None, content_type=None,
               data=''):
        environ = {
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': '/',
        }
        orig_environ = os.environ.copy()
        orig_stdin = sys.stdin
        orig_stdout = sys.stdout
        sys.stdout = StringIO()
        if data:
            sys.stdin = StringIO(data)
            environ['CONTENT_LENGTH'] = len(data)
        if query_string:
            environ['QUERY_STRING'] = query_string
        os.environ.update(environ)
        app = self.CGIApp()
        app()
        sys.stdout = orig_stdout
        sys.stdin = orig_stdin
        for key in environ.keys():
            del os.environ[key]
        os.environ.update(orig_environ)
        return app.getFormDict()

    def testGET(self):
        self.assertEqual(self.runCGI(query_string='a=1&b=2'),
                         {'a': ['1'], 'b': ['2']})


def testSuite():

    return unittest.makeSuite(FormTest)


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
