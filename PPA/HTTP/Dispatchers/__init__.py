
"""
This module provides three types of objects:

Dispatcher - http-dispatcher
Dispatcher.register(condition, action) registers action to be executed if condition metches request
Dispatcher.dispatch(request, response) is wrapped by PPA adapter user want

Condition - http request condition
Condition.__call__(request) - returns boolean, if True is returned - condition matches request

Action - action to be executed on matched request
action(condition, request, response)

The only implemented Condition is Prefix(prefix)
The only implemented Action is Run('dotted.path.to.object', method='method_to_run')

TODO:

Run should accept 'dotted.path.to.objct.and.its.method'
Redirect should be implemented as proof of concept

EXAMPLE USAGE:

dispatcher = Dispatcher([
    (Prefix('/forums'), Run('forum.app')),
    (Prefix('/wiki'), Run('wiki.app', method='run')),
    ])

Location /forums is dispatched to callable object 'app' in module 'forum'.
Location /wiki is dispatched to method 'run' of object 'app' in module 'wiki'
"""

from PPA.HTTP import Errors


def importObject(name, default_module=None, globals=None):
    '''Import object with name in form package.module.obj_name'''
    if '.' in name:
        parts = name.split('.')
        obj_name = parts[-1]
        obj = __import__('.'.join(parts[:-1]), globals)
        for part in parts[1:]:
            obj = getattr(obj, part)
        return obj
    else:
        return getattr(default_module, name)


class Action:
    class Control(Exception):
        pass

    class PassThrough(Control):
        pass


    class Restart(Control):
        pass


    def __call__(self, condition, request, response):
        raise NotImplementedError()


class Run(Action):
    def __init__(self, objectpath, method=None):
        self._path = objectpath
        self._method = method

    def __call__(self, condition, request, response):
        obj = importObject(self._path)
        if self._method:
            callable = getattr(obj, self._method)
        else:
            callable = obj
        callable(request, response)


class Redirect(Action):
    def __init__(self, location):
        self._location = location

    def __call__(self, condition, request, response):
        # XXX modifies pathInfo
        pass


class Condition:
    def __call__(self, request):
        raise NotImplementedError()


class Prefix(Condition):
    def __init__(self, prefix):
        self._prefix = prefix

    def __call__(self, request):
        prefix_len = len(self._prefix)
        prefix = request.pathInfo[:prefix_len]

        if prefix == self._prefix:
            path = request.pathInfo[prefix_len:]
            if path == '' or path.startswith('/'):
                request.pathInfo = path
                return True


class Dispatcher:
    max_restarts = 5 # maximum levels of restarts for request processing

    def __init__(self, registry=None):
        self.registry = registry or []

    def register(self, condition, action):
        self.registry.append((condition, action))

    def __call__(self, request, response, level=0):
        if level > self.max_restarts:
            raise RuntimeError('Max level of pass thgroup actions reached')

        for condition, action in self.registry:
            if condition(request):
                try:
                    return action(condition, request, response)
                except action.PassThrough:
                    continue
                except action.Restart:
                    return self.dispatch(request, response, level+1)

        self.defaultAction(request, response)

    def defaultAction(self, request, response):
        raise Errors.NotFound()
