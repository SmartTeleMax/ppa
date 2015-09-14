from Base import Field, ScalarField, Converter, FieldGroup, View, Context, \
                 Writer, EventHandler, FieldName
import Converters
import sys, itertools, logging
logger = logging.getLogger(__name__)
from PPA.Utils import interpolateString


class String(ScalarField):

    converter = Converter()


class Integer(ScalarField):

    allowNone = False
    default = 0
    converter = Converters.Number(type=int, minValue=-sys.maxint-1,
                                  maxValue=sys.maxint)


class Boolean(Field):
    def fromForm(self, field_name, form_content, context, params):
        return {field_name: bool(form_content[field_name.inForm])}, {}


class Choice(ScalarField):

    options = []  # List of (id, title) pairs
    allowNone = True
    default = None
    converter = Converter()
    noneSelectedError = 'XXX None selected error'

    class _OptionsInTemplate:
        def __init__(self, field_type, context, params):
            self._field_type = field_type
            self._context = context
            self._params = params
        def __iter__(self):
            field_type = self._field_type
            for value, title in field_type.getOptions(self._context,
                                                      self._params):
                yield field_type.converter.toForm(field_type, value), title

    @staticmethod
    def optionsRetriever(field_type, context, params):
        return iter(field_type.options)

    def getOptions(self, context, params):
        return self.optionsRetriever(self, context, params)

    def fromForm(self, field_name, form_content, context, params):
        value, error = self.converter.fromForm(
                        self, form_content[field_name.inForm], context, params)
        # Ignore error, assume nothing is selected
        options_dict = dict(self.getOptions(context, params))
        if not options_dict.has_key(value):
            value = None
        if value is None and not self.allowNone:
            return {}, {field_name.inForm: self.noneSelectedError}
        return {field_name: value}, {}

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        local_namespace = Field.prepareNamespace(
                                self, field_name, form_content,
                                errors, requisites, context, filter, params,
                                template_selector, global_namespace)
        local_namespace['options'] = self._OptionsInTemplate(self, context,
                                                             params)
        return local_namespace


class MultipleChoice(Choice): # this shouldn't be, MultipleChoice is no Scalar
    def fetch(self, form, field_name, context, params):
        return {field_name.inForm: form.getlist(field_name.inForm)}

    def fromForm(self, field_name, form_content, context, params):
        result_value = []
        options_dict = dict(self.getOptions(context, params))

        for i in form_content[field_name.inForm]:
            value, error = self.converter.fromForm(
                self, i, context, params)
            if options_dict.has_key(value):
                result_value.append(value)

        if not result_value and not self.allowNone:
            return {}, {field_name.inForm: self.noneSelectedError}
        return {field_name: result_value}, {}

    def toForm(self, field_name, context, filter):
        assert filter.show is not None
        value = []
        for i in context.value[field_name]:
            value.append(self.converter.toForm(self, i))
        return {field_name.inForm: value}


class Password(ScalarField):
    from md5 import new as digest # may be digest class or None
    mismatch_error = "Passwords doesn't match"

    def accept(self, form, field_name, context, filter, params):
        confirm_name = field_name.child(field_name+'-confirm', branch=False)
        old_value = context.value[field_name]

        fc = {}
        fc.update(self.fetch(form, field_name, context, params))
        fc.update(self.fetch(form, confirm_name, context, params))

        passwd = fc[field_name.inForm]
        confirm = fc[confirm_name.inForm]

        if (passwd or confirm) or not old_value:
            value, errors = self.fromForm(field_name, fc, context, params)
            if errors or passwd != confirm:
                fc[field_name.inForm] = fc[confirm_name.inForm] = ''
                if not errors: # add error only if no other errors occured
                    errors = {field_name.inForm: self.mismatch_error}
            else:
                if self.digest:
                    value[field_name] = self.digest(
                                                value[field_name]).hexdigest()
            return fc, value, errors
        else:
            return fc, {field_name: old_value}, {}


