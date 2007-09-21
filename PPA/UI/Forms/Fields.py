# $Id: Fields.py,v 1.17 2007/08/08 16:03:21 ods Exp $

import sys, logging, inspect, Converters
from PPA.Utils import interpolateString

logger = logging.getLogger(__name__)


class Field(object):

    typeName = None # Never assign other value to this attribute in class that
                    # can be used as base, since this will break template
                    # search algorithm.
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
        for name, value in kwargs.items():
            setattr(self, name, value)
        #self.__dict__.update(kwargs)

    def fromCode(self, value, params):
        return value
    
    def getDefault(self, context):
        return {context.name: self.fromCode(self.default,
                                            context.state.params)}

    def toForm(self, context):
        '''Converts fields to strings and puts into form_content.'''
        return {context.nameInForm: context.scalar}

    def fillRequisites(self, context):
        for filler in self.requisitesFillers:
            filler(self, context)

    def prepareNamespace(self, context,
                         template_selector, global_namespace={}):
        # XXX Just pass state?
        state = context.state
        return dict(state.params, fieldName=context.nameInForm, fieldType=self,
                    content=state.form_content, errors=state.errors,
                    params=state.params)

    def render(self, context, template_selector, global_namespace):
        '''Return HTML representation of field.
        context             - name-value context
        template_selector   - callable object returning template for given
                              field type
        global_namespace    - global namespace for template'''
        self.fillRequisites(context)
        local_namespace = self.prepareNamespace(
                                context, template_selector, global_namespace)
        template = template_selector(self, context.acFilter.renderClass)
        return template.toString(global_namespace, local_namespace)

    def fetch(self, context, form):
        context.state.form_content[context.nameInForm] = \
                                    form.getString(context.nameInForm, '')

    def fromForm(self, context):
        '''Selects field value from form_content for the field and converts to
        Python object.  The second returned object is a dictionary of
        errors.'''
        form_value = context.state.form_content[context.nameInForm]
        return {context.name: form_value}, {}

    def accept(self, context, form):
        assert context.acFilter.accept
        self.fetch(context, form)
        return self.fromForm(context)

    def handleEvent(self, context, event, actions,
                    template_selector, global_namespace):
        # XXX assert context.acFilter.event
        for handle in self.eventHandlers:
            handle(self, context, context, actions,
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
                    *[self._conv_instance(i) for i in obj])
            else:
                self.converter = self._conv_instance(obj) or self.converter
        Field.__init__(self, *args, **kwargs)
    
    def fromForm(self, context):
        form_value = context.state.form_content[context.nameInForm]
        value, error = self.converter.fromForm(context, form_value)
        if error is None:
            return {context.name: value}, {}
        else:
            return {}, {context.nameInForm: error}

    def toForm(self, context):
        assert context.acFilter.renderClass is not None
        return {context.nameInForm: self.converter.toForm(context,
                                                          context.scalar)}


