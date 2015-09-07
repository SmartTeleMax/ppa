#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, sys, os, codecs
from glob import glob
from cStringIO import StringIO

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(dir))

from PPA.Template.Controller import TemplateController
from PPA.Template.SourceFinders import FileSourceFinder, TemplateDirectory


class TemplateTestCase(unittest.TestCase):

    def __init__(self, template_name, template_type, charset, globals, locals,
                 templates_path, results_path):
        unittest.TestCase.__init__(self)
        self.template_name = template_name
        self.template_type = template_type
        writer = StringIO
        if charset is not None:
            templates_path = TemplateDirectory(templates_path, charset)
            writer = lambda: codecs.getwriter(charset)(StringIO())
        self.writer = writer
        self.globals = globals
        self.locals = locals
        self.templates_path = templates_path
        self.results_path = results_path

    def runTest(self):
        source_finder = FileSourceFinder([self.templates_path])
        controller = TemplateController(source_finder=source_finder)
        template = controller.getTemplate(self.template_name,
                                          self.template_type)
        fp = self.writer()
        template.interpret(fp, self.globals, self.locals)
        got_result = fp.getvalue()
        # We use real (possibly auto-determined) type of template when looking
        # for result.
        result_file_name = os.path.join(self.results_path,
                                '.'.join((self.template_name, template.type)))
        result_fp = file(result_file_name)
        result = result_fp.read()
        result_fp.close()
        self.assertEqual(got_result, result)


class TemplateTestSuite(unittest.TestSuite):

    def __init__(self, templates_path, results_path, list_of_tests):
        unittest.TestSuite.__init__(self)
        for template_name, template_type, charset, globals, locals \
                in list_of_tests:
            test = TemplateTestCase(template_name, template_type, charset,
                                    globals, locals,
                                    templates_path, results_path)
            self.addTest(test)


_list_of_tests = [
    ('test',   'pyem',  None,    {'var': 'global'},
                                 {'var': 'local'}),
    ('test',   None,    None,    {'var': 'global'},
                                 {'var': 'local'}),
    ('test2',  'htal',  None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test2',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test3',  'xtal',  None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test3',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test4',  'htal',  None,    {},
                                 {'title': 'Just a title',
                                  'body': 'Just a body'}),
    ('test4',  None,    None,    {},
                                 {'title': 'Just a title',
                                  'body': 'Just a body'}),
    ('test5',  'dtml',  None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'items': ['foo', 'bar'],
                                  'var': 'local'}),
    ('test5',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'items': ['foo', 'bar'],
                                  'var': 'local'}),
    ('test6',  'raw',   None,    {}, {}),
    ('test6',  None,    None,    {}, {}),
    ('test7',  'pysi',  None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'body': ['para1', 'para2', 'para3'],
                                  'max_paras': 2, 'var': 'local'}),
    ('test7',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'body': ['para1', 'para2', 'para3'],
                                  'max_paras': 2, 'var': 'local'}),
    ('test8',  None,    None,    {},
                                 {'sections': [
                                     {'title': 'Title1',
                                      'children': []},
                                     {'title': 'Title2',
                                      'children': [{'title': 'Title2.1',
                                                    'children': []},
                                                   {'title': 'Title2.2',
                                                    'children': []}]}
                                 ]}),
    ('test9',  'xhtal', None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test9',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    ('test9',  None,    None,    {'var': 'global'},
                                 {'title': 'Just a title',
                                  'var': 'local'}),
    # Tests with charset='utf-8'
    ('test10', 'raw',   'utf-8', {}, {}),
    ('test11', 'pysi',  'utf-8', {'cyrillic': 'кириллица'.decode('utf-8')},
                                 {}),
    ('test12', 'pyem',  'utf-8', {'cyrillic': 'кириллица'.decode('utf-8')},
                                 {}),
    ('test13', 'htal',  'utf-8', {'cyrillic': 'кириллица'.decode('utf-8')},
                                 {}),
    ('test14', 'xtal',  'utf-8', {'cyrillic': 'кириллица'.decode('utf-8')},
                                 {}),
    ('test15', 'xhtal', 'utf-8', {'cyrillic': 'кириллица'.decode('utf-8')},
                                 {}),
    # Test for changes in co_consts of compiled object
    ('test16', 'pyem',  'utf-8', {}, {}),
    # Test for keyword arguments in unicode mode
    ('test17', 'pyem',  'utf-8', {}, {}),
]


def testSuite():
    templates_path = os.path.join(dir, 'templates')
    results_path = os.path.join(dir, 'results')
    suite = TemplateTestSuite(templates_path, results_path, _list_of_tests)
    return suite


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
