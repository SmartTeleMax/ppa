# $Id$

from weakref import WeakKeyDictionary
from Errors import ClientError


class Form(object):

    maxContentLength = 1048576
    requireContentLength = 1
    
    __cache = WeakKeyDictionary()
    
    def __new__(cls, request):
        if not cls.__cache.has_key(request):
            cls.__cache[request] = self = object.__new__(cls, request)
            self._init(request)
        return cls.__cache[request]

    def _init(self, request):
        method = request.method()
        if method in ('GET', 'HEAD'):
            self.parseURLEncoded(request.query())
        elif method=='POST':
            content_type = request.headers.get(
                        'Content-Type', 'application/x-www-form-urlencoded')
            try:
                content_length = request.headers['Content-Length']
            except KeyError:
                if self.requireContentLength:
                    raise ClientError(411, '')
                else:
                    content_length = self.maxContentLength
            else:
                if content_length>self.maxContentLength:
                    raise ClientError(413, '')
            if content_type=='application/x-www-form-urlencoded':
                # XXX Silently stripping large body is a bad thing.
                # Should try reading maxContentLength+1 byte to check!
                self.parseURLEncoded(request.read(content_length))
            elif content_type=='multipart/form-data':
                self.parseMultipart(request)