class Schema(Field):

    __required__ = ('subfields',)

    subfields = [] # List of name-type pairs
    dictClass = dict

    def copy(self):
        """Returns copy of itself, actually copies only subfields list"""
        return self.__class__(subfields=self.subfields[:],
                              dictClass=self.dictClass)
    
    def getDefault(self, context):
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_type, subfield_name)
            value.update(subfield_type.getDefault(subcontext))
        return value

    def toForm(self, context):
        assert context.acFilter.renderClass is not None
        form_content = {}
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_type, subfield_name)
            #new_filter = filter(subfield_type, subfield_name, context)
            if subcontext.acFilter.renderClass is not None:
                form_content.update(subfield_type.toForm(subcontext))
        return form_content

    def prepareNamespace(self, context,
                         template_selector, global_namespace={}):
        subfields = {}
        state = context.state
        ns = dict(state.params, fieldType=self, subfields=subfields,
                  errors=state.errors, params=state.params)
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_type, subfield_name)
            if subcontext.acFilter.renderClass is not None:
                subfields[subfield_name] = subfield_type.render(
                            subcontext, template_selector, global_namespace)
        return ns

    def fetch(self, context, form):
        raise RuntimeError()

    def fromForm(self, context):
        raise RuntimeError()

    def accept(self, context, form):
        value = context.value  # XXX otherwise references to other fields won't
                               # work
        errors = {}
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_type, subfield_name)
            if subcontext.acFilter.accept:
                subfield_value, subfield_errors = \
                    subfield_type.accept(subcontext, form)
                value.update(subfield_value)
                errors.update(subfield_errors)
            elif subcontext.acFilter.renderClass is not None:
                context.state.form_content.update(
                    subfield_type.toForm(subcontext))
        return value, errors

    def handleEvent(self, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        for subfield_name, subfield_type in self.subfields:
            subcontext = context.entry(subfield_type, subfield_name)
            if True: # XXX subcontext.acFilter.event:
                subfield_type.handleEvent(subcontext, event, actions,
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
    """Represents boolean fields, converted value is bool"""
    
    def fromForm(self, context):
        form_value = context.state.form_content[context.nameInForm]
        return {context.name: bool(form_value)}, {}


class DateTime(ScalarField):

    format = '%Y-%m-%d'
    parseError = u'Wrong date'
    converter = Converters.DateTime()
    allowNone = True
    default = None


class AbstractChoiceField(ScalarField):
    """Prototype for choice fields, children have to implement

    hasOption()
    getOptions()"""

    noneSelectedError = 'Nothing is selected'
    allowNone = True
    default = None
    noneLabel = '-'
    
    def getOptions(self, context):
        """Returns iterable of tuples (id, label)"""
        raise NotImplementedError()

    def hasOption(self, context, option):
        """Returns True if option (received from form) exists in Choice's
        options, False otherwise"""
        raise NotImplementedError()

    def getOptionLabel(self, context, option):
        """Returns label for the option"""
        raise NotImplementedError()

    def fromForm(self, context):
        form_value = context.state.form_content[context.nameInForm]
        value, error = self.converter.fromForm(context, form_value)
        if value:
            if not self.hasOption(context, value):
                value = None
        if value is None and not self.allowNone:
            return {}, {context.nameInForm: self.noneSelectedError}
        return {context.name: value}, {}

    def prepareNamespace(self, context,
                         template_selector, global_namespace={}):
        ns = ScalarField.prepareNamespace(self, context,
                                          template_selector, global_namespace)
        return dict(ns, options=self.getOptions(context))
    

class ListChoice(AbstractChoiceField):
    """Represents choice between options passed as list of tuples (id, lable):

    ListChoice(option=[(1, 'One'), (2, 'Two')])"""

    __required__ = ('options',)

    options = []  # List of (id, title) pairs

    def getOptions(self, context):
        return iter(self.options)

    def hasOption(self, context, option):
        return dict(self.options).has_key(option)

    def getOptionLabel(self, context, option):
        return dict(self.options).get(option, self.noneLabel)


class AbstractMultipleChoiceField(AbstractChoiceField): # this shouldn't be, MultipleChoice is no Scalar
    default = []

    def fetch(self, context, form):
        context.state.form_content[context.nameInForm] = \
            form.getStringList(context.nameInForm)
    
    def fromForm(self, context):
        result_value = []
        
        for id in context.state.form_content[context.nameInForm]:
            value, error = self.converter.fromForm(context, id)
            if value and self.hasOption(context, value):
                result_value.append(value)
        
        if not result_value and not self.allowNone:
            return {}, {context.nameInForm: self.noneSelectedError}
        return {context.name: result_value}, {}

    def toForm(self, context):
        assert context.acFilter.renderClass is not None
        value = []
        for item in context.scalar:
            value.append(self.converter.toForm(context, item))
        return {context.nameInForm: value}


class ListMultipleChoice(AbstractMultipleChoiceField):
    options = []  # List of (id, title) pairs
    
    __required__ = ('options',)

    def getOptions(self, context):
        return iter(self.options)

    def hasOption(self, context, option):
        return dict(self.options).has_key(option)
    

class Password(ScalarField):
    from md5 import new as digest # may be digest class or None
    mismatch_error = "Passwords doesn't match"

    def accept(self, context, form):
        confirm_context = context.entry(self, context.name+'-confirm')
        old_value = context.value[context.name]
        
        self.fetch(context, form)
        self.fetch(confirm_context, form)

        form_content = context.state.form_content
        passwd = form_content[context.nameInForm]
        confirm = form_content[confirm_context.nameInForm]

        if (passwd or confirm) or not old_value:
            value, errors = self.fromForm(context)
            if errors or passwd!=confirm:
                form_content[context.nameInForm] = \
                    form_content[confirm_context.nameInForm] = ''
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

    def getDefault(self, context):
        items = []
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(self.itemField, item_field_name,
                                         value={})
            item_value = self.itemField.getDefault(item_context)
            items.append(item_value[item_context.name])
        return {context.name: items}

    def toForm(self, context):
        items = context.scalar
        assert len(items)==self.length
        for index, value in enumerate(items):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(self.itemField, item_field_name,
                                         {item_field_name: value})
            if item_context.acFilter.renderClass is None:
                continue
            form_content.update(self.itemField.toForm(item_context))
        return form_content

    def prepareNamespace(self, context,
                         template_selector, global_namespace={}):
        items = []
        state = context.state
        ns = dict(state.params, fieldName=context.nameInForm, fieldType=self,
                  items=items, errors=state.errors, params=state.params)
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            value = context.scalar[index]
            item_context = context.entry(self.itemField, item_field_name,
                                         {item_field_name: value})
            if item_context.acFilter.renderClass is None:
                continue
            items.append(self.itemField.render(
                            item_context, template_selector, global_namespace))
        return ns

    def fetch(self, context, form):
        raise RuntimeError

    def fromForm(self, context):
        raise RuntimeError

    def accept(self, context, form):
        form_content = {}
        items = context.scalar
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(self.itemField, item_field_name,
                                         {item_field_name: items[index]})
            if not item_context.acFilter.accept:
                continue
            item_field_value, item_field_errors = \
                                    self.itemField.accept(item_context, form)
            # subvalue can be left empty if error occured
            assert item_field_value.keys() in ([item_field_name], []), \
                                                self._bad_field_error
            if item_field_value.has_key(item_field_name):
                items[index] = item_field_value[item_field_name]
            context.state.errors.update(item_field_errors)
        return {field_name: items}, errors

    def handleEvent(self, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        items = context.scalar
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(self.itemField, item_field_name,
                                         {item_field_name: items[index]})
            #if not item_context.acFilter.event:
            #    continue
            self.itemField.handleEvent(item_context, event, actions,
                                       template_selector, global_namespace)


class Container(Field):

    schema = Schema(subfields=[])

    def getDefault(self, context):
        new_context = context.branch(self.schema)
        return {context.name: self.schema.getDefault(new_context)}

    def toForm(self, context):
        new_context = context.branch(self.schema, context.scalar)
        if new_context.acFilter.renderClass is None:
            return {}
        return self.schema.toForm(new_context)

    def prepareNamespace(self, context,
                         template_selector, global_namespace={}):
        # XXX Or just render them into content variable?
        new_context = context.branch(self.schema, context.scalar)
        if new_context.acFilter.renderClass is None:
            ns = {'subfields': {}}
        else:
            ns = self.schema.prepareNamespace(
                            new_context, template_selector, global_namespace)
        return dict(ns, fieldName=context.nameInForm, fieldType=self)

    def fetch(self, context, form):
        raise RuntimeError

    def fromForm(self, context):
        raise RuntimeError

    def accept(self, context, form):
        if not context.value.has_key(context.name):
            new_context = context.branch(self.schema)
            context.value.update(self.getDefault(new_context))
        new_context = context.branch(self.schema, context.scalar)
        if not new_context.acFilter.accept:
            return {}, {}
        value, errors = self.schema.accept(new_context, form)
        return {context.name: value}, errors

    def handleEvent(self, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, context, event, actions,
                          template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        new_context = context.branch(self.schema, context.scalar)
        if True: # XXX new_context.acFilter.event:
            self.schema.handleEvent(new_context, event, actions,
                                    template_selector, global_namespace)


class Placeholder(Field):

    def getDefault(self, context):
        return {}

    def toForm(self, context):
        return {}

    def fetch(self, context, form):
        raise RuntimeError

    def fromForm(self, context):
        raise RuntimeError

    def accept(self, context, form):
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
    
    def getDefault(self, context):
        spec = self.optionSpec(context)
        return spec.getDefault(context)

    def toForm(self, context):
        spec = self.optionSpec(context)
        new_context = context.entry(spec, context.name)
        if new_context.acFilter.renderClass is None:
            return {}
        return spec.toForm(new_context)

    def fillRequisites(self, context):
        raise RuntimeError

    def render(self, context, template_selector, global_namespace):
        spec = self.optionSpec(context)
        new_context = context.entry(spec, context.name)
        if new_context.acFilter.renderClass is None:
            return '' # XXX
        return spec.render(context, template_selector, global_namespace)

    def fetch(self, context, form):
        raise RuntimeError

    def fromForm(self, context):
        raise RuntimeError

    def accept(self, context, form):
        spec = self.optionSpec(context)
        new_context = context.entry(spec, context.name)
        if not new_context.acFilter.accept:
            return {}, {}
        return spec.accept(context, form)

    def handleEvent(self, context, event, actions,
                    template_selector, global_namespace):
        Field.handleEvent(self, context, event, actions,
                          template_selector, global_namespace)
        spec = self.optionSpec(context)
        new_context = context.entry(spec, context.name)
        if True: # XXX new_context.acFilter.event:
            spec.handleEvent(context, event, actions,
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

    def accept(self, context, form):
        import os.path
        
        sources = []
        url_context = context.entry(self, context.name+'-url')
        servfile_context = context.entry(self, context.name+'-sid')
        filename_context = context.entry(self, context.name+'-filename')

        self.fetch(url_context, form)
        form_content = context.state.form_content
        form_content[context.nameInForm] = context.scalar
        form_content[servfile_context.nameInForm] = '' # default values
        form_content[filename_context.nameInForm] = ''

        if self.allowUpload:
            upload_context = context.entry(self, context.name+'-upload')
            fieldstorage_file = form.getFile(upload_context.nameInForm)
            if fieldstorage_file is not None:
                filename = fieldstorage_file.filename or ''
                remotefile = fieldstorage_file.file
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
                url = form_content[url_context.nameInForm]
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
                form_content[filename_context.nameInForm] = remotename
                return self.checkFile(context, localpath, remotename)
        if self.allowNone:
            return {}, {}
        else:
            return {}, {context.nameInForm: self.noneFileError}

    def checkFile(self, context, path, name):
        """The only overridable method,
        path - path to temprorary file,
        name - client file name.

        Return touple of value and errors hashes"""

        value = self._File(tmpname=path, remotename=name)
        value, error = self.converter.fromForm(context, value)
        if error is None:
            return {context.name: value}, {}
        else:
            return {}, {context.nameInForm: error}


class Image(File):
    width = None
    height = None
    action = None # 'resize' or 'thumb'
    filter = "ANTIALIAS" # getattr(PIL.Image, filter)
    
    def checkFile(self, context, path, name):
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
