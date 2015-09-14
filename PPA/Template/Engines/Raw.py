# $Id: Raw.py,v 1.1.1.1 2004/04/09 13:18:11 ods Exp $

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
