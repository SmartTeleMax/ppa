# $Id: _TALCommon.py,v 1.2 2003/11/25 12:08:52 ods Exp $

from TAL.TALDefs import TALESError
from TAL.TALGenerator import TALGenerator
from TAL.TALInterpreter import TALInterpreter


class CompileError(Exception): pass


class Compiler:

    def compile(self, expr):
        return compile(expr, '', 'eval')

    def getCompilerError(self):
        return CompileError


class Default:
    def __nonzero__(self):
        return 0
default = Default()


class Iterator:

    def __init__(self, interpreter, sequence, name):
        self.interpreter = interpreter
        self.iterator = iter(sequence)
        self.name = name

    def next(self):
        try:
            value = self.iterator.next()
        except StopIteration:
            return 0
        else:
            self.interpreter.setLocal(self.name, value)
            return 1


class Interpreter:

    def __init__(self, globals, locals, macros, get_template):
        # Don't set default if it's already set for other purposes
        globals.setdefault('default', default)
        self.globals = globals
        self.locals = locals
        self.macros = macros
        self.stack = [self.locals]
        self.get_template = get_template
    
    def getTALESError(self):
        return TALESError

    def getDefault(self):
        return default

    def beginScope(self):
        self.stack.append(self.locals)

    def endScope(self):
        self.locals = self.stack.pop()

    def setLocal(self, name, value):
        if self.locals is self.stack[-1]:
            # Make a copy on first use
            self.locals = self.locals.copy()
        self.locals[name] = value

    def setGlobal(self, name, value):
        self.globals[name] = value

    def setRepeat(self, name, expr):
        sequence = self.evaluateSequence(expr)
        return Iterator(self, sequence, name)

    def setPosition(self, position):
        self.position = position

    def getCompilerError(self):
        return CompileError

    def evaluate(self, expr):
        return eval(expr, self.globals, self.locals)
    
    evaluateValue = evaluateSequence = evaluate

    def evaluateBoolean(self, expr):
        # Called for tal:condition. If we wish to test for absent attributes or
        # names we should catch exceptions.
        try:
            return not not self.evaluate(expr)
        except (NameError, AttributeError):
            return 0
    
    def evaluateText(self, expr):
        expr = self.evaluate(expr)
        if expr in (default, None):
            return expr
        else:
            return str(expr)
    evaluateStructure = evaluateText
    
    def evaluateMacro(self, expr):
        expr = self.evaluate(expr)
        if isinstance(expr, str):
            return self.macros[expr]
        elif isinstance(expr, tuple) and len(expr)==2:
            program, macros = self.get_template(expr[0]).getProgram()
            return macros[expr[1]]
        else:
            raise TALESError('Invalid expression for macro: %r' % expr)


class Engine:

    type = None
    _xml = 1
    _parser_class = None
    
    def compileString(self, source, template_name, get_template):
        cengine = Compiler()
        generator = TALGenerator(cengine, self._xml)
        parser = self._parser_class(generator)
        parser.parseString(source)
        return parser.getCode()
    
    def compileFile(self, fp, template_name, get_template):
        return self.compileString(fp.read(), template_name, get_template)

    def interpret(self, program, fp, globals, locals, get_template):
        tal_program, macros = program
        iengine = Interpreter(globals, locals, macros, get_template)
        interpreter = TALInterpreter(tal_program, macros, iengine, fp, wrap=0,
                                     tal=1, showtal=0, strictinsert=0)
        interpreter()

    def dump(self, program):
        from marshal import dumps
        return dumps(program)

    def load(self, s):
        from marshal import loads
        return loads(s)
