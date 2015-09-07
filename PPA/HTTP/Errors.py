import cgi

statusCodes = {
    # Generated from RFC 2616
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported'
}


class EndOfRequest(Exception):

    def __init__(self, status=None):
        self.status = status

    def handle(self, request, response):
        if self.status is not None:
            response.setStatus(self.status)

    _body_template = '''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>%(code)s - %(desc)s</title>
</head>
<body>
<h1>%(code)s - %(desc)s</h1>
%(message)s
</body>
</html>'''
    _body_content_type = 'text/html'

    def sendBody(self, response, message):
        response.setContentType(self._body_content_type)
        response.write(self._body_template % {
                            'code': self.status,
                            'desc': statusCodes.get(self.status, 'Unknown'),
                            'message': message})


class Redirect(EndOfRequest):

    def __init__(self, uri, status):
        EndOfRequest.__init__(self, status)
        self.uri = uri

    def handle(self, request, response):
        EndOfRequest.handle(self, request, response)
        response.headers['Location'] = self.uri
        quoted_uri = cgi.escape(self.uri, 1)
        self.sendBody(response,
            'Document moved here: <a href="%s">%s</a>.' % (quoted_uri,
                                                           quoted_uri))


class MovedPermanently(Redirect):

    def __init__(self, uri):
        Redirect.__init__(self, uri, 301)


class Found(Redirect):

    def __init__(self, uri):
        Redirect.__init__(self, uri, 302)


class SeeOther(Redirect):

    def __init__(self, uri):
        Redirect.__init__(self, uri, 303)


class TemporaryRedirect(Redirect):

    def __init__(self, uri):
        Redirect.__init__(self, uri, 307)


class ClientError(EndOfRequest):

    def __init__(self, status, message):
        EndOfRequest.__init__(self, status)
        self.message = message

    def handle(self, request, response):
        EndOfRequest.handle(self, request, response)
        self.sendBody(response, self.message)


class NotFound(ClientError):

    def __init__(self):
        EndOfRequest.__init__(self, 404)

    def handle(self, request, response):
        EndOfRequest.handle(self, request, response)
        self.sendBody(response,
                      'The requested URL %s was not found on this server.' % \
                                                cgi.escape(request.uri(), 1))



class ServerError(EndOfRequest):

    def __init__(self, status, message):
        EndOfRequest.__init__(self, status)
        self.message = message

    def handle(self, request, response):
        EndOfRequest.handle(self, request, response)
        self.sendBody(response, self.message)


class InternalServerError(ServerError):

    def __init__(self, message='The server encountered an internal error '\
                               'and was unable to complete your request.'):
        ServerError.__init__(self, 500, message)
