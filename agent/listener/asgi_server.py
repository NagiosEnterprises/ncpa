import datetime
import functools
import os
import sys

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.templating import Jinja2Templates

__INTERNAL__ = False

##################
#
# CONFIG
#
##################

ncpa_config = None # set in ncpa.py until we find a better way to handle this

# Get a configuration value or default
def get_config_value(section, option, default=None):
    try:
        value = config.get(section, option)
        if value == 'None':
            value = None
    except Exception as e:
        value = default
    return value


# Get a set of items from a configuration section
def get_config_items(section):
    return config.items(section)


##########
#
# PATHS
#
##########

# The following if statement is a workaround that is allowing us to run this
# in debug mode, rather than a hard coded location.

if getattr(sys, 'frozen', False):
    appdir = os.path.dirname(sys.executable)
else:
    appdir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

__tmpl_dir = os.path.join(appdir, 'listener', 'templates')
__stat_dir = os.path.join(appdir, 'listener', 'static')




# Starlette Middleware

class AllowedHostsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_hosts=None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts
    
    async def dispatch(self, request, call_next):
        if allowed_hosts and __INTERNAL__ is False:
            if request.remote_addr:
                ipaddr = ipaddress.ip_address(request.remote_addr)
                allowed_networks = [ipaddress.ip_network(_network.strip()) for _network in allowed_hosts.split(',')]
                allowed = [ipaddr in _network for _network in allowed_networks]
                if True not in allowed:
                    return PlainTextResponse("Invalid host", status_code=403)
            else:
                return PlainTextResponse("Invalid host", status_code=403)

        # We're good -- continue down the middleware chain
        response = await call_next(request)
        return response

# __middleware = [
#     Middleware(AllowedHostsMiddleware, allowed_hosts=[]), # TODO: add config
#     Middleware(SessionMiddleware, secret_key='foo'),
# ]

# JINJA2 SETUP
def __jinja2_filter_datetime(date, fmt=None):
    dt = datetime.datetime.fromtimestamp(date)
    if not fmt:
        fmt = '%m/%d/%Y %H:%M:%S'
    return dt.strftime(fmt)

def __jinja2_human_check_result(result):
    check_result = 'UNKNOWN'
    if result == 0:
        check_result = 'OK'
    elif result == 1:
        check_result = 'WARNING'
    elif result == 2:
        check_result = 'CRITICAL'
    return check_result



__templates = Jinja2Templates(directory=__tmpl_dir)
__templates.env.filters['strftime'] = __jinja2_filter_datetime
__templates.env.filters['human_check_result'] = __jinja2_human_check_result

# Helper function, since Jinja2 doesn't suppport context processors natively
def render(request, template_name, supplied_context={}):
    windows = False
    if os.name == 'nt':
        windows = True
    default_context = {
        'admin_visible': int(get_config_value('listener', 'admin_gui_access', 0)),
        'is_windows': windows,
        'no_nav': False,
        'flash_msg': False,
    }
    enriched_context = default_context | supplied_context
    enriched_context['request'] = request
    return __templates.TemplateResponse(template_name, enriched_context)

####################
#
# STARLETTE APP
#
####################

def startup():
    for route in webapp.routes:
        print(route.__dict__)
    print(webapp.routes)


async def home(request):
    print('foo')
    return PlainTextResponse('test')


from starlette.routing import Route
webapp = Starlette(debug=True, routes=[
    Route('/', home)
],
on_startup=[startup])

####################
#
# ROUTES AND VIEWS
#
####################



# Auth decorators

# Token authentication for authentication or actual auth
async def requires_token_or_auth(f):
    @functools.wraps(f)
    async def token_auth_decoration(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.values.get('token', None)

        # This is an internal call, we don't check
        if __INTERNAL__ is True:
            pass
        elif request.session.get('logged', False) or token == ncpa_token:
            pass
        elif token is None:
            request.session['redirect'] = request.url
            return redirect(url_for('login'))
        elif token != ncpa_token:
            return error(msg='Incorrect credentials given.')
        return await f(*args, **kwargs)

    return token_auth_decoration

async def requires_auth(f):
    @functools.wraps(f)
    async def auth_decoration(*args, **kwargs):
        if __INTERNAL__ is True:
            pass
        elif request.session.get('logged', False):
            pass
        else:
            request.session['redirect'] = session.request['url']
            return RedirectResponse(url=request.url_for('login'))
        return await f(*args, **kwargs)
    return auth_decoration    

# Admin auth check, admin access via password if applicable
async def requires_admin_auth(f):
    @functools.wraps(f)
    async def admin_auth_decoration(*args, **kwargs):

        # Verify that regular auth has happened
        if not request.session.get('logged', False):
            return redirect(url_for('login'))

        # Check if access to admin is okay
        admin_gui_access = int(get_config_value('listener', 'admin_gui_access', 0))
        if not admin_gui_access:
            return RedirectResponse(url=request.url_for('gui_index'))

        # Admin password
        admin_password = get_config_value('listener', 'admin_password', None)

        # Special case if admin password not set - log in automatically
        if admin_password is None:
            request.session['admin_logged'] = True

        if not request.session.get('admin_logged', False):
            return RedirectResponse(url=request.url_for('admin_login'))

        return await f(*args, **kwargs)

    return admin_auth_decoration


@webapp.route('/login')
async def login(request):

    # Verify authentication and redirect if we are authenticated
    if request.session.get('logged', False):
        return RedirectResponse(url=request.url_for('index'))

    ncpa_token = config.get('api', 'community_string')

    # Admin password
    has_admin_password = False
    admin_password = get_config_value('listener', 'admin_password', None)
    if admin_password is not None:
        has_admin_password = True

    # Get GUI admin auth only variable
    admin_auth_only = int(get_config_value('listener', 'admin_auth_only', 0))

    message = request.session.get('message', None)
    url = request.session.get('redirect', None)
    token = request.values.get('token', None)

    template_args = { 'hide_page_links': True,
                      'message': message,
                      'url': url,
                      'has_admin_password': has_admin_password,
                      'admin_auth_only': admin_auth_only }

    request.session['message'] = None

    # Do actual authentication check
    if token == ncpa_token and not admin_auth_only:
        request.session['logged'] = True
    elif token == admin_password and admin_password is not None:
        request.session['logged'] = True
        request.session['admin_logged'] = True

    if request.session.get('logged', False):
        if url:
            request.session['redirect'] = None
            return RedirectResponse(url=url)
        else:
            return RedirectResponse(url=request.url_for('index'))
    
    # Display error messages depending on what was given
    if token is not None:
        if not admin_auth_only:
            if token != ncpa_token or token != admin_password:
                template_args['error'] = 'Invalid token or password.'
        else:
            if token == ncpa_token:
                template_args['error'] = 'Admin authentication only.'
            else:
                template_args['error'] = 'Invalid password.'

    return render(request, 'login.html', template_args)

# @webapp.route('/gui/admin/login')
# @requires_auth
async def admin_login(request):

    # Verify authentication and redirect if we are authenticated
    if request.session.get('admin_logged', False):
        return RedirectResponse(url=request.url_for('admin'))

    # Admin password
    admin_password = get_config_value('listener', 'admin_password', None)

    message = request.session.get('message', None)
    password = request.values.get('password', None)
    template_args = { 'hide_page_links': False,
                      'message': message }

    request.session['message'] = None

    if password == admin_password and admin_password is not None:
        request.session['admin_logged'] = True
        return RedirectResponse(url=request.url_for('admin'))
    elif password is not None:
        template_args['error'] = 'Password was invalid.'

    return render(request, 'admin/login.html', template_args)
