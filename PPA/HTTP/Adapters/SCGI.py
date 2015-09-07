from CGI import Headers, Request, Response
import Base
from scgi import scgi_server


class _Handler(scgi_server.SCGIHandler):

    def __init__(self, adapter, fd):
        self.__adapter = adapter
        scgi_server.SCGIHandler.__init__(self, fd)

    def handle_connection(self, conn):
        stdin = conn.makefile('r')
        stdout = conn.makefile('w')
        environ = self.read_env(stdin)
        request = Request(environ, stdin)
        response = Response(request, stdout)
        self.__adapter(request, response)
        stdout.close()
        stdin.close()
        conn.close()


class Adapter(Base.Adapter):

    host = ''
    port = 4000
    max_children = 5
    base_path = ''

    def __init__(self):
        server = scgi_server.SCGIServer(handler_class=self.__handler_class,
                                        host=self.host, port=self.port,
                                        max_children=self.max_children)
        server.serve()

    def __call__(self, *args):
        if args:
            request, response = args
            path = request.path()
            if path.startswith(self.base_path):
                path = path[len(self.base_path):]
            request.pathInfo = path
            Base.Adapter.__call__(self, request, response)

    def __handler_class(self, fd):
        return _Handler(self, fd)
