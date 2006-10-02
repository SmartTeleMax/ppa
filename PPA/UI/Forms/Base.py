from PPA.Template.SourceFinders import TemplateNotFoundError
import inspect, logging

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
        return '%s.%s' % (type_name, render_class)

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


class Context(object):

    def __init__(self, value, parent=None):
        self.value = value
        self.parent = parent

    def child(self, value):
        return self.__class__(value, parent=self)

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


class FieldName(str):

    def __new__(cls, name='', prefix=''):
        self = str.__new__(cls, name)
        self.prefix = prefix
        return self

    @property
    def inForm(self):
        return self.prefix+self

    def child(self, name='', branch=True):
        if branch:
            prefix = '%s%s.' % (self.prefix, self)
        else:
            prefix = self.prefix
        return self.__class__(name, prefix)


class ACFilter:
    '''Access control filter.
    
    show    - either None (don't show) or string with render class
    accept  - True if field have to be accepted from form
    '''

    def __init__(self, show='edit', accept=True, event=True):
        self.show = show
        self.accept = accept
        self.event = event

    def __call__(self, field_type, field_name, context):
        # Unchanged by default
        return self

    def clone(self, **kwargs):
        return self.__class__(kwargs.get('show', self.show),
                              kwargs.get('accept', self.accept),
                              kwargs.get('event', self.event))


class Field(object):

    typeName = None
    default = ''
    requisitesFillers = []
    eventHandlers = []

    def __init__(self, requisitesFillers=[], eventHandlers=[], **kwargs):
        self.__dict__.update(kwargs)
        self.requisitesFillers = self.requisitesFillers + requisitesFillers
        self.eventHandlers = self.eventHandlers + eventHandlers

    def fromCode(self, value, params):
        return value
    
    def getDefault(self, field_name, context, params):
        return {field_name: self.fromCode(self.default, params)}

    def toForm(self, field_name, context, filter):
        '''Converts fields to strings and puts into form_content.'''
        assert filter.show is not None
        return {field_name.inForm: context.value[field_name]}

    def fillRequisites(self, field_name, form_content, errors, requisites,
                       context, filter, params):
        for filler in self.requisitesFillers:
            filler(self, field_name, form_content, errors, requisites,
                   context, filter, params)

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        return {'fieldName': field_name.inForm, 'fieldType': self, 
                'content': form_content, 'errors': errors, 'params': params}

    def render(self, field_name, form_content, errors, requisites,
               context, filter, params, template_selector, global_namespace):
        '''Return HTML representation of field.
        field_name          - name of field
        form_content        - dictionary of strings to fill-in form as returned
                              by fetch or toForm
        errors              - dictionary of errors to fill
        requisites          - requisites object to store data needed to render
                              view (e.g. some JavaScript initialization to put
                              in <head>)
        template_selector   - callable object returning template for given
                              field type
        global_namespace    - global namespace for template
        context             - value context
        filter              - access control filter
        params              - may carry application-dependent parameters'''
        assert filter.show is not None
        self.fillRequisites(field_name, form_content, errors, requisites,
                            context, filter, params)
        local_namespace = self.prepareNamespace(
                                        field_name, form_content, errors,
                                        requisites, context, filter, params,
                                        template_selector, global_namespace)
        template = template_selector(self, filter.show)
        fp = Writer()
        template.interpret(fp, global_namespace, local_namespace)
        return fp.getvalue()

    def fetch(self, form, field_name, context, params):
        return {field_name.inForm: form.getString(field_name.inForm, '')}

    def fromForm(self, field_name, form_content, context, params):
        '''Selects field value from form_content for the field and converts to
        Python object.  The second returned object is a dictionary of
        errors.'''
        return {field_name: form_content[field_name.inForm]}, {}

    def accept(self, form, field_name, context, filter, params):
        assert filter.accept
        form_content = self.fetch(form, field_name, context, params)
        value, errors = self.fromForm(field_name, form_content, context,
                                      params)
        return form_content, value, errors

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        assert filter.event
        for handle in self.eventHandlers:
            handle(self, field_name, event, context, filter, actions, params,
                   template_selector, global_namespace)


class Converter:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def fromForm(self, field_type, value, context, params):
        return value, None

    def toForm(self, field_type, value):
        return value


class ScalarField(Field):
    
    converter = Converter()
    
    def fromForm(self, field_name, form_content, context, params):
        value, error = self.converter.fromForm(
                        self, form_content[field_name.inForm], context, params)
        if error is None:
            return {field_name: value}, {}
        else:
            return {}, {field_name.inForm: error}

    def toForm(self, field_name, context, filter):
        assert filter.show is not None
        return {field_name.inForm:
                self.converter.toForm(self, context.value[field_name])}


