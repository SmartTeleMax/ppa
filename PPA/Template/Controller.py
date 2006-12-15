# $Id: Controller.py,v 1.3 2006/12/14 15:01:53 ods Exp $

import sys
from Caches import NotCached, DummyCache


TEMPLATE_RECURSION_LIMIT = 10


class _Writer:
    """Fast, but incompatible StringIO.StringIO implementation. Only supports
    write and getvalue methods"""
    # XXX This class is fast, but trade-off is dificulty in discovering of
    # UnicodeError source: in case of mixed str/unicode chunks we get an error
    # only when getvalue() is called, while it should be raised in write() to
    # get proper traceback.
    
    def __init__(self):
	self.parts = []
	self.write = self.parts.append
    
    def getvalue(self):
	return ''.join(self.parts)


class TemplateWrapper:
    '''Wraps template in handy object.'''

    def __init__(self, engine, program, compile_deps,
                 create_interpret_dep_reg):
        self._engine = engine
        self.type = engine.type
        self._program = program
        self._create_interpret_dep_reg = create_interpret_dep_reg

    def getProgram(self):
        return self._program

    def interpret(self, fp=sys.stdout, globals={}, locals={},
                  _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        # _recursion_limit is for internal use only
        interpret_dep_reg = self._create_interpret_dep_reg(_recursion_limit-1)
        try:
            self._engine.interpret(self._program, fp, globals, locals,
                                   interpret_dep_reg.getTemplate)
        except TemplateRecursionLimitExceeded, exc:
            raise TemplateRecursionLimitExceeded(
                    [(template_name, template_type)]+exc.stack)
        return interpret_dep_reg.getDependencies()

    def toFile(self, fp, globals={}, locals={}):
        '''Renders template into file-like object.'''
        self.interpret(fp, globals, locals)

    def toString(self, globals={}, locals={}):
        '''Renders template and returns result as string.'''
        fp = _Writer()
        self.toFile(fp, globals, locals)
        return fp.getvalue()


class TemplateDependencyRegistrar:
    '''Register dependecies'''

    def __init__(self, get_template, _recursion_limit):
        self._get_template = get_template
        self._recursion_limit = _recursion_limit
        self._dependencies = set()

    def getTemplate(self, template_name, template_type=None):
        template = self._get_template(template_name, template_type,
                                      self._recursion_limit)
        self._dependencies.add((template_name, template.type))
        return template

    def getDependencies(self):
        return self._dependencies


class TemplateRecursionLimitExceeded(Exception):

    def __init__(self, stack):
        self.stack = stack  # Stack of (template_name, template_type) pairs

    def __str__(self):
        return ' -> '.join(map(repr, self.stack))


class TemplateController:
    '''Control communication between application, template engines, cache,
    template source finder.'''

    def __init__(self, source_finder=None, engine_importer=None,
                 template_cache=None, template_wrapper_class=TemplateWrapper,
                 compile_dep_reg_class=TemplateDependencyRegistrar,
                 interpret_dep_reg_class=TemplateDependencyRegistrar):
        if source_finder is None:
            from SourceFinders import DummySourceFinder
            source_finder = DummySourceFinder()
        self._source_finder = source_finder
        if engine_importer is None:
            from Engines import EngineImporter
            engine_importer = EngineImporter()
        self.getEngine = engine_importer
        if template_cache is None:
            template_cache = DummyCache()
        self._template_cache = template_cache
        self._engine_cache = {}
        self._template_wrapper_class = template_wrapper_class
        self._compile_dep_reg_class = compile_dep_reg_class
        self._interpret_dep_reg_class = interpret_dep_reg_class

    def _create_interpret_dep_reg(self, _recursion_limit):
        return self._interpret_dep_reg_class(self.getTemplate,
                                             _recursion_limit)

    def _compile(self, engine, compile, source, template_name='?',
                 _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        # creating registrar for compile dependencies
        compile_dep_reg = self._compile_dep_reg_class(self.getTemplate,
                                                _recursion_limit-1)
        try:
            program = compile(source, template_name,
                              compile_dep_reg.getTemplate)
        except TemplateRecursionLimitExceeded, exc:
            raise TemplateRecursionLimitExceeded(
                    [(template_name, template_type)]+exc.stack)
        # now compile_dep_reg already catched all compile dependencies
        compile_deps = compile_dep_reg.getDependencies()

        return self._template_wrapper_class(engine, program, compile_deps,
                                            self._create_interpret_dep_reg)

    def compileString(self, source, template_type, template_name='?',
                      _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        engine = self.getEngine(template_type)
        return self._compile(engine, engine.compileString, source,
                             _recursion_limit=_recursion_limit)

    def compileFile(self, source_fp, template_type, template_name='?',
                    _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        engine = self.getEngine(template_type)
        return self._compile(engine, engine.compileFile, source_fp,
                             _recursion_limit=_recursion_limit)

    def getTemplate(self, template_name, template_type=None,
                    _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        # _recursion_limit is for internal use only
        '''Dispatch the request to template engine and return compiled
        template object.'''
        if _recursion_limit==0:
            raise TemplateRecursionLimitExceeded(
                    [(template_name, template_type)])
        try:
            template = self._template_cache.retrieve(
                        (template_name, template_type))
        except NotCached:
            source_fp, real_template_type = \
                self._source_finder.find(template_name, template_type)
            template = self.compileFile(source_fp, real_template_type,
                                        _recursion_limit=_recursion_limit)
            self._template_cache.store((template_name, real_template_type),
                                       template)
        return template
