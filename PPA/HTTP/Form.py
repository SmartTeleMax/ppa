# $Id: Form.py,v 1.5 2007/03/23 11:25:58 ods Exp $

import sys, re
from weakref import WeakKeyDictionary

# http://www.w3.org/TR/REC-xml#NT-Char
# Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | 
#          [#x10000- #x10FFFF]
# (any Unicode character, excluding the surrogate blocks, FFFE, and FFFF)
subNonChar = re.compile(
            ur'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]',
            re.U).sub


class Form(object):

    __cache = WeakKeyDictionary()

    def __new__(cls, request, charset='utf-8', errors='replace'):
        try:
            field_storage = cls.__cache[request]
        except KeyError:
            import cgi
            env = {'QUERY_STRING'   : request.query(),
                   'REQUEST_METHOD' : request.method()}
            hs = request.headers
            if hs.has_key('content-type'):
                env['CONTENT_TYPE'] = hs['content-type']
            if hs.has_key('content-length'):
                env['CONTENT_LENGTH'] = hs['content-length']
            cls.__cache[request] = field_storage = \
                                    cgi.FieldStorage(fp=request, environ=env)
        self = object.__new__(cls)
        self._charset = charset
        self._errors = errors
        if errors=='strict':
            def replacement(m):
                raise ValueError('Invalid character %r in text' % m.group())
        elif errors=='replace':
            replacement = u'\uFFFD'
        else: # ignore
            replacement = ''
        self._replacement = replacement
        self._field_storage = field_storage

    def _decode(self, value):
        return subNonChar(self._replacement,
                          value.decode(self._charset, self._errors))
        
    def getString(self, key, default=None):
        '''Like of getfirst, returning unicode object'''
        value = self.getfirst(key)
        if value is None:
            return default
        return self._decode(value)

    def getStringList(self, key):
        '''Like getlist, returning unicode objects'''
        return [self._decode(item) for item in self.getlist(key)]

    def __getattr__(self, name):
        return getattr(self._field_storage, name)


# XXX Unfinished own implementation
#
#from weakref import WeakKeyDictionary
#from Errors import ClientError
#import urllib
#
#
#class Form(object):
#
#    maxContentLength = 1048576
#    requireContentLength = 1
#    keepBlankValues = 0
#    charset = None
#    charsetErrors = 'replace'
#    
#    __cache = WeakKeyDictionary()
#    
#    def __new__(cls, request):
#        if not cls.__cache.has_key(request):
#            cls.__cache[request] = self = object.__new__(cls)
#            self._init(request)
#        return cls.__cache[request]
#
#    def _init(self, request):
#        self._dict = {}
#        method = request.method()
#        if method in ('GET', 'HEAD'):
#            self.parseURLEncodedString(request.query())
#        elif method=='POST':
#            # XXX Header may contain parameters, parse it.
#            # XXX Add method to Headers class returning value and dictionary of
#            # parameters?
#            content_type = request.headers['Content-Type'] or \
#                                'application/x-www-form-urlencoded'
#            try:
#                content_length = int(request.headers['Content-Length'])
#            except (KeyError, ValueError):
#                content_length = None
#            else:
#                if content_length>self.maxContentLength:
#                    raise ClientError(413, '')
#            if content_length is None and self.requireContentLength:
#                raise ClientError(411, '')
#            if content_type=='application/x-www-form-urlencoded':
#                self.parseURLEncoded(request, content_length)
#            elif content_type=='multipart/form-data':
#                # XXX Use boundary parameter from header.
#                self.parseMultipart(request, content_length)
#    
#    def parseURLEncoded(self, request, content_length=None):
#        if content_length is None:
#            body = request.read(self.maxContentLength+1)
#            if len(body)>self.maxContentLength:
#                raise ClientError(413, '')
#        else:
#            body = request.read(content_length)
#        self.parseURLEncodedString(body)
#
#    def parseURLEncodedString(self, body):
#        pairs = [(ps.split('=', 1)+[''])[:2] for ps0 in body.split(';')
#                                              for ps in ps0.split('&')]
#        unquote = urllib.unquote_plus
#        setdefault = self._dict.setdefault
#        for qfn, qfv in pairs:
#            if qfv or self.keepBlankValues:
#                setdefault(unquote(qfn), []).append(unquote(qfv))
#
#    def _decode(self, value):
#        if self.charset is not None:
#            return value.decode(self.charset, self.charsetErrors)
#        else:
#            return value
#
#    def getString(self, name, default=''):
#        return self._decode(self._dict.get(name, [default])[0])
#
#    def getStringList(self, name):
#        return [self._decode(value) for value in self._dict.get(name, [])]


