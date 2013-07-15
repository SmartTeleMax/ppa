
import Fields
from PPA.Template.Cook import quoteHTML

class HTMLElementAttributes(object):
    """Represents html element attributes, __set__ accepts dictionary,
    __get__ returns formatted string"""

    def __set__(self, inst, value):
        if type(value) is not dict:
            raise ValueError('elementAttributes must be dict')
        inst._elementAttributes = value

    def __get__(self, inst, cls):
        value = getattr(inst, '_elementAttributes', {})
        return ' '.join(
            ['%s="%s"' % (k,quoteHTML(unicode(v))) for (k,v) in value.items()])


class HTMLElement:
    """Base class for all html elements"""

    elementAttributes = HTMLElementAttributes()


class InputText(Fields.String, HTMLElement):
    pass


class TextArea(Fields.String, HTMLElement):
    pass


class InputPassword(Fields.String, HTMLElement):
    pass
