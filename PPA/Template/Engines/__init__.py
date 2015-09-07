__all__ = ['enginesByType', 'UnknownTemplateType', 'EngineImporter']


from _registry import enginesByType


class UnknownTemplateType(LookupError): pass


class EngineImporter:

    def __init__(self, engines_by_type=enginesByType):
        self._engines_by_type = engines_by_type
        self._cache = {}

    def __call__(self, template_type):
        '''Return module of engine by its type'''
        if not self._cache.has_key(template_type):
            try:
                module_name = self._engines_by_type[template_type]
            except KeyError:
                raise UnknownTemplateType(template_type)
            module = __import__('.'.join((__name__, module_name)))
            for part in __name__.split('.')[1:] + [module_name]:
                module = getattr(module, part)
            self._cache[template_type] = module.Engine()
        return self._cache[template_type]