class FieldGroup(Field):

    subfields = [] # List of name-type pairs
    dictClass = dict

    def getDefault(self, field_name, context, params):
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        for subfield_name, subfield_type in self.subfields:
            new_name = field_name.child(subfield_name, branch=False)
            value.update(
                    subfield_type.getDefault(new_name, context, params))
        return value

    def toForm(self, field_name, context, filter):
        assert filter.show is not None
        form_content = {}
        for subfield_name, subfield_type in self.subfields:
            new_name = field_name.child(subfield_name, branch=False)
            new_filter = filter(subfield_type, subfield_name, context)
            if new_filter.show is not None:
                form_content.update(subfield_type.toForm(new_name, context,
                                                         new_filter))
        return form_content

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        subfields = {}
        local_namespace = {'fieldName': field_name.inForm,
                           'fieldType': self, 'subfields': subfields,
                           'errors': errors, 'params': params}
        for subfield_name, subfield_type in self.subfields:
            new_name = field_name.child(subfield_name, branch=False)
            new_filter = filter(subfield_type, subfield_name, context)
            if new_filter.show is not None:
                subfields[subfield_name] = subfield_type.render(
                    new_name, form_content, errors, 
                    requisites, context, new_filter, params,
                    template_selector, global_namespace)
        return local_namespace

    def fetch(self, form, field_name, context, params):
        raise RuntimeError()

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError()

    def accept(self, form, field_name, context, filter, params):
        form_content = {}
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        errors = {}
        for subfield_name, subfield_type in self.subfields:
            new_name = field_name.child(subfield_name, branch=False)
            new_filter = filter(subfield_type, subfield_name, context)
            if new_filter.accept:
                subfield_form_content, subfield_value, subfield_errors = \
                    subfield_type.accept(form, new_name, context,
                                         new_filter, params)
                form_content.update(subfield_form_content)
                value.update(subfield_value)
                errors.update(subfield_errors)
            else:
                subfield_form_content = subfield_type.toForm(
                    new_name, context, filter)
                form_content.update(subfield_form_content)

        return form_content, value, errors

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        Field.handleEvent(self, field_name, event, context, filter, actions,
                          params, template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        for subfield_name, subfield_type in self.subfields:
            new_name = field_name.child(subfield_name, branch=False)
            new_filter = filter(subfield_type, subfield_name, context)
            if new_filter.event:
                subfield_type.handleEvent(new_name, event, context, new_filter,
                                          actions, params,
                                          template_selector, global_namespace)


class Event:

    def __init__(self, id, form):
        self.id = id
        self.form = form


class FormEventParser:

    def __init__(self, event_id_field='event'):
        self.eventIdField = event_id_field

    def __call__(self, form):
        event_id = form.getString(self.eventIdField)
        return Event(event_id, form)


class EventHandler:

    def __init__(self, event_id):
        self.eventId = event_id

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        return []  # Do nothing in default class

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if event.id==self.eventId:
            actions.extend(self.actions(field_type, field_name, event, context,
                                        filter, params, template_selector,
                                        global_namespace))


class View:

    def __init__(self, field_group, get_template, template_name='view', 
                 event_template_name='event', parse_event=FormEventParser(),
                 global_namespace={}, content_type='text/html',
                 charset=None):
        self.fieldGroup = field_group
        self.templateName = template_name
        self.eventTemplateName = event_template_name
        self.parseEvent = parse_event
        self.getTemplate = get_template
        self.templateSelector = FieldTemplateSelector(get_template)
        self.globalNamespace = global_namespace
        self.contentType = content_type
        self.charset = charset

    def createRequisites(self):
        return {}
    
    def render(self, form_content, errors, context, filter=ACFilter(),
               params=None):
        requisites = self.createRequisites()
        content = self.fieldGroup.render(
                                FieldName(), form_content, errors, 
                                requisites, context, filter, params, 
                                self.templateSelector, self.globalNamespace)
        template = self.getTemplate(self.templateName)
        fp = Writer()
        local_namespace = {'content': content, 'requisites': requisites,
                           'params': params}
        template.interpret(fp, self.globalNamespace, local_namespace)
        return fp.getvalue()

    def show(self, value=None, filter=ACFilter(),
             params=None):
        if value is None:
            value = self.fieldGroup.getDefault(FieldName(), Context({}),
                                               params)
        form_content = {}
        context = Context(value)
        form_content = self.fieldGroup.toForm(FieldName(), context, filter)
        content = self.render(form_content, {}, context, filter, params)
        return content

    def accept(self, form, value=None, filter=ACFilter(),
               params=None):
        if value is None:
            value = self.fieldGroup.getDefault(FieldName(), Context({}),
                                               params)
        context = Context(value)
        form_content, new_value, errors = \
            self.fieldGroup.accept(form, FieldName(), context, filter, params)
        if errors:
            logging.info('Errors: %r', errors)
            context = Context(new_value)
            return None, self.render(form_content, errors, context, filter,
                                     params))
        else:
            return new_value, None

    def event(self, form, value=None, filter=ACFilter(),
              params=None):
        if value is None:
            value = self.fieldGroup.getDefault(FieldName(), Context({}),
                                               params)
        event = self.parseEvent(form)
        context = Context(value)
        actions = []
        self.fieldGroup.handleEvent(
                        FieldName(), event, context, filter, actions, params,
                        self.templateSelector, self.globalNamespace)
        logging.info('actions: %r', actions)
        template = self.getTemplate(self.eventTemplateName)
        fp = Writer()
        local_namespace = {'actions': actions, 'params': params}
        template.interpret(fp, self.globalNamespace, local_namespace)
        return fp.getvalue()
