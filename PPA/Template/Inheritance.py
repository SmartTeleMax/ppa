# $Id: Inheritance.py,v 1.1 2007/04/03 13:41:32 ods Exp $

"""PPA.Template.Inheritance - uses class names in MRO to find suitable template
"""

from SourceFinders import TemplateNotFoundError
import inspect


class InheritanceTemplateSelector(object):
    
    def __init__(self, get_template):
        self._get_template = get_template
        self._cache = {}

    def composeName(self, name):
        '''composeName(name, *args) -> template_name
        
        args to __call__ methods are passed here unchanged.'''
        return name

    def __call__(self, inst, name=None, args=()):
        '''Find appropriate template for the instance.

        name (if not None) is prepended to the list of class names in MRO.
        args is passed to composeName.'''
        get_template = self._get_template
        cache = self._cache
        first_exc = None
        if name is not None:
            if cache.has_key((name, args)):
                return cache[name, args]
            try:
                template = get_template(self.composeName(name, *args))
            except TemplateNotFoundError, exc:
                first_exc = exc
            else:
                cache[name, args] = template
                return template
        to_cache = []
        for cls in inspect.getmro(inst.__class__):
            name = cls.__name__
            if cache.has_key((name, args)):
                template = cache[name, args]
                break
            to_cache.append((name, args))
            try:
                template = get_template(self.composeName(cls.__name__, *args))
            except TemplateNotFoundError, exc:
                if first_exc is None:
                    first_exc = exc
            else:
                break
        else:
            raise first_exc
        for name, args in to_cache:
            cache[name, args] = template
        return template