class FixedList(Field):

    itemField = String()
    _bad_field_error = 'itemField must be scalar Field or '\
                                        'Agregate, not FieldGroup'
    length = 3

    def itemFieldName(self, field_name, index):
        return field_name.child('%s-%d' % (field_name, index),
                                branch=False)

    def getDefault(self, field_name, context, params):
        items = []
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({})
            item_value = self.itemField.getDefault(item_field_name, context,
                                                   params)
            items.append(item_value[item_field_name])
        return {field_name: items}

    def toForm(self, field_name, context, filter):
        items = context.value[field_name]
        assert len(items)==self.length
        form_content = {}
        for index, value in enumerate(items):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: value})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if new_filter.show is None:
                continue
            form_content.update(self.itemField.toForm(item_field_name,
                                                      new_context, new_filter))
        return form_content

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        items = []
        local_namespace = {'fieldName': field_name.inForm, 'fieldType': self,
                           'items': items, 'errors': errors, 'params': params}
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child(
                        {item_field_name: context.value[field_name][index]})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if new_filter.show is None:
                continue
            items.append(self.itemField.render(
                                item_field_name, form_content, errors,
                                requisites, new_context, new_filter, params,
                                template_selector, global_namespace))
        return local_namespace

    def fetch(self, form, field_name, context, params):
        raise RuntimeError

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError

    def accept(self, form, field_name, context, filter, params):
        form_content = {}
        items = context.value[field_name]
        errors = {}
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: items[index]})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if not new_filter.accept:
                continue
            item_form_content, item_field_value, item_field_errors = \
                        self.itemField.accept(form, item_field_name,
                                              new_context, new_filter, params)
            # subvalue can be left empty if error occured
            assert item_field_value.keys() in ([item_field_name], []), \
                                                self._bad_field_error
            if item_field_value.has_key(item_field_name):
                items[index] = item_field_value[item_field_name]
            errors.update(item_field_errors)
        return form_content, {field_name: items}, errors

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        Field.handleEvent(self, field_name, event, context, filter, actions,
                          params, template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        items = context.value[field_name]
        for index in xrange(self.length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: items[index]})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if not new_filter.event:
                continue
            self.itemField.handleEvent(item_field_name, event, new_context,
                                       new_filter, actions, params,
                                       template_selector, global_namespace)


