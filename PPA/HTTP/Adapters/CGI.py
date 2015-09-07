import Base

class Headers:
    '''Read-only input headers wrapper to envirinment variables HTTP_*.'''
    _raw_headers = ('CONTENT_LENGTH', 'CONTENT_TYPE')

    def __init__(self, environ=None):
        if environ is None:
            from os import environ
        self._environ = environ

    def _environ_name(self, key):
        key = key.replace('-', '_').upper()
        if key in self._raw_headers:
            return key
        else:
            return 'HTTP_'+key

    def keys(self):
        environ = self._environ
        res = []
        for name in self._raw_headers:
            if environ.has_key(name):
                res.append(name.replace('_', '-').lower())
        for name in environ:
            if name.startswith('HTTP_'):
                res.append(name[5:].replace('_', '-').lower())
        return res

    def has_key(self, key):
        return self._environ.has_key(self._environ_name(key))

    def __getitem__(self, key):
        return self._environ.get(self._environ_name(key))


class Request(Base.Request):

    def __init__(self, environ, stdin):
        self._environ = environ
        Base.Request.__init__(self, Headers(environ), stdin,
                              environ.get('PATH_INFO', ''))

    def protocol(self):
        return self._environ['SERVER_PROTOCOL']

    def method(self):
        return self._environ['REQUEST_METHOD'].upper()

    def uri(self):
        if self._environ.has_key('REQUEST_URI'):
            # This variable is not part of CGI/1.1 standard (available in
            # apache)
            return self._environ['REQUEST_URI']
        else:
            query = self.query()
            if query:
                return self.path()+'?'+query
            else:
                return self.path()

    def serverAddr(self):
        return self._environ['SERVER_ADDR']

    def serverName(self):
        return self._environ['SERVER_NAME']

    def serverPort(self):
        return int(self._environ['SERVER_PORT'])

    def remoteAddr(self):
        return self._environ['REMOTE_ADDR']

    def remoteName(self):
        if self._environ.has_key('REMOTE_HOST'):
            return self._environ['REMOTE_HOST']
        #elif explicitly lookup is allowed we can do it
        else:
            return self.remoteAddr()

    def user(self):
        return self._environ.get('REMOTE_USER')

    def query(self):
        return self._environ.get('QUERY_STRING', '')

    def path(self):
        # We shouldn't rely on self.pathInfo since it can be changed
        return self._environ['SCRIPT_NAME']+self._environ.get('PATH_INFO', '')

    def scheme(self):
        # This variable is not part of CGI/1.1 standard (available in apache)
        script_uri = self._environ.get('SCRIPT_URI', '')
        if script_uri:
            if script_uri.startswith('http:'):
                return 'http'
            elif script_uri.startswith('https:'):
                return 'https'
        return Base.Request.scheme(self)


class Response(Base.Response):

    def _write_status(self):
        if self._status!=200:
            self._fp.write('Status: %d\r\n' % self._status)


class Adapter(Base.Adapter):

    def __call__(self):
        import os, sys
        request = Request(os.environ, sys.stdin)
        response = Response(request, sys.stdout)
        Base.Adapter.__call__(self, request, response)
