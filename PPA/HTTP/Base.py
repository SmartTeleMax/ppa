# $Id: Base.py,v 1.5 2006/10/18 13:39:33 ods Exp $

'''Define base classes Headers, Request, Response, Adapter'''
import logging
logger = logging.getLogger(__name__)

class Headers:
    '''Dictionary-like object of HTTP headers with case insensitive key lookup
    and add() method. The order of headers is preserved.'''

    def __init__(self, data={}):
        self._headers =  []
        self._headers_map = {}
        if data:
            if isinstance(data, dict):
                # From dictionary
                for key, value in data.iteritems():
                    self.add(key, value)
            else:
                # from any sequence of pairs
                for key, value in data:
                    self.add(key, value)
            # XXX Here can be initialization from other types: string, file.

    def __iter__(self):
        return iter(self._headers)

    def __len__(self):
        return len(self._headers)

    def keys(self):
        return self._headers_map.keys()

    def has_key(self, key):
        return self._headers_map.has_key(key)

    def add(self, key, value):
        self._headers.append((key, value))
        self._headers_map.setdefault(key.lower(), []).append(value)

    def __getitem__(self, key):
        '''Get header. If there are several header with the same key, their
        values are joined.'''
        # RFC 2616, 4.2 Message Headers
        return ', '.join(self._headers_map[key.lower()])

    def __setitem__(self, key, value):
        '''Replace headers with the same key.'''
        del self[key]
        self.add(key, value)

    def __delitem__(self, key):
        '''Delete all headers with this key. Never fail.'''
        key = key.lower()
        if self._headers_map.has_key(key):
            del self._headers_map[key]
            self._headers = [(k, v) for (k, v) in self._headers
                                    if k.lower()!=key]

    def __str__(self):
        return '\r\n'.join(['%s: %s' % h for h in self._headers])+'\r\n'


class Request:

    def __init__(self, headers, fp, path_info=''):
        self.headers = headers
        self._fp = fp
        self.pathInfo = path_info

    def read(self, *args):
        return self._fp.read(*args)

    def readline(self, *args):
        return self._fp.readline(*args)

    def version(self):
        parts = self.protocol().split('/')
        if len(parts)>=2:
            digits = parts[1].split('.')
            if len(digits)==2:
                try:
                    return (int(digits[0]), int(digits[1]))
                except ValueError:
                    pass
        return (0, 9)

    def query(self):
        # XXX General implementation
        raise NotImplementedError()

    def scheme(self):
        # There is no "right" way to determine scheme of request, but this will
        # work in most cases.  Redefine this method if this method is not
        # suitable.
        if self.serverPort()==443:
            return 'https'
        else:
            return 'http'


class Response:

    from Errors import statusCodes
    charset = 'ascii'
    charsetErrors = 'replace'
    charsetErrorsByType = {
        'text/sgml'     : 'xmlcharrefreplace',
        'text/html'     : 'xmlcharrefreplace',
        'text/xml'      : 'xmlcharrefreplace',
    }

    def __init__(self, request, fp, buffered=1):
        self._request = request
        self._fp = fp
        self.headers = Headers({'Content-Type': 'text/plain'})
        self._status = 200
        self._header_sent = 0
        self._buffered = buffered
        self._buffer = []

    def setBuffered(self, value):
        if value:
            if not self._header_sent:
                self._buffered = 1
            # Else: Too late to switch - ignoring
        else:
            if self._buffer:
                self.flush()
            self._buffered = 0

    def _write_status(self):
        self._fp.write('HTTP/%s %d %s\r\n' % \
                        (self._request.version(), self._status,
                         self.statusCodes.get(self._status, 'Unknown')))

    def _write_headers(self):
        self._fp.write(str(self.headers))
        self._fp.write('\r\n')

    def write(self, data):
        if isinstance(data, unicode):
            data = data.encode(self.charset, self.charsetErrors)
        if self._buffered:
            self._buffer.append(data)
        else:
            if not self._header_sent:
                self._write_status()
                self._write_headers()
                self._header_sent = 1
            self._fp.write(data)

    def flush(self):
        if not self._header_sent:
            self._write_status()
            self._write_headers()
            self._header_sent = 1
        write = self._fp.write
        for chunk in self._buffer:
            write(chunk)
        self._buffer = []

    def close(self):
        if not self._header_sent:
            data = ''.join(self._buffer)
            self.headers['Content-Length'] = str(len(data))
            self._write_status()
            self._write_headers()
            self._fp.write(data)
        else:
            self.flush()
        self._fp = None


    def setStatus(self, status):
        self._status = int(status)

    def setContentType(self, mime_type, charset=None, errors=None):
        if charset is None:
            header = mime_type
        else:
            header = '%s; charset=%s' % (mime_type, charset)
            self.charset = charset
        if errors is None:
            self.charsetErrors = self.charsetErrorsByType.get(
                                            mime_type, self.charsetErrors)
        else:
            self.charsetErrors = errors
        self.headers['Content-Type'] = header


class Adapter:
    """Base adapter for all protocol adapters in PPA.HTTP. Implementation
    of this adapter provide same interface for all supported web-protocols.

    There are two ways to use it:
    
    1) Initialize protocol's Adapter with function. This function will be
       called for every HTTP request with two arguments: request and response
       objects.
    2) Subclass protocol's Adapter and redefine handle method.

    Example:

    def hello(request, response):
        response.setContentType('text/plain')
        response.write('Hello world!')

    adapter = Adapter(hello)
    """

    def __init__(self, handle=None):
        if handle is not None:
            self.handle = handle

    def handle(self, request, response):
        import Errors
        raise Errors.NotFound()

    def __call__(self, request, response):
        from Errors import EndOfRequest, InternalServerError
        try:
            self.handle(request, response)
        except EndOfRequest, exc:
            exc.handle(request, response)
        except SystemExit:
            pass
        except IOError, exc:
            # Broken pipe
            logger.warning('%s: %s', exc.__class__.__name__, exc)
        except:
            # unhandled error
            logger.exception('Unhandled exception for %s', request.uri())
            InternalServerError().handle(request, response)

        try:
            response.close()
        except IOError, exc:
            # Broken pipe
            logger.warning('%s: %s', exc.__class__.__name__, exc)
