
# XXX not tested, need some imoports

class QPSItemConverter(Converter):

    def getStream(self, field_type, context, view):
        stream_id = interpolateString(field_type.streamTemplate,
                                      {'context': context})
        return view.site.retrieveStream(stream_id)

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

    def getStream(self, field_type, context, view):
        stream_id = interpolateString(field_type.streamTemplate,
                                      {'context': context})
        return view.site.retrieveStream(stream_id)

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


class QPSItemMultipleChoice(MultipleChoice):

    allowNone = True
    default = None
    dependencies = []
    streamTemplate = None
    labelTemplate = '%(getattr(item, "title", item.id))s'
    converter = QPSItemConverter()
    optionsRetriever = QPSStreamOptions()
