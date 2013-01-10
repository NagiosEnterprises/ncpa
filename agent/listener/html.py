import jinja2

class HttpResponse(object):
    
    def __init__(self, *args, **kwargs):
        super(HttpResponse, self).__init__(*args, **kwargs)
        self.code = 200
        self.message = '<html>Default Response</html>'
        self.header = 'text/html'

def render_to_response(template, params):
    env = jinja2.Environment(loader=jinja2.PackageLoader('listener', 'templates'))
    hp = HttpResponse()
    
    template = env.get_template(template)
    hp.message = template.render(**params)
    return hp
