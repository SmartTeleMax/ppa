# $Id: VarList.py,v 1.1 2007/05/16 14:10:58 ods Exp $
# XXX The module is not adapted to the new interface yet

from Fields import Field, String
from Events import EventHandler, EventGenerator, AcceptEventHandler, \
                   RenderEventHandler


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
                                        'Agregate, not Schema'

    eventHandlers = [VarListInsertEventHandler(), VarListDeleteEventHandler()]
    requisitesFillers = [VarListInsertEventGenerator()]

    # Tuning event generator
    allowDeleteAll = True
    allowDelete = True
    allowInsert = True
    allowAppend = True

    def itemFieldName(self, field_name, index):
        return '%s-%d' % (field_name, index)

    def lengthFieldName(self, field_name):
        return '%s-length' % field_name

    def getDefault(self, field_name, context, params):
        return {field_name: []}

    def toForm(self, state, context):
        items = context.scalar
        length_context = context.entry(self.lengthFieldName(context.name))
        form_content = {length_context.nameInForm: len(items)}
        for index, value in enumerate(items):
            item_field_name = self.itemFieldName(context.name, index)
            item_context = context.entry(item_field_name,
                                         {item_field_name: value})
            # XXX new_filter = filter(self.itemField, item_field_name, item_context)
            #if new_filter.show is None:
            #    continue
            form_content.update(self.itemField.toForm(state, item_context))
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
            new_context = context.branch(
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
                                                   context.branch(), params)
            items.append(item_value[item_field_name])
        errors = {}
        for index in xrange(length):
            item_field_name = self.itemFieldName(field_name, index)
            new_context = context.branch({item_field_name: items[index]})
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
            new_context = context.branch({item_field_name: item})
            new_filter = filter(self.itemField, item_field_name, new_context)
            if not new_filter.event:
                continue
            self.itemField.handleEvent(item_field_name, event, new_context,
                                       new_filter, actions, params,
                                       template_selector, global_namespace)

# vim: set sts=4 sw=4 ai et:
