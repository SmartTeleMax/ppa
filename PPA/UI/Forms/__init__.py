from FieldTypes import *
from PPA.Utils import interpolateString
import logging
logger = logging.getLogger(__name__)


class QPSItemConverter(Converter):

    def getStream(self, field_type, context, params):
        stream_id = interpolateString(field_type.streamTemplate,
                                      {'context': context})
        return params['site'].retrieveStream(stream_id)

    def fromForm(self, field_type, value, context, view):
        if not value and field_type.allowNone:
            return None, None
        stream = self.getStream(field_type, context, view)
        try:
            item_id = stream.fields.id.convertFromString(value, None)
            item = stream.retrieveItem(item_id)
        except Exception, exc:
            return None, str(exc)
        return item, None

    def toForm(self, field_type, value):
        if value is None:
            return ''
        return value.fields.id.convertToString(value.id, value)
        

class QPSItemReference(ScalarField):
    
    allowNone = True
    default = None
    streamTemplate = None
    converter = QPSItemConverter()


class QPSStreamOptions:

    def getStream(self, field_type, context, params):
        stream_id = interpolateString(field_type.streamTemplate,
                                      {'context': context})
        return params['site'].retrieveStream(stream_id)

    def __call__(self, field_type, context, view):
        for dependency in field_type.dependencies:
            if context[dependency] is None:
                return
        stream = self.getStream(field_type, context, view)
        for item in stream:
            title = interpolateString(field_type.labelTemplate,
                                      {'item': item})
            yield item, title


class QPSItemChoice(Choice):

    allowNone = True
    default = None
    dependencies = []
    streamTemplate = None
    labelTemplate = '%(getattr(item, "title", item.id))s'
    converter = QPSItemConverter()
    optionsRetriever = QPSStreamOptions()
    noneSelectedError = 'No item selected'

    def fromForm(self, field_name, form_content, context, params):
        value, error = self.converter.fromForm(
                        self, form_content[field_name.inForm], context, params)
        if value is None and not self.allowNone:
            return {}, {field_name.inForm: self.noneSelectedError}
        return {field_name: value}, {}


class QPSItemMultipleChoice(MultipleChoice):

    allowNone = True
    default = None
    dependencies = []
    streamTemplate = None
    labelTemplate = '%(getattr(item, "title", item.id))s'
    converter = QPSItemConverter()
    optionsRetriever = QPSStreamOptions()


class EditShowEventHandler(RenderEventHandler):

    def __init__(self):
        pass

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        logger.debug('%r ?= %r', event.id, field_name.inForm+'-editShow')
        if event.id!=field_name.inForm+'-editShow':
            return
        actions.extend(RenderEventHandler.actions(
                                self, field_type.editSpec, field_name, event,
                                context, filter, params,
                                template_selector, global_namespace))


class EditAcceptEventHandler(AcceptEventHandler, RenderEventHandler):

    suffix = 'editAccept'

    def __init__(self):
        pass

    def store(self, field_name, context, params):
        # XXX Redefine to use callback from params
        logger.info('EditAcceptEventHandler.store(%r, Context(%r, ...), %r)',
                    field_name, context.value, params)

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if event.id!=field_name.inForm+'-'+self.suffix:
            return
        actions.extend(AcceptEventHandler.actions(
                                self, field_type.editSpec, field_name, event,
                                context, filter, params,
                                template_selector, global_namespace))
        self.store(field_name, context, params)
        actions.extend(RenderEventHandler.actions(
                                self, field_type, field_name, event,
                                context, filter, params,
                                template_selector, global_namespace))


class ViewEditSwitchEventGenerator(EventGenerator):

    action = 'click'
    nodeIdTmpl = '%(field_name)s-%(suffix)s'
    eventNameTmpl = '%(field_name)s-%(suffix)s'
    onloadTmpl = """Event.observe('%(node_id)s', '%(field_action)s', function () {%(eapi)s.sendEvent('%(event_name)s', %(values)s)});"""
    deps = []

    def __init__(self, suffix, dependencies=[]):
        self.suffix = suffix
        self.deps = dependencies

    def __call__(self, field_type, field_name, form_content, errors,
                 requisites, context, filter, params):
        r = requisites
        r['create_eventapi'] = True
        onload = r.setdefault('onload', [])
        params = {'suffix': self.suffix,
                  'field_name': field_name.inForm,
                  'field_action': self.action,
                  'values': self._sendEventValues(field_name.inForm),
                  'eapi': self.eapiName}
        params['node_id'] = interpolateString(self.nodeIdTmpl, params)
        params['event_name'] = interpolateString(self.eventNameTmpl, params)
        onload.append(interpolateString(self.onloadTmpl, params))


class MaskAcceptEventHandler(AcceptEventHandler):

    def __init__(self, mask):
        import re
        self._match = re.compile(mask).match

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if self._match(event.id):
            actions.extend(self.actions(field_type, field_name, event,
                                        context, filter, params,
                                        template_selector, global_namespace))


class ItemToVarListEventHandler(AcceptEventHandler, RenderEventHandler):

    def __init__(self, suffix, paramName):
        self.suffix = suffix
        self.paramName = paramName

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        raise RuntimeError

    def __call__(self, field_type, field_name, event, context, filter, actions,
                 params, template_selector, global_namespace):
        if event.id.startswith(field_name.inForm+'-'+self.suffix):
            AcceptEventHandler.actions(self, field_type, field_name, event,
                                       context, filter, params,
                                       template_selector, global_namespace)
            try:
                index = int(event.form.getString(
                                            field_name.inForm+'-index', ''))
            except ValueError:
                import traceback
                logger.error(traceback.format_exc())
                return
            else:
                try:
                    #del context.value[field_name][index]
                    callback = params[self.paramName]
                    new_actions = callback(field_name, index, context)
                    if new_actions:
                        actions.extend(new_actions)
                except IndexError:
                    return
            actions.extend(RenderEventHandler.actions(
                                        self, field_type, field_name, event,
                                        context, filter, params,
                                        template_selector, global_namespace))


class ItemToVarListEventGenerator(EventGenerator):

    action = 'click'
    onloadTmpl = """Event.observe('%(node_id)s', '%(field_action)s', function () {%(eapi)s.sendEvent('%(event_name)s', %(values)s)});"""

    def __init__(self, suffix, dependencies=()):
        self.suffix = suffix
        self.deps = dependencies

    def __call__(self, field_type, field_name, form_content, errors,
                 requisites, context, filter, params):
        r = requisites
        r['create_eventapi'] = True

        onload = r.setdefault('onload', [])
        length = form_content[field_type.lengthFieldName(field_name).inForm]
        for index in xrange(length):
            onload.append(
                interpolateString(
                    self.onloadTmpl,
                    {'node_id': field_name.inForm+'-%s-%s' % 
                                                        (self.suffix, index),
                     'event_name': field_name.inForm+'-%s' % self.suffix,
                     'field_name': field_name.inForm,
                     'field_action': self.action,
                     'values': '["%s-index=%s", ' % (field_name.inForm, index) + self._sendEventValues(field_name.inForm)[1:],
                     'eapi': self.eapiName})
                )
        logger.info(onload)