class Container(Field):

    fieldGroup = FieldGroup(subfields=[])

    def getDefault(self, field_name, context, params):
        new_context = context.child({})
        new_name = field_name.child()
        return {field_name: self.fieldGroup.getDefault(new_name,
                                                       new_context, params)}

    def toForm(self, field_name, context, filter):
        new_context = context.child(context.value[field_name])
        new_name = field_name.child(None)
        new_filter = filter(self.fieldGroup, new_name, new_context)
        if new_filter.show is None:
            return {}
        return self.fieldGroup.toForm(new_name, new_context, new_filter)

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        # XXX Or just render them into content variable?
        new_name = field_name.child(None)
        new_context = context.child(context.value[field_name])
        new_filter = filter(self.fieldGroup, new_name, new_context)
        if new_filter.show is None:
            local_namespace = {'subfields': {}}
        else:
            local_namespace = self.fieldGroup.prepareNamespace(
                                new_name, form_content, errors,
                                requisites, new_context, new_filter, params,
                                template_selector, global_namespace)
        local_namespace.update({'fieldName': field_name.inForm,
                                'fieldType': self})
        return local_namespace

    def fetch(self, form, field_name, context, params):
        raise RuntimeError

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError

    def accept(self, form, field_name, context, filter, params):
        new_name = field_name.child(None)
        if not context.value.has_key(field_name):
            context.value.update(self.getDefault(field_name, context.child({}),
                                                 params))
        new_context = context.child(context.value[field_name])
        new_filter = filter(self.fieldGroup, new_name, new_context)
        if not new_filter.accept:
            return {}, {}, {}
        form_content, value, errors = self.fieldGroup.accept(
                            form, new_name, new_context, new_filter, params)
        return form_content, {field_name: value}, errors

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        Field.handleEvent(self, field_name, event, context, filter, actions,
                          params, template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        new_name = field_name.child(None)
        new_context = context.child(context.value[field_name])
        new_filter = filter(self.fieldGroup, new_name, new_context)
        if new_filter.event:
            self.fieldGroup.handleEvent(new_name, event, new_context,
                                        new_filter, actions, params,
                                        template_selector, global_namespace)


class EventGenerator:
    eapiName = "eapi"
    onloadTmpl = """Event.observe('%(field_name)s-control', '%(field_action)s', function () {%(eapi)s.sendEvent('%(event_name)s', %(values)s)});"""

    def __init__(self, eventName, eventAction='change', dependencies=[]):
        self.name = eventName
        self.action = eventAction
        self.deps = set(dependencies)

    def _sendEventValues(self, field_name):
        deps = set(self.deps)
        deps.add(field_name)
        return '[%s]' % ', '.join(
            ["%s.fields.extractValue('%s')" % (self.eapiName, i,) \
             for i in deps])


    def __call__(self, field_type, field_name, form_content, errors,
                 requisites, context, filter, params):
        r = requisites
        r['create_eventapi'] = True

        onload = r.setdefault('onload', [])
        onload.append(
            interpolateString(
                self.onloadTmpl,
                {'event_name': self.name,
                 'field_name': field_name.inForm,
                 'field_action': self.action,
                 'values': self._sendEventValues(field_name.inForm),
                 'eapi': self.eapiName})
            )
        logger.info(onload)


class AcceptEventHandler(EventHandler):

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        logger.debug('AcceptEventHandler for %s', field_name.inForm)
        if filter.accept:
            form_content, value, errors = field_type.accept(
                            event.form, field_name, context, filter, params)
        context.value.update(value)
        return []


def JSString(content):
    for src, targ in [('\\', '\\\\'), ('\n', '\\n'), ('"', '\\"')]:
        content = content.replace(src, targ)
    return '"%s"' % content


class SetDefaultEventHandler(EventHandler):

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        context.value.update(
                        field_type.getDefault(field_name, context, params))
        return []


class RenderEventHandler(EventHandler):

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        logger.debug('RenderEventHandler for %s', field_name.inForm)
        if filter.show is None:
            return []
        form_content = field_type.toForm(field_name, context, filter)
        requisites = {}
        content = field_type.render(field_name, form_content, {}, requisites,
                                    context, filter, params,
                                    template_selector, global_namespace)
        return ['Element.replace("%s-container", %s)' % (field_name,
                                                         JSString(content))]+\
               requisites.get('onload', [])


class Placeholder(Field):

    def getDefault(self, field_name, context, params):
        return {}

    def toForm(self, field_name, context, filter):
        return {}

    def fetch(self, form, field_name, context, params):
        raise RuntimeError

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError

    def accept(self, form, field_name, context, filter, params):
        return {}, {}, {}


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

    def getDefault(self, field_name, context, params):
        spec = self.optionSpec(context)
        return spec.getDefault(field_name, context, params)

    def toForm(self, field_name, context, filter):
        spec = self.optionSpec(context)
        new_filter = filter(spec, field_name, context)
        if new_filter.show is None:
            return {}
        return spec.toForm(field_name, context, new_filter)

    def fillRequisites(self, field_name, form_content, errors,
                       requisites, context, params):
        raise RuntimeError

    def render(self, field_name, form_content, errors, requisites,
               context, filter, params, template_selector, global_namespace):
        spec = self.optionSpec(context)
        new_filter = filter(spec, field_name, context)
        if new_filter.show is None:
            return '' # XXX
        return spec.render(field_name, form_content, errors,
                           requisites, context, new_filter, params,
                           template_selector, global_namespace)

    def fetch(self, form, field_name, context, params):
        raise RuntimeError

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError

    def accept(self, form, field_name, context, filter, params):
        spec = self.optionSpec(context)
        new_filter = filter(spec, field_name, context)
        if not new_filter.accept:
            return {}, {}, {}
        return spec.accept(form, field_name, context, new_filter, params)

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        Field.handleEvent(self, field_name, event, context, filter, actions,
                          params, template_selector, global_namespace)
        spec = self.optionSpec(context)
        new_filter = filter(spec, field_name, context)
        if new_filter.event:
            spec.handleEvent(field_name, event, context, new_filter, actions,
                             params, template_selector, global_namespace)


class File(Field):
    root = None # webroot
    converter = Converter()
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

    def accept(self, form, field_name, context, filter, params):
        import os.path

        sources = []
        fc = {}
        url_field_name = field_name.child(field_name+'-url', branch=False)
        servfile_field_name = field_name.child(field_name+'-sid', branch=False)
        filename_field_name = field_name.child(
            field_name+'-filename', branch=False)

        fc.update(self.fetch(form, url_field_name, context, params))
        fc[field_name.inForm] = context[field_name]
        fc[servfile_field_name.inForm] = '' # default values
        fc[filename_field_name.inForm] = ''

        if self.allowUpload:
            upload_field_name = field_name.child(field_name+'-upload',
                                                 branch=False)
            try:
                filename = form[upload_field_name.inForm].filename or ''
                remotefile = form[upload_field_name.inForm].file
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
                url = fc[url_field_name.inForm]
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
                return fc, {}, {field_name: str(why)}

        for remotename, file in sources:
            data = file.read()
            if not data:
                continue
            else:
                localname = self.nameGenerator()
                localpath = os.path.join(self.tempDir, localname)
                open(localpath, 'w').write(data)
                #fc[servfile_field_name.inForm] = localname
                fc[filename_field_name.inForm] = remotename
                return (fc,) + self.checkFile(
                    field_name, localpath, remotename, context, params)
        if self.allowNone:
            return fc, {}, {}
        else:
            return fc, {}, {field_name.inForm: self.noneFileError}

    def checkFile(self, field_name, path, name, context, params):
        """The only overridable method,
        path - path to temprorary file,
        name - client file name.

        Return touple of value and errors hashes"""

        value = self._File(tmpname=path, remotename=name)
        value, error = self.converter.fromForm(
            self, value, context, params)
        if error is None:
            return {field_name: value}, {}
        else:
            return {}, {field_name.inForm: error}


class Image(File):
    width = None
    height = None
    action = None # 'resize' or 'thumb'
    filter = "ANTIALIAS" # getattr(PIL.Image, filter)

    def checkFile(self, field_name, path, name, context, params):
        import PIL.Image, os
        try:
            image = PIL.Image.open(open(path))
        except IOError:
            from PPA.Template.Cook import quoteHTML
            return {}, {field_name.inForm: \
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
                return {}, {field_name.inForm: error}

        return {field_name: self._File(tmpname=path, remotename=name)}, {}

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


class VarListInsertEventHandler(AcceptEventHandler, RenderEventHandler):

    def __init__(self):
        pass

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        raise RuntimeError

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if event.id==field_name.inForm+'-insert':
            AcceptEventHandler.actions(self, field_type, field_name, event,
                                       context, filter, params,
                                       template_selector, global_namespace)
            value = context.value[field_name]
            try:
                index = int(event.form.getString(
                                            field_name.inForm+'-index', ''))
            except ValueError:
                index = len(value)
            item_field_name = field_type.itemFieldName(field_name, index)
            item_value = field_type.itemField.getDefault(item_field_name,
                                                         context, params)
            value.insert(index, item_value[item_field_name])
            actions.extend(
                RenderEventHandler.actions(
                                        self, field_type, field_name, event,
                                        context, filter, params,
                                        template_selector, global_namespace))


class VarListDeleteEventHandler(AcceptEventHandler, RenderEventHandler):

    def __init__(self):
        pass

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        raise RuntimeError

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if event.id.startswith(field_name.inForm+'-delete'):
            AcceptEventHandler.actions(self, field_type, field_name, event,
                                       context, filter, params,
                                       template_selector, global_namespace)
            value = context.value[field_name]
            try:
                index = int(event.form.getString(
                                            field_name.inForm+'-index', ''))
            except ValueError:
                # clear all
                del value[:]
            else:
                try:
                    del context.value[field_name][index]
                except IndexError:
                    return
            actions.extend(
                RenderEventHandler.actions(
                                        self, field_type, field_name, event,
                                        context, filter, params,
                                        template_selector, global_namespace))


class VarListInsertEventGenerator(EventGenerator):

    action = 'click'
    onloadTmpl = """Event.observe('%(node_id)s', '%(field_action)s', function () {%(eapi)s.sendEvent('%(event_name)s', %(values)s)});"""
    deps = []

    def __init__(self):
        pass

    def __call__(self, field_type, field_name, form_content, errors,
                 requisites, context, filter, params):
        r = requisites
        r['create_eventapi'] = True

        onload = r.setdefault('onload', [])
        if field_type.allowAppend:
            onload.append(
                interpolateString(
                    self.onloadTmpl,
                    {'node_id': field_name.inForm+'-insert',
                     'event_name': field_name.inForm+'-insert',
                     'field_name': field_name.inForm,
                     'field_action': self.action,
                     'values': self._sendEventValues(field_name.inForm),
                     'eapi': self.eapiName})
                )
        if field_type.allowDeleteAll:
            onload.append(
                interpolateString(
                    self.onloadTmpl,
                    {'node_id': field_name.inForm+'-delete',
                     'event_name': field_name.inForm+'-delete',
                     'field_name': field_name.inForm,
                     'field_action': self.action,
                     'values': self._sendEventValues(field_name.inForm),
                     'eapi': self.eapiName})
                )
        length = form_content[field_type.lengthFieldName(field_name).inForm]
        for index in xrange(length):
            if field_type.allowInsert:
                onload.append(
                    interpolateString(
                        self.onloadTmpl,
                        {'node_id': field_name.inForm+'-insert-%s' % index,
                         'event_name': field_name.inForm+'-insert',
                         'field_name': field_name.inForm,
                         'field_action': self.action,
                         'values': '["%s-index=%s", ' % (field_name.inForm, index) + self._sendEventValues(field_name.inForm)[1:],
                         'eapi': self.eapiName})
                    )
            if field_type.allowDelete:
                onload.append(
                    interpolateString(
                        self.onloadTmpl,
                        {'node_id': field_name.inForm+'-delete-%s' % index,
                         'event_name': field_name.inForm+'-delete',
                         'field_name': field_name.inForm,
                         'field_action': self.action,
                         'values': '["%s-index=%s", ' % (field_name.inForm, index) + self._sendEventValues(field_name.inForm)[1:],
                         'eapi': self.eapiName})
                    )
        logger.info(onload)


class VarList(Field):


    itemField = String()
    _bad_field_error = 'itemField must be scalar Field or '\
                                        'Agregate, not FieldGroup'

    eventHandlers = [VarListInsertEventHandler(), VarListDeleteEventHandler()]
    requisitesFillers = [VarListInsertEventGenerator()]

    # Tuning event generator
    allowDeleteAll = True
    allowDelete = True
    allowInsert = True
    allowAppend = True

    def itemFieldName(self, field_name, index):
        return field_name.child('%s-%d' % (field_name, index),
                                branch=False)
    def lengthFieldName(self, field_name):
        return field_name.child('%s-length' % field_name, branch=False)

    def getDefault(self, field_name, context, params):
        return {field_name: []}

    def toForm(self, field_name, context, filter):
        items = context.value[field_name]
        form_content = {self.lengthFieldName(field_name).inForm: len(items)}
        for index, value in enumerate(items):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: value})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if new_filter.show is None:
                continue
            form_content.update(self.itemField.toForm(item_field_name,
                                                      new_context, new_filter))
        return form_content

    def prepareNamespace(self, field_name, form_content, errors,
                         requisites, context, filter, params,
                         template_selector, global_namespace={}):
        items = []
        local_namespace = {'fieldName': field_name.inForm, 'fieldType': self,
                           'items': items, 'errors': errors, 'params': params}
        length = form_content[self.lengthFieldName(field_name).inForm]
        for index in xrange(length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child(
                        {item_field_name: context.value[field_name][index]})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if new_filter.show is None:
                continue
            items.append(self.itemField.render(
                                item_field_name, form_content, errors,
                                requisites, new_context, new_filter, params,
                                template_selector, global_namespace))
        return local_namespace

    def fetch(self, form, field_name, context, params):
        raise RuntimeError

    def fromForm(self, field_name, form_content, context, params):
        raise RuntimeError

    def accept(self, form, field_name, context, filter, params):
        length_field_name = self.lengthFieldName(field_name)
        try:
            length = int(form.getString(length_field_name.inForm, ''))
        except ValueError:
            length = 0
        form_content = {length_field_name.inForm: length}
        items = context.value[field_name][:length]
        while len(items)<length:
            item_field_name = self.itemFieldName(field_name, len(items))
            item_value = self.itemField.getDefault(item_field_name,
                                                   context.child({}), params)
            items.append(item_value[item_field_name])
        errors = {}
        for index in xrange(length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: items[index]})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if not new_filter.accept:
                continue
            item_form_content, item_field_value, item_field_errors = \
                        self.itemField.accept(form, item_field_name,
                                              new_context, new_filter, params)
            # subvalue can be left empty if error occured
            assert item_field_value.keys() in ([item_field_name], []), \
                                                self._bad_field_error
            if item_field_value.has_key(item_field_name):
                items[index] = item_field_value[item_field_name]
            errors.update(item_field_errors)
        return form_content, {field_name: items}, errors

    def handleEvent(self, field_name, event, context, filter, actions, params,
                    template_selector, global_namespace):
        Field.handleEvent(self, field_name, event, context, filter, actions,
                          params, template_selector, global_namespace)
        # propogate event to subfields
        # XXX should this be done before or after calling own handlers?
        items = context.value[field_name]
        for index, item in enumerate(items):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.child({item_field_name: item})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if not new_filter.event:
                continue
            self.itemField.handleEvent(item_field_name, event, new_context,
                                       new_filter, actions, params,
                                       template_selector, global_namespace)

