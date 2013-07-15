# $Id: Cook.py,v 1.6 2007/06/29 05:43:49 ods Exp $

from __future__ import generators
import re


def quoteHTML(text, nl2br=0, pre=0):
    for char, repl in [('&', '&amp;'),
                       ('"', '&quot;'),
                       ('<', '&lt;'),
                       ('>', '&gt;')]:
        text = text.replace(char, repl)
    if nl2br or pre:
        if type(nl2br) not in (str, unicode):
            nl2br = '<br>'
        text = text.replace('\n', nl2br)
        if pre:
            text = text.replace('\t', ' '*8).replace('  ', '&nbsp; ')
            text = '<tt>%s</tt>' % text
    return text


def quoteURLPath(text):
    return re.sub(r"[^\w\d_.!~*'()/+-]",
                  lambda m: '%%%02X' % ord(m.group()), text)


def quoteFormField(text):
    text = re.sub(r"[^\w\d_.!~*'() -]",
                  lambda m: '%%%02X' % ord(m.group()), text)
    return text.replace(' ', '+')


def quoteJS(text):
    text = text.replace('\r\n', '\\n');
    text = text.replace('\n', '\\n');
    for char in '\'"<>&':
        text = text.replace(char, '\\x%2x' % ord(char))
    return text


class Repeat:

    class _Item:
        def __init__(self, value, index, has_next):
            self.value = value
            self.index = index
            self.isLast = not has_next
            self.isFirst = not index
        def isOdd(self):
            return self.index % 2
        isOdd = property(isOdd)
        def isEven(self):
            return not self.index % 2
        isEven = property(isEven)
        def alter(self, *args):
            return args[self.index % len(args)]

    def __init__(self, sequence):
        self._iter = iter(sequence)

    def _shift(self):
        try:
            self._next = self._iter.next()
        except StopIteration:
            self._has_next = 0
        else:
            self._has_next = 1

    def __iter__(self):
        self._shift()
        index = 0
        while self._has_next:
            value = self._next
            self._shift()
            yield self._Item(value, index, self._has_next)
            index += 1


def pare(string, size, etc='...'):
    '''Pare string to have maximum size and add etc to the end if it's
    changed'''
    size = int(size)
    string = string.strip()
    if len(string)>size:
        string = string[:size]
        half = size//2
        last = None
        import re
        whitespace = re.compile('\s+')
        for mo in whitespace.finditer(string[half:]):
            if mo is not None:
                last = mo
        if last is not None:
            string = string[:half+last.start()+1]
        return string+etc
    else:
        return string
