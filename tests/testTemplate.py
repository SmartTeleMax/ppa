#!/usr/bin/env python
# $Id: testTemplate.py,v 1.14 2003/11/25 12:08:53 ods Exp $

import unittest, sys, os
from glob import glob
from cStringIO import StringIO

dir = os.path.dirname(os.path.abspath(globals().get('__file__', sys.argv[0])))
sys.path.insert(0, os.path.dirname(os.path.dirname(dir)))

from PPA.Template.Controller import TemplateController
from PPA.Template.SourceFinders import FileSourceFinder


class TemplateTestCase(unittest.TestCase):

    def __init__(self, template_name, template_type, globals, locals,
                 templates_path, results_path):
        unittest.TestCase.__init__(self)
        self.template_name = template_name
        self.template_type = template_type
        self.globals = globals
        self.locals = locals
        self.templates_path = templates_path
        self.results_path = results_path
    
    def runTest(self):
        source_finder = FileSourceFinder([self.templates_path])
        controller = TemplateController(source_finder=source_finder)
        template = controller.getTemplate(self.template_name,
                                          self.template_type)
        fp = StringIO()
        template.interpret(fp, self.globals, self.locals)
        got_result = fp.getvalue()
        # We use real (possibly auto-determined) type of template when looking
        # for result.
        result_fp = open(os.path.join(self.results_path,
                '.'.join((self.template_name, template.type))))
        result = result_fp.read()
        result_fp.close()
        self.assertEqual(got_result, result)


class TemplateTestSuite(unittest.TestSuite):

    def __init__(self, templates_path, results_path, list_of_tests):
        unittest.TestSuite.__init__(self)
        for template_name, template_type, globals, locals in list_of_tests:
            test = TemplateTestCase(template_name, template_type, globals,
                                    locals, templates_path, results_path)
            self.addTest(test)


_list_of_tests = [
    ('test',  'pyem',  {'var': 'global'},
                       {'var': 'local'}),
    ('test',  None,    {'var': 'global'},
                       {'var': 'local'}),
    ('test2', 'htal',  {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
    ('test2', None,    {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
    ('test3', 'xtal',  {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
    ('test3', None,    {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
    ('test4', 'htal',  {},
                       {'title': 'Just a title', 'body': 'Just a body'}),
    ('test4', None,    {},
                       {'title': 'Just a title', 'body': 'Just a body'}),
    ('test5', 'dtml',  {'var': 'global'},
                       {'title': 'Just a title', 'items': ['foo', 'bar'],
                        'var': 'local'}),
    ('test5', None,    {'var': 'global'},
                       {'title': 'Just a title', 'items': ['foo', 'bar'],
                        'var': 'local'}),
    ('test6', 'raw',   {}, {}),
    ('test6', None,    {}, {}),
    ('test7', 'pysi',  {'var': 'global'}, 
                       {'title': 'Just a title',
                        'body': ['para1', 'para2', 'para3'],
                        'max_paras': 2, 'var': 'local'}),
    ('test7', None,    {'var': 'global'},
                       {'title': 'Just a title',
                        'body': ['para1', 'para2', 'para3'],
                        'max_paras': 2, 'var': 'local'}),
    ('test8', None,    {},
                       {'sections': [
                           {'title': 'Title1', 'children': []},
                               {'title': 'Title2', 'children': [
                               {'title': 'Title2.1', 'children': []},
                               {'title': 'Title2.2', 'children': []}
                       ]}]}),
    ('test9', 'xhtal', {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
    ('test9', None,    {'var': 'global'},
                       {'title': 'Just a title', 'var': 'local'}),
]


def testSuite():
    templates_path = os.path.join(dir, 'templates')
    results_path = os.path.join(dir, 'results')
    suite = TemplateTestSuite(templates_path, results_path, _list_of_tests)
    return suite


if __name__=='__main__':
    unittest.TextTestRunner().run(testSuite())
