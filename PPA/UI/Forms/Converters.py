
class Converter:

    """Base Converter class, all children must implement
    fromForm and toForm methods"""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def fromForm(self, context, value):
        """Returns value, None if convertation was successful, or None, error
        if there was error"""
        
        return value, None

    def toForm(self, context, value):
        """Returns value converted for form"""
        
        return value

    
class Chain(Converter):
    """Chain converter, accepts converters as arguments and chains thru them.

    Example:

    Chain(NotNull(), String())

    fromForm chains in direct order,
    toForm in reverse order"""
    
    chain = []

    def __init__(self, *args, **kwargs):
        self.chain = args
        Converter.__init__(self, **kwargs)
    
    def fromForm(self, context, value):
        for converter in self.chain:
            value, error = converter.fromForm(context, value)
            if error is not None:
                return None, error
        return value, None

    def toForm(self, context, value):
        for converter in reversed(self.chain):
            value = converter.toForm(context, value)
        return value



class Length(Converter):
    """Controls length on string. Params are:

    min - minimal required length (default 0)
    max - maximal required length (default 255)
    error - message to raise on length mismatch"""

    min = 0
    max = 255
    error = 'Length error'
    
    def fromForm(self, context, value):
        if self.min<=len(value)<=self.max:
            return value, None
        else:
            return None, self.error


class NotNull(Converter):
    """Controls if bool(value) is True. Params are:

    error - message to raise if value is false"""

    error = 'This field cant be empty'
    
    def fromForm(self, context, value):
        if value:
            return value, None
        else:
            return None, self.error


class Strip(Converter):
    """Returns stripped string, no errors are raised"""
    
    def fromForm(self, context, value):
        return value.strip(), None


class Pattern(Converter):
    """Checks string against a given pattern.

    pattern - regexp pattern used to check a string
    error - error raised if string doesn't match pattern"""
    
    pattern = None
    error = "String doesn't match pattern"

    def fromForm(self, context, value):
        if self.pattern:
            import re
            if not re.match(self.pattern, value):
                return None, self.error
        return value, None

#mandatoryEmailPattern = "^.+\@.+$"
#emailPattern = "(%s)|(^$)" % mandatoryEmailPattern
#urlPattern = '(^(http|ftp)://[a-zA-Z0-9\.\?&%=/_;+-]*$|^$)|(^$)'
#mandatoryUrlPattern = '^(http|ftp)://[a-zA-Z0-9\.\?&%=/_;+-]*$'


class Email(Pattern):
    """Subclass of Pattern, checks if string is a valid email address"""
    
    pattern = "^.+\@.+$"
    error = "This is not email"


class Url(Pattern):
    """Subclass of Pattern, checks if string is a valid url address"""

    pattern = '^(http|ftp)://[a-zA-Z0-9\.\?&%=/_;+-]*$'
    error = "This is not url"


class Number(Converter):

    """Converts string into numeric python type. Params are:

    type - python type (int for example)
    minValue - minimal border of converted value
    maxValue - maximum border of converted value
    rangeError - error raised if value is not in a given range.

    If ValueError (while type(value)) occures - it's raised"""

    type = None
    minValue = None
    maxValue = None
    rangeError = 'XXX Range error'

    def __init__(self, type, **kwargs):
        self.type = type
        Converter.__init__(self, **kwargs)

    def toForm(self, context, value):
        if value is None:
            return ''
        return str(value)

    def fromForm(self, context, value):
        if not value and context.fieldType.allowNone:
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

    def fromForm(self, context, value):
        return _strip_tags(value, self.allowedTags), None
