import re
from urllib import unquote
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import Input


class PatchedWSGIHandler(WebSocketHandler):

    def get_environ(self):
        env = self.server.get_environ()
        env['REQUEST_METHOD'] = self.command
        env['SCRIPT_NAME'] = ''
        decode_slashes = False

        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''

        if not decode_slashes:
            path = re.sub(r'%2f', '%252F', path, flags=re.I)

        env['PATH_INFO'] = unquote(path)
        env['QUERY_STRING'] = query

        if self.headers.typeheader is not None:
            env['CONTENT_TYPE'] = self.headers.typeheader

        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        env['SERVER_PROTOCOL'] = self.request_version

        client_address = self.client_address
        if isinstance(client_address, tuple):
            env['REMOTE_ADDR'] = str(client_address[0])
            env['REMOTE_PORT'] = str(client_address[1])

        for key, value in self._headers():
            if key in env:
                if 'COOKIE' in key:
                    env[key] += '; ' + value
                else:
                    env[key] += ',' + value
            else:
                env[key] = value

        if env.get('HTTP_EXPECT') == '100-continue':
            socket = self.socket
        else:
            socket = None
        chunked = env.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked'
        self.wsgi_input = Input(self.rfile, self.content_length, socket=socket, chunked_input=chunked)
        env['wsgi.input'] = self.wsgi_input
        return env
