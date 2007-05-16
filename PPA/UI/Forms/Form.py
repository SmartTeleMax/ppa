# $Id$

__all__ = ['UIForm']

from Fields import Schema
from PPA.Template.SourceFinders import TemplateNotFoundError
import inspect
from PPA.Utils import CachedClassAttribute


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
    '''Name-value context'''

    def __init__(self, value=None, name=None, prefix='', parent=None):
        self.name = name
        if value is None:
            value = {}
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

    def entry(self, name, value=None):
        if value is None:
            value = self.value
            parent = self.parent
        else:
            parent = self
        return self.__class__(value, name=name, prefix=self.prefix,
                              parent=parent)

    def branch(self, value=None):
        if value is None:
            value = {}
        prefix = '%s%s.' % (self.prefix, self.name)
        return self.__class__(value, name=None, prefix=prefix, parent=self)

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


class UIForm:

    # public parameters:
    #   schema          - form schema (either Schema object or list of fields)
    #   value           - converted (python) values
    #   filter          - access control filter
    #   params          - any object to pass to fields (application dependent)
    # for internal use:
    #   errors          - occured errors
    #   form_content    - None # original form params
    # attributes:
    #   requisites      - requisites object to store data needed to render
    #                     view (e.g. some JavaScript initialization to put
    #                     in <head>)
    
    def __init__(self, schema, value=None, params=None,
                 errors=None, form_content=None):
        if not isinstance(schema, Schema):
            schema = Schema(subfields=schema)
        self.schema = schema
        self.params = params
        self.errors = errors or {}
        self.form_content = form_content or {}
        if value is None:
            value = schema.getDefault(self, NVContext())
        self.value = value
        self.requisites = None

    def render(self, template_controller, global_namespace={}):
        """Renders form using template_controller to find fields templates,
        returns dict(content=unicode, requisites=list), where content is
        form rendered to html and requisites is SOMETHING"""
        context = NVContext(self.value)
        if not self.form_content:
            self.form_content = self.schema.toForm(self, context)
        self.requisites = self.createRequisites()
        template_selector = FieldTemplateSelector(
                                    template_controller.getTemplate)
        content = self.schema.render(self, context,
                                     template_selector, global_namespace)
        return content

    def accept(self, form):
        """Accepts form fields from from (PPA.HTTP.Form) with self.schema,
        initialized something of self.errors, self.form_content, self.content
        """
        context = NVContext(self.value)
        # XXX Do we need to return form_content and errors or just fill them
        # in-place?
        self.value, self.errors = self.schema.accept(self, context, form)

    def hasErrors(self):
        return bool(self.errors)

    def event(self): # XXX what else?
        raise NotImplementedError()

    def createRequisites(self):
        return {}


# vim: set sts=4 sw=4 ai et:
