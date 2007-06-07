
import Fields

class HTMLElementAttributes(object):
    """Represents html element attributes, __set__ accepts dictionary,
    __get__ returns formatted string"""
    
    def __set__(self, inst, value):
        if type(value) is not dict:
            raise ValueError('elementAttributes must be dict')
        self.value = value

    def __get__(self, inst, cls):
        return ' '.join(
            ['%s="%s"' % (key, value) for (key, value) in self.value.items()])


class HTMLElement:
    """Base class for all html elements"""
    
    elementAttributes = HTMLElementAttributes()


class InputText(Fields.String, HTMLElement):
    pass


class TextArea(Fields.String, HTMLElement):
    pass


class InputPassword(Fields.String, HTMLElement):
    pass
