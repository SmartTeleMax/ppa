'''Python-style string interpolation'''


class EvalDict:

    def __init__(self, globals, locals, template_name='?'):
        self.template_name = template_name
        self.globals = globals
        self.locals = locals

    def __getitem__(self, key):
        code = compile(key, self.template_name, 'eval')
        return eval(code, self.globals, self.locals)


class Engine:

    type = 'pysi'

    def compileString(self, source, template_name, get_template):
        return template_name, source

    def compileFile(self, fp, template_name, get_template):
        return template_name, fp.read()

    def interpret(self, program, fp, globals, locals, get_template):
        template_name, source = program
        fp.write(source % EvalDict(globals, locals, template_name))

    def dump(self, program):
        template_name, source = program
        return '\0'.join([template_name, source])

    def load(self, s):
        template_name, source = s.split('\0', 1)
        return template_name, source
