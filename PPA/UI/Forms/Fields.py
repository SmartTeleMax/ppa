# $Id$

import sys, logging, inspect, Converters
from PPA.Utils import interpolateString

logger = logging.getLogger(__name__)


class Field(object):

    typeName = None
    default = ''
    requisitesFillers = []
    eventHandlers = []
    __required__ = ()

    def __init__(self, requisitesFillers=[], eventHandlers=[], **kwargs):
        self.requisitesFillers = self.requisitesFillers + requisitesFillers
        self.eventHandlers = self.eventHandlers + eventHandlers

        for name in self.__required__:
            try:
                value = kwargs.pop(name)
                setattr(self, name, value)
            except KeyError:
                raise ValueError('Required param %r for field %r omited' % \
                                 (name, self.__class__.__name__))
        self.__dict__.update(kwargs)

    def fromCode(self, value, params):
        return value
    
    def getDefault(self, state, context):
        return {context.name: self.fromCode(self.default, state.params)}

    def toForm(self, state, context):
        '''Converts fields to strings and puts into form_content.'''
        return {context.nameInForm: context.scalar}

    def fillRequisites(self, state, context, requisites):
        for filler in self.requisitesFillers:
            filler(self, state, context, requisites)

    def prepareNamespace(self, state, context, requisites,
                         template_selector, global_namespace={}):
        # XXX Just pass state?
        return dict(state.params, fieldName=context.nameInForm, fieldType=self,
                    content=state.form_content, errors=state.errors,
                    params=state.params)

    def render(self, state, context, requisites, template_selector,
               global_namespace):
        '''Return HTML representation of field.
        state               - current form state
        context             - name-value context
        requisites          - requisites object to store data needed to render
                              view (e.g. some JavaScript initialization to put
                              in <head>)
        template_selector   - callable object returning template for given
                              field type
        global_namespace    - global namespace for template'''
        self.fillRequisites(state, context, requisites)
        local_namespace = self.prepareNamespace(
                                        state, context, requisites,
                                        template_selector, global_namespace)
        template = template_selector(self, 'edit') # XXX filter.show
        return template.toString(global_namespace, local_namespace)

    def fetch(self, state, context, form):
        state.form_content[context.nameInForm] = \
                                    form.getString(context.nameInForm, '')

    def fromForm(self, state, context):
        '''Selects field value from form_content for the field and converts to
        Python object.  The second returned object is a dictionary of
        errors.'''
        return {context.name: state.form_content[context.nameInForm]}, {}

    def accept(self, state, context, form):
        # XXX assert filter.accept
        self.fetch(state, context, form)
        return self.fromForm(state, context)

    def handleEvent(self, state, context, event, actions,
                    template_selector, global_namespace):
        # XXX assert filter.event
        for handle in self.eventHandlers:
            handle(self, state, context, context, actions,
                   template_selector, global_namespace)


class ScalarField(Field):

    """Scalar (represented in html by one html controle) field class.

    Scalar fields may have converters, provide convertes in 'converters'
    keyword argument to __init__.

    1. If converter doesn't need any arguments - you may provide a class,
    it will be instantiated:

    ScalarField(converter=Converters.NotNull)

    2. If converter requires arguments - provide an instance:

    ScalarField(converter=Converters.Number(type=int, minValue=-sys.maxint-1,
                                            maxValue=sys.maxint))

    3. If you have a list of converters just give field a list:

    ScalarField(converter=[NotNull, Strip, Pattern('^http://.*')])
    """
    
    converter = Converters.Converter()

    def _conv_instance(self, obj):
        if inspect.isclass(obj) and issubclass(obj, Converters.Converter):
            obj = obj()
        return obj

    def __init__(self, *args, **kwargs):
        try:
            obj = kwargs.pop('converter')
        except KeyError:
            pass
        else:
            if isinstance(obj, (list, tuple)):
                self.converter = Converters.Chain(
                    [self._conv_instance(i) for i in obj])
            else:
                self.converter = self._conv_instance(obj) or self.converter
        Field.__init__(self, *args, **kwargs)
    
    def fromForm(self, state, context):
        value, error = self.converter.fromForm(
                                        state, context, self,
                                        state.form_content[context.nameInForm])
        if error is None:
            return {context.name: value}, {}
        else:
            return {}, {context.nameInForm: error}

    def toForm(self, state, context):
        # XXX assert filter.show is not None
        return {context.nameInForm:
                self.converter.toForm(self, context.scalar)}


