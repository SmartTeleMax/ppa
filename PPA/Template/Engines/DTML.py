from DocumentTemplate import HTML, HTMLFile


class Engine:

    type = 'dtml'

    def compileString(self, source, template_name, get_template):
        program = HTML(source)
        program.cook()
        return program

    def compileFile(self, fp, template_name, get_template):
        return self.compileString(fp.read(), template_name, get_template)

    def interpret(self, program, fp, globals, locals, get_template):
        if locals.has_key('__object__'):
            object = locals['__object__']
        elif globals.has_key('__object__'):
            object = globals['__object__']
        else:
            object = None
        result = program(object, globals, **locals)
        fp.write(result)

    def dump(self, program):
        from cPickle import dumps
        return dumps(program)

    def load(self, s):
        from cPickle import loads
        return loads(s)
