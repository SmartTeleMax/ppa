from PPA.Template.SourceFinders import TemplateNotFoundError
import logging, inspect
from PPA.Utils import CachedClassAttribute

logger = logging.getLogger(__name__)


class Writer:
    """Fast, but incompatible StringIO.StringIO implementation. Only supports
    write and getvalue methods"""
    
    def __init__(self):
        self.parts = []
        self.write = self.parts.append
    
    def getvalue(self):
        return ''.join(self.parts)


class FieldTemplateSelector:

    def __init__(self, get_template):
        self._get_template = get_template
        self._cache = {}

    def getTemplateName(self, type_name, render_class):
        return '%s.%s.html' % (type_name, render_class)

    def __call__(self, field_type, render_class):
        cache = self._cache
        first_exc = None
        type_name = field_type.typeName
        if type_name is not None:
            if cache.has_key((type_name, render_class)):
                return cache[type_name, render_class]
            try:
                cache[type_name, render_class] = template = \
                    self._get_template(self.getTemplateName(type_name,
                                                            render_class))
            except TemplateNotFoundError, exc:
                first_exc = exc
            else:
                return template
        to_cache = []
        for cls in inspect.getmro(field_type.__class__):
            type_name = cls.__name__
            if cache.has_key((type_name, render_class)):
                template = cache[type_name, render_class]
                break
            to_cache.append((type_name, render_class))
            try:
                template = self._get_template(
                                self.getTemplateName(type_name, render_class))
            except TemplateNotFoundError, exc:
                if first_exc is None:
                    first_exc = exc
            else:
                break
        else:
            raise first_exc
        for type_name, render_class in to_cache:
            cache[type_name, render_class] = template
        return template


class NVContext(object):
    def __init__(self, value={}, name='', prefix='', parent=None):
        self.name = name
        self.value = value
        self.prefix = prefix
        self.parent = parent

    @property
    def nameInForm(self):
        return self.prefix+self.name

    @property
    def scalar(self):
        '''Easy access to current value assuming it's of scalar type'''
        return self.value[self.name]

    def child(self, name, value=None, branch=True):
        if branch:
            prefix = '%s%s.' % (self.prefix, self.name)
        else:
            prefix = self.prefix
        if value is None:
            value = self.value
            parent = self.parent
        else:
            parent = self
        return self.__class__(value, name=name, prefix=prefix, parent=parent)

    def __getitem__(self, path):
        context = self
        names = path.split('/')
        while names and names[0]=='..':
            names.pop(0)
            context = context.parent
        value = context.value
        for name in names:
            value = value[name]
        return value


#class ACFilter:
#    '''Access control filter.
#    
#    show    - either None (dont show) or string with render class
#    accept  - True if field have to be accepted from form
#    '''
#
#    def __init__(self, show='edit', accept=True, event=True):
#        self.show = show
#        self.accept = accept
#        self.event = event
#
#    def __call__(self, field_type, context):
#        # Unchanged by default
#        return self
#
#    def clone(self, **kwargs):
#        return self.__class__(kwargs.get('show', self.show),
#                              kwargs.get('accept', self.accept),
#                              kwargs.get('event', self.event))


# vim: set sts=4 sw=4 ai et:
