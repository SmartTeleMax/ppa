# $Id: Controller.py,v 1.1.1.1 2004/04/09 13:18:10 ods Exp $

import sys
from Caches import NotCached, DummyCache


TEMPLATE_RECURSION_LIMIT = 10


# XXX Problem with this class and related code: it breaks incapsulation. On the
# other hand serialization always breaks incapsulation.
class TemplateWrapper:

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
        #
        # XXX Comments below are a bit outdated
        # This method can be overwritten to change vars and add callback
        # methods that need to know about fp etc.  E.g. access to another
        # template:
        #     # using nested scopes
        #     def template(vars=vars.copy()):
        #         other_template = self._controller.getTemplate()
        #         other_template.interpret(fp, vars)
        interpret_dep_reg = self._create_interpret_dep_reg(_recursion_limit-1)
        try:
            self._engine.interpret(self._program, fp, globals, locals,
                                   interpret_dep_reg.getTemplate)
        except TemplateRecursionLimitExceeded, exc:
            raise TemplateRecursionLimitExceeded(
                    [(template_name, template_type)]+exc.stack)
        return interpret_dep_reg.getDependencies()


class TemplateDependencyRegistrar:
    '''Register dependecies'''

    def __init__(self, get_template, _recursion_limit):
        self._get_template = get_template
        self._recursion_limit = _recursion_limit
        self._dependencies = {}

    def getTemplate(self, template_name, template_type=None):
        template = self._get_template(template_name, template_type,
                                      self._recursion_limit)
        self._dependencies[template_name, template.type] = 1
        # XXX self._dependencies.extend(...)
        return template

    def getDependencies(self):
        return self._dependencies.keys()


class TemplateRecursionLimitExceeded(Exception):

    def __init__(self, stack):
        self.stack = stack  # Stack of (template_name, template_type) pairs

    def __str__(self):
        return ' -> '.join(map(repr, self.stack))


# XXX The only public method of TemplateController is getTemplate?
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
