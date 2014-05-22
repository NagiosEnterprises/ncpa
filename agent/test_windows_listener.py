from gevent.wsgi import WSGIServer
import listener.server
import listener.psapi
import listener.windowscounters
import os

counters = listener.windowscounters.get_counters_node()
listener.psapi.init_root(counters)

plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'plugins')

listener.server.listener.config['iconfig'] = {'api': 'test',
                                              'plugin directives': plugin_path}
listener.server.listener.secret_key = 'notasecret'

http_server = WSGIServer(('', 5693), listener.server.listener)
http_server.serve_forever()