class Schema(Field):

    __required__ = ('subfields',)

    subfields = [] # List of name-type pairs
    dictClass = dict

    def getDefault(self, state, context):
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_name)
            value.update(subfield_type.getDefault(state, subcontext))
        return value

    def toForm(self, state, context):
        # XXX assert filter.show is not None
        form_content = {}
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_name)
            #new_filter = filter(subfield_type, subfield_name, context)
            if True: # XXX new_filter.show is not None:
                form_content.update(subfield_type.toForm(state, subcontext))
        return form_content

    def prepareNamespace(self, state, context, requisites,
                         template_selector, global_namespace={}):
        subfields = {}
        ns = dict(state.params, fieldName=context.nameInForm, fieldType=self,
                  subfields=subfields, errors=state.errors,
                  params=state.params)
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_name)
            # XXX new_filter = filter(subfield_type, subfield_name, context)
            if True: # XXX new_filter.show is not None:
                subfields[subfield_name] = subfield_type.render(
                                        state, subcontext, requisites,
                                        template_selector, global_namespace)
        return ns

    def fetch(self, state, context, form):
        raise RuntimeError()

    def fromForm(self, state, context):
        raise RuntimeError()

    def accept(self, state, context, form):
        form_content = {}
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        errors = {}
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_name)
            # XXX new_filter = filter(subfield_type, subfield_name, context)
            if True: # XXX new_filter.accept:
                subfield_value, subfield_errors = \
                    subfield_type.accept(state, subcontext, form)
                value.update(subfield_value)
                errors.update(subfield_errors)
            else:
                subfield_type.toForm(state, subcontext)

        return value, errors

    def handleEvent(self, state, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, state, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_name)
            # XXX new_filter = filter(subfield_type, subfield_name, context)
            if True: # XXX new_filter.event:
                subfield_type.handleEvent(state, subcontext, event, actions,
                                          template_selector, global_namespace)


class String(ScalarField):
    """Represents string fields, converted value is unicode"""
    
    pass


class Integer(ScalarField):
    """Represents integer fields, converted value is controlled by converter"""
    
    allowNone = False
    default = 0
    converter = Converters.Number(type=int, minValue=-sys.maxint-1,
                                  maxValue=sys.maxint)


class Boolean(Field):
    """Represents boolean fields, cobverted value is bool"""
    
    def fromForm(self, state, context):
        return {context.name: bool(state.form_content[context.nameInForm])}, {}


class AbstractChoiceField(ScalarField):
    """Prototype for choice fields, children have to implement

    hasOption()
    getOptions()"""

    noneSelectedError = 'Nothing is selected'
    allowNone = True
    default = None
    
    def getOptions(self, state, context):
        """Returns iterable of tuples (id, label)"""
        raise NotImplementedError()

    def hasOption(self, state, context, option):
        """Returns True if option (received from form) exists in Choice's
        options, False otherwise"""
        raise NotImplementedError()

    def fromForm(self, state, context):
        value, error = self.converter.fromForm(
                                        state, context, self,
                                        state.form_content[context.nameInForm])
        if value:
            if not self.hasOption(state, context, value):
                value = None
        if value is None and not self.allowNone:
            return {}, {context.nameInForm: self.noneSelectedError}
        return {context.name: value}, {}

    def prepareNamespace(self, state, context, requisites,
                         template_selector, global_namespace={}):
        ns = Field.prepareNamespace(self, state, context, requisites,
                                    template_selector, global_namespace)
        return dict(ns, options=self.getOptions(state, context))
    

class ListChoice(AbstractChoiceField):
    """Represents choice between options passed as list of tuples (id, lable):

    ListChoice(option=[(1, 'One'), (2, 'Two')])"""

    __required__ = ('options',)

    options = []  # List of (id, title) pairs

    def getOptions(self, state, context):
        return iter(self.options)

    def hasOption(self, state, context, option):
        return dict(self.options).has_key(option)





class MultipleChoice(ListChoice): # this shouldn't be, MultipleChoice is no Scalar
    default = []

    def fetch(self, state, context, form):
        return {context.nameInForm: form.getStringList(context.nameInForm)}
    
    def fromForm(self, state, context):
        result_value = []
        # XXX use hasOption?
        options_dict = dict(self.getOptions(state, context))
        
        for item in form_content[context.nameInForm]:
            value, error = self.converter.fromForm(state, context, self, item)
            if options_dict.has_key(value):
                result_value.append(value)
        
        if not result_value and not self.allowNone:
            return {}, {context.nameInForm: self.noneSelectedError}
        return {context.name: result_value}, {}

    def toForm(self, state, context):
        # XXX assert filter.show is not None
        value = []
        for item in context.scalar:
            value.append(self.converter.toForm(self, item))
        return {context.nameInForm: value}
    

