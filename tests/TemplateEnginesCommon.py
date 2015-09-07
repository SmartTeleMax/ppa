import unittest, sys
from cStringIO import StringIO


def _get_template(self, template_name, template_type=None):
    raise RuntimeError('Subsequent templates are not supported')


class InterpretTestCase(unittest.TestCase):

    def __init__(self, engine, template_string, globals, locals, result):
        unittest.TestCase.__init__(self)
        self._engine = engine
        self._template_string = template_string
        self._globals = globals
        self._locals = locals
        self._result = result

    def runTest(self):
        engine = self._engine
        # Source in string
        program = engine.compileString(self._template_string,
                                       '<string>', _get_template)
        out_fp = StringIO()
        engine.interpret(program, out_fp, self._globals, self._locals,
                         _get_template)
        self.assertEqual(out_fp.getvalue(), self._result)
        saved = engine.dump(program)
        self.assertEqual(type(saved), str)
        restored = engine.load(saved)
        self.assertEqual(restored, program)
        # Source in file
        in_fp = StringIO(self._template_string)
        program = engine.compileFile(in_fp, '<string>', _get_template)
        out_fp = StringIO()
        engine.interpret(program, out_fp, self._globals, self._locals,
                         _get_template)
        self.assertEqual(out_fp.getvalue(), self._result)
        saved = engine.dump(program)
        self.assertEqual(type(saved), str)
        restored = engine.load(saved)
        self.assertEqual(restored, program)


class InterpretTestSuite(unittest.TestSuite):

    def __init__(self, engine_class, list_of_tests):
        unittest.TestSuite.__init__(self)
        engine = engine_class()
        for template_string, globals, locals, result in list_of_tests:
            test = InterpretTestCase(engine, template_string, globals,
                                     locals, result)
            self.addTest(test)
