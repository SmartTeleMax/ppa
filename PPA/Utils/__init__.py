'''General utils'''

__all__ = []


class CachedAttribute(object):

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


class CachedClassAttribute(object):

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        result = self.method(cls)
        setattr(cls, self.name, result)
        return result


class ReadAliasAttribute(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, inst, cls):
        if inst is None:
            return self
        return getattr(inst, self.name)


class AliasAttribute(ReadAliasAttribute):

    def __set__(self, inst, value):
        setattr(inst, self.name, value)

    def __delete__(self, inst):
        delattr(inst, self.name)


class DictRecord(dict):
    '''Handy class providing two ways to get/set items.'''
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        for arg in args+(kwargs,):
            self.update(arg)
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value


from PPA.Template.Engines.PySI import EvalDict

def interpolateString(template, namespace):
    return template % EvalDict(namespace, namespace)