class Password(ScalarField):
    from md5 import new as digest # may be digest class or None
    mismatch_error = "Passwords doesn't match"

    def accept(self, state, context, form):
        confirm_context = context.entry(context.name+'-confirm')
        old_value = context.value[context.name]
        
        self.fetch(state, context, form)
        self.fetch(state, confirm_context, form)

        passwd = state.form_content[context.nameInForm]
        confirm = state.form_content[confirm_context.nameInForm]

        if (passwd or confirm) or not old_value:
            value, errors = self.fromForm(state, context)
            if errors or passwd!=confirm:
                state.form_content[context.nameInForm] = \
                    state.form_content[confirm_context.nameInForm] = ''
                if not errors: # add error only if no other errors occured
                    errors = {context.nameInForm: self.mismatch_error}
            else:
                if self.digest:
                    value[context.name] = \
                            self.digest(value[context.name]).hexdigest()
            return value, errors
        else:
            return {context.name: old_value}, {}

        
class FixedList(Field):

    itemField = String()
    _bad_field_error = 'itemField must be scalar Field or '\
                                        'Agregate, not Schema'
    length = 3

    def itemFieldName(self, field_name, index):
        return '%s-%d' % (field_name, index)

    def getDefault(self, state, context):
        items = []
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(item_field_name, value={})
            item_value = self.itemField.getDefault(state, item_context)
            items.append(item_value[item_context.name])
        return {context.name: items}

    def toForm(self, state, context):
        items = context.scalar
        assert len(items)==self.length
        for index, value in enumerate(items):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(item_field_name,
                                         {item_field_name: value})
            # XXX new_filter = filter(self.itemField, item_field_name, new_context)
            #if new_filter.show is None:
            #    continue
            form_content.update(self.itemField.toForm(state, item_context))
        return form_content

    def prepareNamespace(self, state, context, requisites,
                         template_selector, global_namespace={}):
        items = []
        ns = dict(state.params, fieldName=context.nameInForm, fieldType=self,
                  items=items, errors=state.errors, params=state.params)
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            value = context.scalar[index]
            item_context = context.entry(item_field_name,
                                         {item_field_name: value})
            # XXX new_filter = filter(self.itemField, item_field_name, new_context)
            #if new_filter.show is None:
            #    continue
            items.append(self.itemField.render(
                                        state, item_context, requisites,
                                        template_selector, global_namespace))
        return ns

    def fetch(self, state, context, form):
        raise RuntimeError

    def fromForm(self, state, context):
        raise RuntimeError

    def accept(self, state, context, form):
        form_content = {}
        items = context.scalar
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(item_field_name,
                                         {item_field_name: items[index]})
            # XXX new_filter = filter(self.itemField, item_field_name, new_context)
            #if not new_filter.accept:
            #    continue
            item_field_value, item_field_errors = \
                            self.itemField.accept(state, item_context, form)
            # subvalue can be left empty if error occured
            assert item_field_value.keys() in ([item_field_name], []), \
                                                self._bad_field_error
            if item_field_value.has_key(item_field_name):
                items[index] = item_field_value[item_field_name]
            state.errors.update(item_field_errors)
        return {field_name: items}, errors

    def handleEvent(self, state, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, state, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        items = context.scalar
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(item_field_name,
                                         {item_field_name: items[index]})
            # XXX new_filter = filter(self.itemField, item_field_name, new_context)
            #if not new_filter.event:
            #    continue
            self.itemField.handleEvent(state, item_context, event, actions,
                                       template_selector, global_namespace)


class Container(Field):

    schema = Schema(subfields=[])

    def getDefault(self, state, context):
        new_context = context.branch()
        return {context.name: self.schema.getDefault(state, new_context)}

    def toForm(self, state, context):
        new_context = context.branch(context.scalar)
        # XXX new_filter = filter(self.schema, new_name, new_context)
        #if new_filter.show is None:
        #    return {}
        return self.schema.toForm(state, new_context)

    def prepareNamespace(self, state, context, requisites,
                         template_selector, global_namespace={}):
        # XXX Or just render them into content variable?
        new_context = context.branch(context.scalar)
        # XXX new_filter = filter(self.schema, new_name, new_context)
        #if new_filter.show is None:
        #    ns = {'subfields': {}}
        #else:
        ns = self.schema.prepareNamespace(
                                    state, new_context, requisites,
                                    template_selector, global_namespace)
        return dict(ns, fieldName=context.nameInForm, fieldType=self)

    def fetch(self, state, context, form):
        raise RuntimeError

    def fromForm(self, state, context):
        raise RuntimeError

    def accept(self, state, context, form):
        if not context.value.has_key(field_name):
            new_context = context.branch()
            context.value.update(self.getDefault(state, new_context))
        new_context = context.branch(context.scalar)
        # XXX new_filter = filter(self.schema, new_name, new_context)
        #if not new_filter.accept:
        #    return {}, {}, {}
        value, errors = self.schema.accept(state, new_context, form)
        return {field_name: value}, errors

    def handleEvent(self, state, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, state, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        new_context = context.branch(context.scalar)
        # XXX new_filter = filter(self.schema, new_name, new_context)
        if True: # XXX new_filter.event:
            self.schema.handleEvent(state, new_context, event, actions,
                                    template_selector, global_namespace)


class Placeholder(Field):

    def getDefault(self, state, context):
        return {}

    def toForm(self, state, context):
        return {}

    def fetch(self, state, context, form):
        raise RuntimeError

    def fromForm(self, state, context):
        raise RuntimeError

    def accept(self, state, context, form):
        return {}, {}


class SwitchField(Field):

    switcherPath = None
    optionSpecs = {}
    defaultOptionSpec = Placeholder()

    def optionSpec(self, context):
        value = context[self.switcherPath]
        try:
            return self.optionSpecs[value]
        except KeyError:
            return self.defaultOptionSpec
    
    def getDefault(self, state, context):
        spec = self.optionSpec(context)
        return spec.getDefault(state, context)

    def toForm(self, state, context):
        spec = self.optionSpec(context)
        # XXX new_filter = filter(spec, field_name, context)
        #if new_filter.show is None:
        #    return {}
        return spec.toForm(state, context)

    def fillRequisites(self, state, context, requisites):
        raise RuntimeError

    def render(self, state, context, requisites,
               template_selector, global_namespace):
        spec = self.optionSpec(context)
        # XXX new_filter = filter(spec, field_name, context)
        #if new_filter.show is None:
        #    return '' # XXX
        return spec.render(state, context, requisites,
                           template_selector, global_namespace)

    def fetch(self, state, context, form):
        raise RuntimeError

    def fromForm(self, state, context):
        raise RuntimeError

    def accept(self, state, context, form):
        spec = self.optionSpec(context)
        # XXX new_filter = filter(spec, field_name, context)
        #if not new_filter.accept:
        #    return {}, {}, {}
        return spec.accept(state, context, form)

    def handleEvent(self, state, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, state, context, event, actions,
                          template_selector, global_namespace)
        spec = self.optionSpec(context)
        # XXX new_filter = filter(spec, field_name, context)
        if True: # XXX new_filter.event:
            spec.handleEvent(state, context, event, actions,
                             template_selector, global_namespace)


class File(Field):
    root = None # webroot
    tempDir = '/tmp' # directory to store temprorary files in
    allowUpload = True # allows to upload file
    allowFetch = False # allows to fetch file from url
    allowNone = True
    noneFileError = "This field cant be empty"

    class _File:
        def __init__(self, tmpname=None, url=None, remotename=None):
            self.tmpname = tmpname
            self.url = url
            self.remotename = remotename

        def path(self):
            return self.url

        def name(self):
            return self.url.split('/')[-1]

        def __nonzero__(self):
            return bool(self.url or self.tmpname)
        

    default = _File()

    def nameGenerator():
        import random, string
        return ''.join(
            [random.choice(string.ascii_letters) for i in range(20)])
    nameGenerator = staticmethod(nameGenerator)

    def accept(self, state, context, form):
        import os.path
        
        sources = []
        url_context = context.entry(context.name+'-url')
        servfile_context = context.entry(context.name+'-sid')
        filename_context = context.entry(context.name+'-filename')

        self.fetch(state, url_context, form)
        state.form_content[context.nameInForm] = context.scalar
        state.form_content[servfile_context.nameInForm] = '' # default values
        state.form_content[filename_context.nameInForm] = ''

        if self.allowUpload:
            upload_context = context.entry(context.name+'-upload')
            try:
                filename = form[upload_context.nameInForm].filename or ''
                remotefile = form[upload_context.nameInForm].file
            except (KeyError, AttributeError):
                pass
            else:
                if remotefile:
                    # some browsers pass fullpath of file
                    for sep in ('/', '\\'):
                        pos = filename.rfind(sep)
                        if pos!=-1:
                            filename = filename[pos+1:]
                            break
                    sources.append((filename, remotefile))
        if self.allowFetch:
            try:
                url = state.form_content[url_context.nameInForm]
                if url:
                    referer = '/'.join(url.split('/')[:-1])+'/'
                    import urllib2
                    req = urllib2.Request(url=url)
                    req.add_header('Referer', referer)
                    remotefile = urllib2.urlopen(req)
                    if remotefile:
                        sources.append((url.split('/')[-1], remotefile))
            except ValueError:
                pass
            except IOError, why:
                return {}, {field_name: str(why)}

        for remotename, file in sources:
            data = file.read()
            if not data:
                continue
            else:
                localname = self.nameGenerator()
                localpath = os.path.join(self.tempDir, localname)
                open(localpath, 'w').write(data)
                state.form_content[filename_context.nameInForm] = remotename
                return self.checkFile(state, context, localpath, remotename)
        if self.allowNone:
            return {}, {}
        else:
            return {}, {context.nameInForm: self.noneFileError}

    def checkFile(self, state, context, path, name):
        """The only overridable method,
        path - path to temprorary file,
        name - client file name.

        Return touple of value and errors hashes"""

        value = self._File(tmpname=path, remotename=name)
        value, error = self.converter.fromForm(state, context, self, value)
        if error is None:
            return {context.name: value}, {}
        else:
            return {}, {context.nameInForm: error}


class Image(File):
    width = None
    height = None
    action = None # 'resize' or 'thumb'
    filter = "ANTIALIAS" # getattr(PIL.Image, filter)
    
    def checkFile(self, state, context, path, name):
        import PIL.Image, os
        try:
            image = PIL.Image.open(open(path))
        except IOError:
            from PPA.Template.Cook import quoteHTML
            return {}, {context.nameInForm: \
                        'Broken image in %s' % quoteHTML(name)}
        if self.action and (self.height and self.width):
            format = image.format
            transform = getattr(self, '_transform_%s' % self.action)
            image, error = transform(image)
            if image:
                from cStringIO import StringIO
                f = StringIO()
                image.save(f, format)
                open(path, 'w').write(f.getvalue())
            elif error:
                return {}, {context.nameInForm: error}

        return {context.name: self._File(tmpname=path, remotename=name)}, {}

    def _transform_resize(self, image):
        """Resizes image (PIL.Image) to self.width, self.height with original
        ratio.

        Returns tuple (image (PIL.Image|None), error (str|None))"""
        
        import PIL.Image
        filter = getattr(PIL.Image, self.filter)
        orig_image = image
        w,h = image.size
        maxw, maxh = self.width, self.height

        if maxw and w > maxw:
            image = image.resize((maxw, maxw*h/w), filter)
            w,h = image.size
        if maxh and h > maxh:
            image = image.resize((w*maxh/h, maxh), filter)
        return image, None

    def _transform_thumb(self, image):
        """Thumbnails (resize+crop) image (PIL.Image) 
        to self.width, self.height with ratio self.width X self.height.
        
        Returns tuple (image (PIL.Image|None), error (str|None))"""
        w, h = image.size
        if w > self.width or h > self.height:
            try:
                image = self._thumbnail(image)
            except IOError, why:
                return None, str(why)
            else:
                return image, None
        else:
            return image, None
        
    def _thumbnail(self, image):
        import PIL.Image
        filter = getattr(PIL.Image, self.filter)
        w, h = image.size

        if float(h)/w > float(self.height)/self.width:
            size = (self.width, self.width*h/w)
            image = image.resize(size, filter)
            w,h = image.size
            rect = (0,
                    (h-self.height)/2,
                    self.width,
                    (h-self.height)/2+self.height
                    )
            image = image.crop(rect)
        else:
            size = (self.height*w/h, self.height)
            image = image.resize(size, filter)
            w,h = image.size
            rect = ((w-self.width)/2,
                    0,
                    (w-self.width)/2+self.width,
                    self.height
                    )
            image = image.crop(rect)
        return image


# vim: set sts=4 sw=4 ai et:
