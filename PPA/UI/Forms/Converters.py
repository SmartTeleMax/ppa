
from Base import Converter


class Chain(Converter):
    chain = []

    def __init__(self, *args, **kwargs):
        self.chain = args
        Converter.__init__(self, **kwargs)
    
    def fromForm(self, field_type, value, context, view):
        for converter in self.chain:
            value, error = converter.fromForm(field_type, value, context, view)
            if error is not None:
                return None, error
        return value, None

    def toForm(self, field_type, value):
        for converter in self.chain:
            value = converter.toForm(field_type, value)
        return value



class Length(Converter):

    min = 0
    max = 255
    error = 'Length error'
    
    def fromForm(self, field_type, value, context, view):
        if self.min<=len(value)<=self.max:
            return value, None
        else:
            return None, self.error


class Pattern(Converter):
    pattern = None
    error = "String doesn't match pattern"

    def fromForm(self, field_type, value, context, view):
        if self.pattern:
            import re
            if not re.match(self.pattern, value):
                return None, self.error
        return value, None


class Number(Converter):

    type = None
    minValue = None
    maxValue = None
    rangeError = 'XXX Range error'

    def __init__(self, type, **kwargs):
        self.type = type
        Converter.__init__(self, **kwargs)

    def toForm(self, field_type, value):
        if value is None:
            return ''
        return str(value)

    def fromForm(self, field_type, value, context, view):
        if not value and field_type.allowNone:
            return None, None
        try:
            value = self.type(value)
        except ValueError, exc:
            return None, str(exc)
        else:
            if (self.minValue is None or self.minValue<=value) and \
                    (self.maxValue is None or value<=self.maxValue):
                return value, None
            else:
                return None, self.rangeError


try:
    import stripogram
except ImportError:
    _strip_tags = lambda a: a
else:
    class StripogramFilter(stripogram.HTML2SafeHTML):
        can_close   = ['li', 'p', 'dd', 'dt', 'option']
        CDATA_CONTENT_ELEMENTS = []

    def html2safehtml(string, valid_tags=[]):
        valid_tags = [t.lower() for t in valid_tags]
        parser = StripogramFilter(valid_tags)
        parser.feed(string)
        parser.close()
        parser.cleanup()
        return parser.result
    _strip_tags = html2safehtml


class StripTags(Converter):
    allowedTags = []

    def fromForm(self, field_type, value, context, view):
        return _strip_tags(value, self.allowedTags), None
