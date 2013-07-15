
def JSString(content):
    for src, targ in [('\\', '\\\\'), ('\n', '\\n'), ('"', '\\"')]:
        content = content.replace(src, targ)
    return '"%s"' % content


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


class AcceptEventHandler(EventHandler):

    def actions(self, field_type, field_name, event, context, filter, params,
                template_selector, global_namespace):
        logger.debug('AcceptEventHandler for %s', field_name.inForm)
        if filter.accept:
            form_content, value, errors = field_type.accept(
                            event.form, field_name, context, filter, params)
        context.value.update(value)
        return []

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
