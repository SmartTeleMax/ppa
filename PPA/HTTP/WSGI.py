# $Id: WSGI.py,v 1.2 2006/10/18 11:39:25 ods Exp $

'''Adapter for use in WSGI (Python Web Server Gateway Interface) servers.
See http://www.python.org/dev/peps/pep-0333/ for more information about WSGI.
'''

import Base, CGI, logging
logger = logging.getLogger(__name__)


class Request(CGI.Request):
    def scheme(self):
        try:
            return self._environ['wsgi.url_scheme']
        except KeyError:
            return CGI.Request.scheme(self)


class WSGIFileObject:
    def write(self, *args, **kwargs):
	raise RuntimeError('WSGI start_response was not called yet')


class Response(CGI.Response):
    def __init__(self, request, start_response, buffered=1):
	self._start_response = start_response
	CGI.Response.__init__(self, request, WSGIFileObject(), buffered)

    def _write_status(self):
	# All work is done by _write_headers
	pass

    def _write_headers(self):
	status = "%d %s" % (self._status,
                            self.statusCodes.get(self._status, 'Unknown'))
	self._fp.write = self._start_response(status, self.headers._headers)
	

class Adapter(Base.Adapter):
    """WSGI adapter handles abstraction for WSGI protocol. __call__ method
    implements interface of general WSGI application.

    Usage example with flup:

    class WSGIApplication(PPA.WSGI.Adapter):
        def handle(self, request, response):
            response.setContentType('text/plain')
            response.write('Hello world')

    wsgi_app = WSGIApplication()

    from flup.server.fcgi_fork import WSGIServer
    WSGIServer(wsgi_app).run()
    """
    

    def __call__(self, environ, start_response):
        request = Request(environ, environ['wsgi.input'])
        response = Response(request, start_response, buffered=1)	        
        Base.Adapter.__call__(self, request, response)
	return []
