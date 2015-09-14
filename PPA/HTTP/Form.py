# $Id: Form.py,v 1.4 2006/06/09 10:16:26 ods Exp $

from weakref import WeakKeyDictionary
from Errors import ClientError
import urllib


class Form(object):

    maxContentLength = 1048576
    requireContentLength = 1
    keepBlankValues = 0
    charset = None
    charsetErrors = 'replace'
    
    __cache = WeakKeyDictionary()
    
    def __new__(cls, request):
        if not cls.__cache.has_key(request):
            cls.__cache[request] = self = object.__new__(cls)
            self._init(request)
        return cls.__cache[request]

    def _init(self, request):
        self._dict = {}
        method = request.method()
        if method in ('GET', 'HEAD'):
            self.parseURLEncodedString(request.query())
        elif method=='POST':
            # XXX Header may contain parameters, parse it.
            # XXX Add method to Headers class returning value and dictionary of
            # parameters?
            content_type = request.headers['Content-Type'] or \
                                'application/x-www-form-urlencoded'
            try:
                content_length = int(request.headers['Content-Length'])
            except (KeyError, ValueError):
                content_length = None
            else:
                if content_length>self.maxContentLength:
                    raise ClientError(413, '')
            if content_length is None and self.requireContentLength:
                raise ClientError(411, '')
            if content_type=='application/x-www-form-urlencoded':
                self.parseURLEncoded(request, content_length)
            elif content_type=='multipart/form-data':
                # XXX Use boundary parameter from header.
                self.parseMultipart(request, content_length)
    
    def parseURLEncoded(self, request, content_length=None):
        if content_length is None:
            body = request.read(self.maxContentLength+1)
            if len(body)>self.maxContentLength:
                raise ClientError(413, '')
        else:
            body = request.read(content_length)
        self.parseURLEncodedString(body)

    def parseURLEncodedString(self, body):
        pairs = [(ps.split('=', 1)+[''])[:2] for ps0 in body.split(';')
                                              for ps in ps0.split('&')]
        unquote = urllib.unquote_plus
        setdefault = self._dict.setdefault
        for qfn, qfv in pairs:
            if qfv or self.keepBlankValues:
                setdefault(unquote(qfn), []).append(unquote(qfv))

    def _decode(self, value):
        if self.charset is not None:
            return value.decode(self.charset, self.charsetErrors)
        else:
            return value

    def getString(self, name, default=''):
        return self._decode(self._dict.get(name, [default])[0])

    def getStringList(self, name):
        return [self._decode(value) for value in self._dict.get(name, [])]
