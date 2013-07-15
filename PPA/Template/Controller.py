# $Id: Controller.py,v 1.10 2008/06/06 11:51:48 ods Exp $

import sys, os
from Caches import NotCached, MemoryCache


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

    def __init__(self, name, type, engine, program, get_template):
        self.name = name
        self.type = type
        self._engine = engine
        self._program = program
        self._get_template = get_template

    def getProgram(self):
        return self._program

    def interpret(self, fp=sys.stdout, globals=None, locals=None,
                  _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        # _recursion_limit is for internal use only
        try:
            self._engine.interpret(self._program, fp,
                                   globals or {}, locals or {},
                                   self._get_template)
        except TemplateRecursionLimitExceeded, exc:
            raise TemplateRecursionLimitExceeded(
                            [(self.name, self.type)]+exc.stack)

    def toFile(self, fp, globals=None, locals=None):
        '''Renders template into file-like object.'''
        self.interpret(fp, globals, locals)

    def toString(self, globals=None, locals=None):
        '''Renders template and returns result as string.'''
        fp = _Writer()
        self.toFile(fp, globals, locals)
        return fp.getvalue()


class TemplateRecursionLimitExceeded(Exception):

    def __init__(self, stack):
        self.stack = stack  # Stack of (name, type) pairs

    def __str__(self):
        return ' -> '.join(map(repr, self.stack))


class TemplateController:
    '''Control communication between application, template engines, cache,
    template source finder.'''

    def __init__(self, source_finder=None, engine_importer=None,
                 template_cache=None, template_wrapper_class=TemplateWrapper):
        if source_finder is None:
            from SourceFinders import DummySourceFinder
            source_finder = DummySourceFinder()
        self._source_finder = source_finder
        if engine_importer is None:
            from Engines import EngineImporter
            engine_importer = EngineImporter()
        self.getEngine = engine_importer
        if template_cache is None:
            template_cache = MemoryCache()
        self._template_cache = template_cache
        self._engine_cache = {}
        self._template_wrapper_class = template_wrapper_class

    def _compile(self, engine, compile, source, name, type,
                 _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        try:
            program = compile(source, name, self.getTemplate)
        except TemplateRecursionLimitExceeded, exc:
            raise TemplateRecursionLimitExceeded([(name, type)]+exc.stack)
        return self._template_wrapper_class(name, type, engine, program,
                                            self.getTemplate)

    def typeFromName(self, name):
        ext = os.path.splitext(name)[1]
        if not ext:
            raise ValueError("Can't determine template type automatically. "\
                             'You have to state it explicitly.')
        assert ext[0]=='.'
        return ext[1:]

    def compileString(self, source, name='?', type=None,
                      _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        if type is None:
            type = self.typeFromName(name)
        engine = self.getEngine(type)
        return self._compile(engine, engine.compileString, source, name, type,
                             _recursion_limit=_recursion_limit)

    def compileFile(self, source_fp, name=None, type=None,
                    _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        if name is None:
            name = getattr(source_fp, 'name', '?')
        if type is None:
            type = self.typeFromName(name)
        engine = self.getEngine(type)
        return self._compile(engine, engine.compileFile, source_fp, name, type,
                             _recursion_limit=_recursion_limit)

    def getTemplate(self, name, type=None,
                    _recursion_limit=TEMPLATE_RECURSION_LIMIT):
        # _recursion_limit is for internal use only
        '''Dispatch the request to template engine and return compiled
        template object.'''
        if _recursion_limit==0:
            raise TemplateRecursionLimitExceeded([(name, type)])
        try:
            template = self._template_cache.retrieve((name, type))
        except NotCached:
            source_fp, real_type = \
                self._source_finder.find(name, type)
            template = self.compileFile(source_fp, name, real_type,
                                        _recursion_limit=_recursion_limit)
            self._template_cache.store((name, real_type), template)
            if type!=real_type:
                self._template_cache.store((name, type), template)
        return template
