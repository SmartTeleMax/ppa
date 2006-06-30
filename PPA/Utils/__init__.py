# $Id$

'''General utils'''


class CachedAttribute(object):

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        try:
            result = self.method(inst)
            setattr(inst, self.name, result)
        except:
            # XXX It's a bug in Python 2.2: any exception is replaced with
            # AttributeError
            logger.exception('Error in CachedAttribute:')
            raise
        return result


class CachedClassAttribute(object):

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        try:
            result = self.method(cls)
            setattr(cls, self.name, result)
        except:
            # XXX It's a bug in Python 2.2: any exception is replaced with
            # AttributeError
            logger.exception('Error in CachedClassAttribute:')
            raise
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
