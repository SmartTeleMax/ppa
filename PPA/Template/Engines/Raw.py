# $Id: Raw.py,v 1.2 2003/11/25 12:08:52 ods Exp $

'''The most simple engine around: returns source unchanged'''


class Engine:

    type = 'raw'

    def compileString(self, source, template_name, get_template):
        return source

    def compileFile(self, fp, template_name, get_template):
        return fp.read()

    def interpret(self, program, fp, globals, locals, get_template):
        fp.write(program)

    def dump(self, program):
        return program

    def load(self, s):
        return s
