# $Id: ModPython.py,v 1.16 2004/02/06 15:17:16 corva Exp $

import Base
from mod_python import apache


class Request(Base.Request):

    def __init__(self, mp_request):
        Base.Request.__init__(self, mp_request.headers_in, mp_request,
                              mp_request.path_info)
        self._mp_request = mp_request

    def protocol(self):
        return self._mp_request.protocol

    def method(self):
        return self._mp_request.method.upper()

    def uri(self):
        return self._mp_request.unparsed_uri

    def serverAddr(self):
        return self._mp_request.connection.local_addr[0]

    def serverName(self):
        return self._mp_request.server.server_hostname

    def serverPort(self):
        return self._mp_request.connection.local_addr[1]

    def remoteAddr(self):
        return self._mp_request.connection.remote_ip

    def remoteName(self):
        return self._mp_request.connection.remote_host or self.remoteAddr()

    def user(self):
        return self._mp_request.connection.user

    def query(self):
        return self._mp_request.args or ''

    def path(self):
        return self._mp_request.uri


class Response(Base.Response):

    def __init__(self, mp_request, buffered=1):
        self._mp_request = mp_request
        self._fp = mp_request
        self.headers = mp_request.headers_out
        mp_request.content_type = 'text/plain'
        self._status = 200
        self._header_sent = 0
        self._buffered = buffered
        self._buffer = []

    def _write_status(self):
        pass

    def _write_headers(self):
        self._mp_request.send_http_header()

    def setStatus(self, status):
        Base.Response.setStatus(self, status)
        self._mp_request.status = status

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
        self._mp_request.content_type = header


class Adapter(Base.Adapter):

    def __call__(self, mp_request):
        request = Request(mp_request)
        response = Response(mp_request)
        Base.Adapter.__call__(self, request, response)
        return apache.OK
