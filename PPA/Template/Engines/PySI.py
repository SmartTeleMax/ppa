# $Id: PySI.py,v 1.2 2003/11/25 12:08:52 ods Exp $

'''Python-style string interpolation'''


class EvalDict:

    def __init__(self, globals, locals):
        self.globals = globals
        self.locals = locals

    def __getitem__(self, key):
        key = key % self
        return eval(key, self.globals, self.locals)


class Engine:

    type = 'pysi'

    def compileString(self, source, template_name, get_template):
        return source

    def compileFile(self, fp, template_name, get_template):
        return fp.read()

    def interpret(self, program, fp, globals, locals, get_template):
        fp.write(program % EvalDict(globals, locals))

    def dump(self, program):
        return program

    def load(self, s):
        return s
