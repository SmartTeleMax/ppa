#!/usr/bin/env python
# $Id: testPythonEmbedded.py,v 1.3 2004/04/12 10:00:16 ods Exp $

import unittest, sys, os

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(dir))

from PPA.Template.Engines.PythonEmbedded import Parser, ParseError, Engine


class PyEmParserTestCase(unittest.TestCase):

    def _parse(self, s):
        return Parser(s).process()

    def testRawHTML(self):
        '''Parsing raw HTML'''
        raw_html = '''\
<html>
<body background="#ffffff">
<h1 align="center">Header</h1>
<p style="color: blue">Some Text</p>
</body>
</html>'''
        self.assertEqual(self._parse(raw_html), [('html', raw_html)])

    def testSimpleSuite(self):
        '''Parsing simple python suite'''
        suite = '''
import operator
def fact(n):
    assert n>=0
    if n<=1:
        return 1
    return reduce(operator.mul, range(1, n+1))
'''
        self.assertEqual(self._parse('<%' + suite + '%>'), [('suite', suite)])

    def testSimpleExpr(self):
        '''Parsing simple Python expression'''
        expr = '(a+b)*c'
        self.assertEqual(self._parse('<%=' + expr + '%>'), [('expr', expr)])

    def testQuotes(self):
        '''Parsing quotes in suites and expressions'''
        for quotes in [
                '"string"',
                "'string'",
                '"""multiline\nstring"""',
                "'''multiline\nstring'''",
                '"\\"escapes\\""',
                "'\\'escapes\\''",
                '"con""cat"\'ena\'\'tion\'',
                '"""multiline\n\\\'with\\\'\\"esqapes\\""""']:
            suite = '\n%s\n' % quotes
            self.assertEqual(self._parse('<%' + suite + '%>'),
                             [('suite', suite)])
            expr = quotes
            self.assertEqual(self._parse('<%=' + expr + '%>'),
                             [('expr', expr)])

    def testImproperExpr(self):
        '''Improperly embedded expressions'''
        for expr in ['\n1', '1\n', '1\n2', '', ' ']:
            self.assertRaises(ParseError, self._parse, '<%=' + expr + '%>')

    def testImproperSuite(self):
        '''Improperly embedded suites'''
        for suite in ['\n1', '1\n', '12', '1\n2']:
            self.assertRaises(ParseError, self._parse, '<%' + suite + '%>')


from TemplateEnginesCommon import InterpretTestSuite

list_of_interpret_tests = [
    ('<html></html>', {}, {}, '<html></html>'),
    ('<%= 1 %>', {}, {}, '1'),
    ('<%= title %>', {'title': 'Just a title'}, {}, 'Just a title'),
    ('<%= title.upper() %>', {'title': 'Just a title'}, {}, 'JUST A TITLE'),
    ('''\
<%
for i in range(n):
    %><%= i+1 %><br><%
%>''', {'n': 5}, {}, '1<br>2<br>3<br>4<br>5<br>'),
    ('<%\nimport string\n%><%= string.__name__ %>', {}, {}, 'string'),
]


def testSuite():
    return unittest.TestSuite([
        unittest.makeSuite(PyEmParserTestCase),
        InterpretTestSuite(Engine, list_of_interpret_tests)
    ])


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
