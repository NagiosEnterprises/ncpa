from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session, make_response, abort
import os
import sys
import ssl
from zlib import ZLIB_VERSION as zlib_version
import platform
import requests
import functools
import datetime
import json
import psutil
import listener.psapi as psapi
import listener.processes as processes
import listener.database as database
import math
import re
import ipaddress
import urllib.parse
import gevent
import ncpa
import process.daemon_manager as daemon_manager
import subprocess
import listener.environment as environment
from ncpa import listener_logger as logging
#import inspect


# Set whether or not a request is internal or not
import socket
from hmac import compare_digest

__VERSION__ = ncpa.__VERSION__
__STARTED__ = datetime.datetime.now()
__INTERNAL__ = False


# The following if statement is a workaround that is allowing us to run this
# in debug mode, rather than a hard coded location.

if getattr(sys, 'frozen', False):
    appdir = os.path.dirname(sys.executable)
else:
    appdir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

tmpl_dir = os.path.join(appdir, 'listener', 'templates')
stat_dir = os.path.join(appdir, 'listener', 'static')

listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)


# Set some settings for Flask
listener.config.update(SECRET_KEY=os.urandom(24))
listener.url_map.strict_slashes = False
listener.config.update(
    SESSION_COOKIE_SECURE = True
);


# ------------------------------
# Helper functions
# ------------------------------


# Get a configuration value or default
def get_config_value(section, option, default=None):
    try:
        value = listener.config['iconfig'].get(section, option)
        if value == 'None':
            value = None
    except Exception as e:
        value = default
    return value


# Get a set of items from a configuration section
def get_config_items(section):
    return listener.config['iconfig'].items(section)


# Misc function for making information for main page
def make_info_dict():
    now = datetime.datetime.now()
    uptime = str(now - __STARTED__)
    uptime = uptime.split('.', 1)[0]

    # Get check status
    db = database.DB()
    total_checks = db.get_checks_count()
    check_logging_time = int(get_config_value('general', 'check_logging_time', 30))

    uname = platform.uname()
    proc_type = uname[5]
    if proc_type == '':
        proc_type = uname[4];

    return { 'agent_version': __VERSION__,
             'uptime': uptime,
             'python_version': sys.version,
             'ssl_version': ssl.OPENSSL_VERSION,
             'zlib_version': zlib_version,
             'processor': proc_type,
             'node': uname[1],
             'system': uname[0],
             'release': uname[2],
             'version': uname[3],
             'total_checks': format(total_checks, ",d"),
             'check_logging_time': check_logging_time }


def get_unmapped_ip(ip):
    """ Get unmapped IPv4 in case ip is an IPv4-mapped IPv6

    This function gets an IPv4, IPv6 or IPv4-mapped IPv6 address.
    It returns the given ip, but in case ip is an IPv4-mapped IPv6 address,
    it returns ip as ordinary IPv4.
    """
    try:
        # check if ip is IPv6
        if ipaddress.ip_address(str(ip)).version == 6:
            # check if ip is a IPv4-mapped IPv6 address
            if ipaddress.IPv6Address(str(ip)).ipv4_mapped is not None:
                # return the ordinary IPv4 address
                return str(ipaddress.IPv6Address(str(ip)).ipv4_mapped)
            else:
                # return the IPv6 address
                return str(ipaddress.IPv6Address(str(ip)))
        else:
            # return the IPv4 address
            return str(ipaddress.ip_address(str(ip)))
    # Needed for passive checks, in this case ip is 'Internal'
    except ValueError as e:
        logging.debug(e)
        return ip


def lookup_hostname(ip):
    """
    This function gets an ip and returns the hostname lookuped by DNS.
    """
    try:
        hostname = socket.gethostbyaddr(str(ip))
        return hostname[0]
    except Exception as e:
        logging.error(e)
        return


def is_ip(ip):
    """
    Checks if ip is a valid ip address.
    """
    try:
        ipaddress.ip_address(str(ip)).version
        return True
    except ValueError as e:
        logging.debug(e)
        return False


def is_network(ip):
    """
    Checks if ip is a valid ip network.
    """
    try:
        ipaddress.ip_network(str(ip))
        return True
    except ValueError as e:
        logging.debug(e)
        return False

# Securely compares strings - byte string or unicode
# Comparison is done via compare_digest() to prevent timing attacks
# If both items evaluate to false, they match. This makes it easier to handle
# empty strings or variables which may have "NoneType"
def secure_compare(item1, item2):
    item1 = '' if item1 is None else str(item1)
    item2 = '' if item2 is None else str(item2)
    return compare_digest(item1, item2)


# ------------------------------
# Authentication Wrappers
# ------------------------------

@listener.before_request
def before_request():
    # allowed is set to False by default
    allowed = False
    allowed_hosts = get_config_value('listener', 'allowed_hosts')
    logging.debug("    before_request() - type(request.view_args): %s", type(request.view_args))

    # For logging some debug info for actual page requests
    if isinstance(request.view_args, dict) and ('filename' not in request.view_args):
        logurl = request.url
        parts = logurl.split('token=')
        new_parts = [parts[0]]
        for part in parts[1:]:
            sub_parts = part.split('&', 1)
            sub_parts[0] = '********'
            new_parts.append('&'.join(sub_parts))
        logurl = 'token='.join(new_parts)
        logging.info("before_request() - request.url: %s", logurl)
        logging.debug("    before_request() - request.path: %s", request.path)
        logging.debug("    before_request() - request.url_rule: %s", request.url_rule)
        logging.debug("    before_request() - request.view_args: %s", request.view_args)
        logging.debug("    before_request() - request.routing_exception: %s", request.routing_exception)

    if allowed_hosts and __INTERNAL__ is False:
        if request.remote_addr:
            for host in allowed_hosts.split(','):
                host = host.strip()
                remote_ipaddr_unmapped = get_unmapped_ip(request.remote_addr)

                # check if host is written as CIDR suffix notation
                if is_network(host):
                    remote_ipaddr = request.remote_addr
                    # check if host is a valid ip
                    if is_ip(host):
                        # check if ip is allowed
                        if remote_ipaddr == host or remote_ipaddr_unmapped == host:
                            allowed = True
                            break
                    else:
                        # host is written as CIDR suffix notation
                        # get all ip's from the given subnet
                        allowed_network = ipaddress.ip_network(str(host))

                        for ip in allowed_network:
                            ip = str(ip)
                            # check if an ip of the subnet is allowed
                            if remote_ipaddr == ip or remote_ipaddr_unmapped == ip:
                                allowed = True
                                break
                else:
                    # lookup of the remote_ipaddr_unmapped
                    remote_hostname = lookup_hostname(remote_ipaddr_unmapped)

                    # check if hostname is allowed
                    if remote_hostname == host:
                        allowed = True
                        break

            # if not allowed, abort
            if not allowed:
                abort(403)
        else:
            abort(403)


@listener.after_request
def apply_headers(response):
    allowed_sources = get_config_value('listener', 'allowed_sources')

    if allowed_sources:
        response.headers["X-Frame-Options"] = "ALLOW-FROM %s" % allowed_sources
        response.headers["Content-Security-Policy"] = "frame-ancestors %s" % allowed_sources
    else:
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"

    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'

    return response


# Variable injection for all pages that flask creates
@listener.context_processor
def inject_variables():
    admin_gui_access = int(get_config_value('listener', 'admin_gui_access', 0))
    windows = False
    if os.name == 'nt':
        windows = True
    values = { 'admin_visible': admin_gui_access, 'is_windows': windows,
               'no_nav': False, 'flash_msg': False }
    return values


@listener.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    dt = datetime.datetime.fromtimestamp(date)
    if not fmt:
        fmt = '%m/%d/%Y %H:%M:%S'
    return dt.strftime(fmt)


@listener.template_filter('human_check_result')
def _jinja2_filter_datetime(result):
    check_result = 'UNKNOWN'
    if result == 0:
        check_result = 'OK'
    elif result == 1:
        check_result = 'WARNING'
    elif result == 2:
        check_result = 'CRITICAL'
    return check_result


# Token authentication for authentication or actual auth
def requires_token_or_auth(f):
    @functools.wraps(f)
    def token_auth_decoration(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.values.get('token', None)
        token_valid = secure_compare(token, ncpa_token)

        # This is an internal call, we don't check
        if __INTERNAL__ is True:
            pass
        elif session.get('logged', False) or token_valid:
            pass
        elif token is None:
            session['redirect'] = request.url
            return redirect(url_for('login'))
        elif not token_valid:
            return error(msg='Incorrect credentials given.')
        return f(*args, **kwargs)

    return token_auth_decoration


# Standard auth check, no token-only access
def requires_auth(f):
    @functools.wraps(f)
    def auth_decoration(*args, **kwargs):

        # This is an internal call, we don't check
        if __INTERNAL__ is True:
            pass
        elif session.get('logged', False):
            pass
        else:
            session['redirect'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return auth_decoration


# Admin auth check, admin access via password if applicable
def requires_admin_auth(f):
    @functools.wraps(f)
    def admin_auth_decoration(*args, **kwargs):

        # Verify that regular auth has happened
        if not session.get('logged', False):
            return redirect(url_for('login'))

        # Check if access to admin is okay
        admin_gui_access = int(get_config_value('listener', 'admin_gui_access', 0))
        if not admin_gui_access:
            return redirect(url_for('gui_index'))

        # Admin password
        admin_password = get_config_value('listener', 'admin_password', None)

        # Special case if admin password not set - log in automatically
        if admin_password is None:
            session['admin_logged'] = True

        if not session.get('admin_logged', False):
            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)

    return admin_auth_decoration


# ------------------------------
# Authentication
# ------------------------------


@listener.route('/login', methods=['GET', 'POST'], provide_automatic_options = False)
def login():
    # Verify authentication and redirect if we are authenticated
    if session.get('logged', False):
        return redirect(url_for('index'))

    ncpa_token = listener.config['iconfig'].get('api', 'community_string')

    # Admin password
    has_admin_password = False
    admin_password = get_config_value('listener', 'admin_password', None)
    if admin_password is not None:
        has_admin_password = True

    # Get GUI admin auth only variable
    admin_auth_only = int(get_config_value('listener', 'admin_auth_only', 0))

    message = session.get('message', None)
    url = session.get('redirect', None)
    token = request.values.get('token', None)

    token_valid = secure_compare(token, ncpa_token)
    token_is_admin = secure_compare(token, admin_password)

    template_args = { 'hide_page_links': True,
                      'message': message,
                      'url': url,
                      'has_admin_password': has_admin_password,
                      'admin_auth_only': admin_auth_only }

    session['message'] = None

    # Do actual authentication check
    if not admin_auth_only and token_valid:
        session['logged'] = True
    elif admin_password is not None and token_is_admin:
        session['logged'] = True
        session['admin_logged'] = True

    if session.get('logged', False):
        if url:
            session['redirect'] = None
            return redirect(url)
        else:
            return redirect(url_for('index'))

    # Display error messages depending on what was given
    if token is not None:
        if not admin_auth_only:
            if not token_valid and not token_is_admin:
                template_args['error'] = 'Invalid token or password.'
        else:
            if token_valid:
                template_args['error'] = 'Admin authentication only.'
            else:
                template_args['error'] = 'Invalid password.'

    return render_template('login.html', **template_args)


@listener.route('/gui/admin/login', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def admin_login():
    # Verify authentication and redirect if we are authenticated
    if session.get('admin_logged', False):
        return redirect(url_for('admin'))

    # Admin password
    admin_password = get_config_value('listener', 'admin_password', None)
    password = request.values.get('password', None)
    password_valid = secure_compare(password, admin_password)

    message = session.get('message', None)
    template_args = { 'hide_page_links': False,
                      'message': message }

    session['message'] = None

    if admin_password is not None and password_valid:
        session['admin_logged'] = True
        return redirect(url_for('admin'))
    elif password is not None:
        template_args['error'] = 'Password was invalid.'

    return render_template('admin/login.html', **template_args)


@listener.route('/logout', methods=['GET', 'POST'], provide_automatic_options = False)
def logout():
    session.clear()
    session['message'] = 'Successfully logged out.'
    return redirect(url_for('login'))


# ------------------------------
# Templates for HTTP error codes
# ------------------------------


@listener.errorhandler(404)
def error_page_not_found(e):
    template_args = {}
    if not session.get('logged', False):
        template_args = { 'hide_page_links': True }
    return render_template('errors/404.html', **template_args), 404


@listener.errorhandler(500)
def error_page_not_found(e):
    template_args = {}
    if not session.get('logged', False):
        template_args = { 'hide_page_links': True }
    return render_template('errors/500.html', **template_args), 500


# ------------------------------
# Basic GUI
# ------------------------------


@listener.route('/', provide_automatic_options = False)
@requires_auth
def index():
    return redirect(url_for('gui_index'))


@listener.route('/gui/', provide_automatic_options = False)
@requires_auth
def gui_index():
    info = make_info_dict()
    try:
        return render_template('gui/dashboard.html', **info)
    except Exception as e:
        logging.exception(e)


@listener.route('/gui/checks', provide_automatic_options = False)
@requires_auth
def checks():
    data = { 'filters': False, 'show_fp': False, 'show_lp': False }
    db = database.DB()

    data['senders'] = db.get_check_senders()

    search = request.values.get('search', '')
    size = int(request.values.get('size', 20))
    page = int(request.values.get('page', 1))
    ctype = request.values.get('ctype', '')
    page_raw = page

    status = request.values.get('status', '')
    if status != '':
        status = int(status)

    check_senders = request.values.getlist('check_senders')

    # Add data values for page
    data['check_senders'] = check_senders
    data['search'] = search
    data['checks'] = db.get_checks(search, size, page, status=status, ctype=ctype, senders=check_senders)
    data['size'] = size
    data['page'] = format(page, ",d")
    data['page_raw'] = page_raw
    data['status'] = status
    data['ctype'] = ctype

    # Do some page math magic
    total = db.get_checks_count(search, status=status, senders=check_senders)

    total_pages = int(math.ceil(float(total)/size))
    if total_pages < 1:
        total_pages = 1

    data['total_pages'] = format(total_pages, ",d")
    data['total'] = format(total, ",d")

    # Get a URL for the next/last pages
    link = 'checks?page='
    link_vals = ''
    if size != 20:
        link_vals += '&size=' + str(size)
    if status != '':
        link_vals += '&status=' + str(status)
    if ctype != '':
        link_vals += '&ctype=' + str(ctype)
    if search != '':
        link_vals += '&search=' + str(search)
    if len(check_senders) > 0:
        for sender in check_senders:
            link_vals += '&check_senders=' + sender

    # Get list of pages to display
    data['page_links'] = { page: link + str(page) }
    for x in range(1, 5):
        if not (page_raw - x) <= 0:
            data['page_links'][page_raw - x] = link + str(page - x) + link_vals
            if page_raw > 5:
                data['show_fp'] = True
                data['show_fp_link'] = link + '1' + link_vals
        if not (page_raw + x) > total_pages:
            data['page_links'][page_raw + x] = link + str(page + x) + link_vals
            if page_raw < total_pages:
                data['show_lp'] = True
                data['show_lp_link'] = link + str(total_pages) + link_vals
    data['page_link_iters'] = sorted(data['page_links'].keys())

    # Get start and end record display
    data['show_start_end'] = False
    if total > size:
        data['show_start_end'] = True
        start_record = (page_raw - 1) * size
        data['start_record'] = format(start_record + 1, ",d")
        end_record = start_record + size
        if end_record > total:
            end_record = total
        data['end_record'] = format(end_record, ",d")

    # Switch if we have any filters applied
    if search != '' or status != '' or check_senders != []:
        data['filters'] = True

    return render_template('gui/checks.html', **data)


@listener.route('/gui/stats', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def live_stats():
    return render_template('gui/stats.html')


@listener.route('/gui/top', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def top_base():
    return render_template('gui/top.html')


@listener.route('/gui/tail', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def tail_base():
    return render_template('gui/tail.html')


# This function renders the graph picker page, which can be though of
# the explorer for the graphs.
@listener.route('/gui/graphs', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def graph_picker():
    return render_template('gui/graphs.html')


@listener.route('/gui/api', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_auth
def view_api():
    info = make_info_dict()
    return render_template('gui/api.html', **info)


# Help section (just a frame for the actual help)
@listener.route('/gui/help', provide_automatic_options = False)
@requires_auth
def help_section():
    return render_template('gui/help.html')


# ------------------------------
# Admin GUI section
# ------------------------------


@listener.route('/gui/admin', methods=['GET', 'POST'], provide_automatic_options = False)
@listener.route('/gui/admin/', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin():
    tmp_args = {}
    tmp_args['config'] = listener.config['iconfig']
    return render_template('admin/index.html', **tmp_args)


@listener.route('/gui/admin/global', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_global():
    section = 'general'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    print("sectioncfg: ", sectioncfg)
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg

    # Check session for flash message
    flash_msg_text = session.get('flash_msg_text', '')
    if flash_msg_text != '':
        flash_msg_type = session.get('flash_msg_type', 'info')
        tmp_args['flash_msg_text'] = flash_msg_text
        tmp_args['flash_msg_type'] = flash_msg_type
        tmp_args['flash_msg'] = True
        session['flash_msg_text'] = ''

    return render_template('admin/global.html', **tmp_args)


@listener.route('/gui/admin/listener', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_listener_config():
    section = 'listener'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg

    # Todo: add form actions when submitted

    return render_template('admin/listener.html', **tmp_args)


@listener.route('/gui/admin/api', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_api_config():
    section = 'api'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg
    # tmp_args = { 'no_nav': True,
    #              'community_string': get_config_value('api', 'community_string', 'mytoken') }

    return render_template('admin/api.html', **tmp_args)


@listener.route('/gui/admin/passive', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_passive_config():
    section = 'passive'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg

    if tmp_args['sectioncfg']['handlers'] is None:
        tmp_args['sectioncfg']['handlers'] = []

    # Todo: add form actions when submitted

    return render_template('admin/passive.html', **tmp_args)


@listener.route('/gui/admin/nrdp', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_nrdp_config():
    section = 'nrdp'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg

    handlers = get_config_value('passive', 'handlers', None)
    if handlers is None:
        handlers = []
    tmp_args['handlers'] = handlers

    return render_template('admin/nrdp.html', **tmp_args)


@listener.route('/gui/admin/kafkaproducer', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_kafkaproducer_config():
    section = 'kafkaproducer'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = { 'no_nav': True }
    tmp_args['sectioncfg'] = sectioncfg
    handlers = get_config_value('passive', 'handlers', None)

    if handlers is None:
        handlers = []
    tmp_args['handlers'] = handlers

    return render_template('admin/kafkaproducer.html', **tmp_args)


@listener.route('/gui/admin/plugin-directives', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_plugin_config():
    section = 'plugin directives'
    config = listener.config['iconfig']
    sectioncfg = dict(config.items(section, 1))
    tmp_args = {}
    tmp_args['sectioncfg'] = sectioncfg

    try:
        directives = [x for x in get_config_items('plugin directives') if x[0] not in listener.config['iconfig'].defaults()]
    except Exception as e:
        directives = []
    tmp_args['directives'] = directives

    return render_template('admin/plugins.html', **tmp_args)


@listener.route('/gui/admin/passive-checks', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_checks_config():
    try:
        checks = [x for x in get_config_items('passive checks') if x[0] not in listener.config['iconfig'].defaults()]
    except Exception as e:
        checks = []
    tmp_args = { 'no_nav': True,
                 'checks': checks }
    return render_template('admin/checks.html', **tmp_args)


# Page that removes all checks from the DB
@listener.route('/gui/admin/clear-check-log', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_admin_auth
def admin_clear_check_log():
    db = database.DB()
    db.truncate('checks')
    session['flash_msg_type'] = 'success'
    session['flash_msg_text'] = 'Cleared checks log of all check values.'
    return redirect(url_for('admin_global'))


# ------------------------------
# Web Sockets
# ------------------------------


@listener.route('/ws/api/<path:accessor>', websocket=True)
@requires_token_or_auth
def api_websocket(accessor=None):
    logging.debug("api_websocket()")
    """Meant for use with the websocket and API.

    Make a connection to this function, and then pass it the API
    path you wish to receive. Function returns only the raw value
    and unit in list form.

    """
    sane_args = dict(request.args)
    sane_args['accessor'] = accessor
    logging.debug("api_websocket() - sane_args: %s: ", sane_args)

    config = listener.config['iconfig']

    encoding = sys.stdin.encoding
    if encoding is None:
        encoding = sys.getdefaultencoding()

    # Refresh the root node before creating the websocket
    psapi.refresh(config)

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        logging.info("===== api_websocket() - websocket for %s listening...", accessor)

        while not ws.closed:
            logging.debug("    **** api_websocket() - while open...")
            try:
                message = ws.receive()
                if message:
                    logging.debug("        api_websocket - message: %s", message)
                    node = psapi.getter(message, config, request.path, request.args)
                    logging.debug("        api_websocket - node: %s", node)
                    prop = node.name
                    logging.debug("        api_websocket - prop: %s", prop)
                    val = node.walk(first=True, **sane_args)
                    logging.debug("        api_websocket - val: %s", val)
                    jval = json.dumps(val[prop])
                    logging.debug("        api_websocket - jval: %s", jval)
                    ws.send(jval)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.warning("api_websocket() Exception: %s", e)
                ws.close()
                break
        else:
            logging.info("===== api_websocket() - websocket for %s closed.", accessor)

    else:
        logging.warning("api_websocket() - NO request.environ.wsgi.websocket")

    return ''


@listener.route('/ws/top', websocket=True)
@requires_token_or_auth
def top_websocket():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        logging.info("===== top_websocket() - websocket listening...")

        while not ws.closed:
            logging.debug("    **** top_websocket() - while open...")
            load = psutil.cpu_percent()
            vir_mem = psutil.virtual_memory().percent
            swap_mem = psutil.swap_memory().percent
            pnode = processes.get_node()
            procs = pnode.get_process_dict()

            process_list = []

            for process in procs:
                if process['pid'] == 0:
                    continue
                process_list.append(process)


            json_val = json.dumps({'load': load, 'vir': vir_mem, 'swap': swap_mem, 'process': process_list})

            try:
                ws.send(json_val)
                gevent.sleep(1)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.warning("top_websocket Exception: %s", e)
                ws.close()
                break
        else:
            logging.info("===== top_websocket() - websocket closed.")

    return ''


@listener.route('/ws/tail', websocket=True)
@requires_token_or_auth
def tail_websocket():
    import listener.windowslogs

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        logging.info("===== top_websocket() - websocket listening...")

        last_ts = datetime.datetime.now()
        while not ws.closed:
            logging.debug("    **** tail_websocket() - while open...")
            try:
                last_ts, logs = listener.windowslogs.tail_method(last_ts=last_ts, **request.args)

                json_val = json.dumps(logs)
                ws.send(json_val)

                gevent.sleep(5)
            except Exception as e:
                logging.warning("tail_websocket Exception: %s", e)
                ws.close()
                break
        else:
            logging.info("===== tail_websocket() - websocket closed.")

    return ''


# ------------------------------
# Internal (loaded internally)
# ------------------------------


@listener.route('/top', provide_automatic_options = False)
@requires_auth
def top():
    display = request.values.get('display', 0)
    highlight = request.values.get('highlight', None)
    warning = request.values.get('warning', 0)
    critical = request.values.get('critical', 0)
    info = {}

    if highlight is None:
        info['highlight'] = None
    else:
        info['highlight'] = highlight

    try:
        info['warning'] = int(warning)
    except TypeError:
        info['warning'] = 0

    try:
        info['critical'] = int(critical)
    except TypeError:
        info['critical'] = 0

    try:
        info['display'] = int(display)
    except TypeError:
        info['display'] = 0

    return render_template('top.html', **info)


@listener.route('/tail', provide_automatic_options = False)
@requires_token_or_auth
def tail(accessor=None):
    info = { }

    query_string = request.query_string
    info['query_string'] = urllib.parse.quote(query_string)

    return render_template('tail.html', **info)


@listener.route('/graph/<path:accessor>', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_token_or_auth
def graph(accessor=None):
    """
    Accessor method for fetching the HTML for the real-time graphing.

    :param accessor: The API path to be accessed (see /api)
    :type accessor: unicode
    :rtype: flask.Response
    """
    info = {'graph_path': accessor,
            'graph_hash': hash(accessor)}

    config = listener.config['iconfig']

    # Refresh the root node before creating the websocket
    psapi.refresh(config)

    node = psapi.getter(accessor, config, request.path, request.args, cache=True)
    prop = node.name

    if request.values.get('delta'):
        info['delta'] = 1
    else:
        info['delta'] = 0

    info['graph_prop'] = prop
    query_string = request.query_string
    info['query_string'] = urllib.parse.quote(query_string)

    url = urllib.parse.urlparse(request.url)
    info['load_from'] = url.scheme + '://' + url.netloc
    info['load_websocket'] = url.netloc

    # Generate page and add cross-domain loading
    response = make_response(render_template('graph.html', **info))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


# ------------------------------
# Misc Endpoints
# ------------------------------


@listener.route('/error/', provide_automatic_options = False)
@listener.route('/error/<msg>', provide_automatic_options = False)
def error(msg=None):
    if not msg:
        msg = 'Error occurred during processing request.'
    return jsonify(error=msg)


@listener.route('/testconnect/', methods=['GET', 'POST'], provide_automatic_options = False)
def testconnect():
    """
    Method meant for testing connecting with monitoring applications and wizards.

    :rtype: flask.Response
    """
    real_token = listener.config['iconfig'].get('api', 'community_string')
    test_token = request.values.get('token', None)
    if real_token != test_token:
        return jsonify({'error': 'Bad token.'})
    else:
        return jsonify({'value': 'Success.'})


@listener.route('/nrdp/', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_token_or_auth
def nrdp():
    """
    Function acts an an NRDP forwarder.

    Refers to the parent node and parent token under the NRDP section of the config
    and forward all traffic hitting this function to the parent. Will return
    the response from the parent NRDP server, so pretty much acts as proxy.

    :rtype: flask.Response
    """
    try:
        forward_to = listener.config['iconfig'].get('nrdp', 'parent')
        if request.method == 'get':
            response = requests.get(forward_to, params=request.args)
        else:
            response = requests.post(forward_to, params=request.form)
        resp = Response(response.content, 200, mimetype=response.headers['content-type'])
        return resp
    except Exception as exc:
        logging.exception(exc)
        return error(msg=exc)


# ------------------------------
# Configuration Endpoints
# ------------------------------
#
# ALLOWED SECTIONS:
#   Global
#      - Check Logging (in browser)
#      - Check Log Retention (days)
#      - Log Level (info, warning, debug, error)
#      - Log Max MB
#      - Log Backups (days)
#      - Default Units (K,Ki,M,Mi,G,Gi,T,Ti)
#   Listener
#       None
#   API
#       None
#   Passive
#       - Handlers (None, NRDP, Kafka Producer, Both)
#   NRDP
#       - NRDP URL
#       - NRDP Token
#       - Hostname
#       - Connection Timeout
#   Kafka Producer
#       - Hostname
#       - Servers
#       - Client Name
#       - Topic
#   Plugin Directives
#       - None
#   Passive Checks
#       - Adding checks

# sanitize inputs from the form
def sanitize_for_configparser(input_value):
    max_length = 1024
    if len(input_value) > max_length:
        return False
    
    input_value = input_value.replace('\\', '').replace('\n', '').replace('\r', '')
    sanitized = input_value.encode().decode('unicode_escape')
    sanitized = sanitized.replace('/', '\/')
    
    return sanitized

# validate the input from the form against the valid options
def validate_config_input(section, option, value, valid_options):
    # [section], option_name, option_name_in_ncpa.cfg, allowed_values (list or regex)
    for (target_section, tbl_option, option_in_file, valid_values) in valid_options:
        if "["+section+"]" == target_section:
            if option == tbl_option:
                if isinstance(valid_values, list):
                    if value.strip() not in valid_values:
                        return False
                    else:
                        value = sanitize_for_configparser(value)
                        return (section, option_in_file, value.strip())
                elif not re.match(valid_values, value.strip()):
                    return False
                else:
                    value = sanitize_for_configparser(value)
                    return (section, option_in_file, value.strip())
    return None, None, None

# inputs sanitized and validated, write to the config and file
# section_options_to_update = {("section", "option_name"): "value"}
def write_to_config_and_file(section_options_to_update):
    config = listener.config['iconfig']

    for (section, option), value in section_options_to_update.items():
        if not value:
            return False # Invalid input detected, don't write to config file

    try:
        if environment.SYSTEM == "Windows":
            cfg_file = os.path.join('C:\\', 'Program Files', 'NCPA', 'etc', 'ncpa.cfg')
        else:
            cfg_file = os.path.join('/', 'usr', 'local', 'ncpa', 'etc', 'ncpa.cfg')

        sed_cmds = []
        lines = None
        with open(cfg_file, 'r') as configfile:
            lines = configfile.readlines()

            uncommented_options = set()
            section = None

            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("["):
                    section = line.strip()
                    continue
                if '=' in line and not line.startswith('#'):
                    option = line.split('=')[0].strip()
                    uncommented_options.add((section, option))

            section = None

            for i, line in enumerate(lines):
                if line.startswith("["):
                    section = line.strip()
                    continue
                for (target_section, target_option), value in section_options_to_update.items():
                    if section == "["+target_section+"]":
                        pattern = re.compile(r'^\s*(#\s*)(' + re.escape(target_option) + r'\s*=\s*).*$', re.IGNORECASE)
                        no_comment_pattern = re.compile(r'^\s*(' + re.escape(target_option) + r'\s*=\s*).*$', re.IGNORECASE)
                        
                        # if there is an uncommented version in the config file, we don't want to replace commented out versions
                        if (section, target_option) in uncommented_options:
                            if no_comment_pattern.match(line):
                                sed_cmds.append(f"sed -i '{i+1}s/.*/{target_option} = {value}/' {cfg_file}")
                                config.set(target_section, target_option, value)
                        else:
                            if pattern.match(line):
                                sed_cmds.append(f"sed -i '{i+1}s/.*/{target_option} = {value}/' {cfg_file}")
                                config.set(target_section, target_option, value)
            configfile.close()

        for sed_cmd in sed_cmds:

            if environment.SYSTEM == "Windows":
                match = re.match(r's/(.*)/(.*)/', sed_cmd)
                if not match:
                    continue
                pattern, replacement = match.groups()
                # Convert sed syntax to PowerShell equivalent
                powershell_cmd = f"Get-Content {cfg_file} | Foreach-Object {{ $_ -replace '{pattern}', '{replacement}' }} | Set-Content {cfg_file}"
                command = ["powershell", "-Command", powershell_cmd]
                running_check = subprocess.run(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT
                )
            else:
                running_check = subprocess.run(
                    sed_cmd, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid
                )

            if running_check.returncode != 0:
                logging.error("write_to_configFile() - sed_cmd failed: %s", running_check.stdout)
                return False
    except Exception as e:
        logging.exception(e)
        return False
        
# Endpoint to make allowed changes to the config
@listener.route('/update-config/', methods=['POST'], provide_automatic_options = False)
@requires_admin_auth
def set_config():
    config = listener.config['iconfig']
    if config.get('listener', 'allow_config_edit') != '1':
        return jsonify({'message': 'Editing your configuration via the GUI is disabled.'})

    # [section], option_name from form, option_name in ncpa.cfg, allowed_values (list or regex)
    allowed_options = [
        ("[general]", "check_logging",  "check_logging",        ["0", "1"]),
        ("[general]", "check_logging_time","check_logging_time",r"^\d+$"),
        ("[general]", "log_level",      "loglevel",             ["info", "warning", "debug", "error"]),
        ("[general]", "log_max_mb",     "logmaxmb",             r"^\d+$"),
        ("[general]", "log_backups",    "logbackups",           r"^\d+$"),
        ("[general]", "default_units",  "default_units",        ["K", "Ki", "M", "Mi", "G", "Gi", "T", "Ti"]),

        ("[passive]", "handlers",       "handlers",             ["None", "nrdp", "kafkaproducer", "nrdp, kafkaproducer"]),

        ("[nrdp]",    "nrdp_url",       "parent",               r"^https?://\S+/nrdp$"),
        ("[nrdp]",    "nrdp_token",     "token",                r"^\S+$"),
        ("[nrdp]",    "hostname",       "hostname",             r"^\S+$"),
        ("[nrdp]",    "connection_timeout",   "connection_timeout",   r"^\d+$"),

        ("[kafkaproducer]", "hostname",     "hostname",         r"^\S+$"),
        ("[kafkaproducer]", "servers",      "servers",          r"^\S+(?:,\S+)*$"),
        ("[kafkaproducer]", "client_name",  "clientname",       r"^\S+$"),
        ("[kafkaproducer]", "topic",        "topic",            r"^\S+$"),
    ]

    editable_options_list = [option for (_, option, _, _) in allowed_options]

    section_options_to_update = {}
    
    section = request.form.get('section', None)
    if section is None:
        return jsonify({'type': 'danger', 'message': 'No section specified.'})
    for (option, value) in request.form.items():
        if option in editable_options_list:
            (current_section, current_option, sanitized_input) = validate_config_input(section, option, value, allowed_options) or (None, None, None)
            section_options_to_update[current_section, current_option] = sanitized_input
            if not current_section or not current_option or not sanitized_input:
                return jsonify({'type': 'danger', 'message': 'Invalid input: %s' % option})
    write_to_config_and_file(section_options_to_update)


    # TODO: finish option of restarting of the service (disabled by default)
    # allow_restart = config.get('general', 'allow_remote_restart').lower()
    # if allow_restart in {'none', '0'}:
    #     logging.info("restart not allowed")
    # else:
    #     try:
    #         logging.info("allow_restart: %s", allow_restart)
    #         if os.name == 'nt':
    #             logging.info("restarting ncpa service")
    #             restart_ncpa = subprocess.run(
    #                 "net stop ncpa && net start ncpa",
    #                 shell=True,
    #                 stdout=subprocess.PIPE,
    #                 stderr=subprocess.STDOUT
    #             )
    #         elif os.name == 'posix':
    #             logging.info("restarting ncpa service")
    #             restart_ncpa = subprocess.run(
    #                 "systemctl restart ncpa",
    #                 shell=True,
    #                 stdout=subprocess.PIPE,
    #                 stderr=subprocess.STDOUT
    #             )
    #         else:
    #             logging.error("unsupported OS")
    #             return jsonify({'type': 'danger', 'message': 'Unsupported OS. This service must be restarted manually.'})
    #     except Exception as e:
    #         logging.exception(e)
    #         return jsonify({'type': 'danger', 'message': 'Failed to restart the service.'})

    return jsonify({'type': 'success', 'message': 'Configuration updated. <b>Note</b>: You may need to <b>restart NCPA</b> for all changes to take effect.'})

# Endpoint to add a new passive check
# TODO: implement removing checks
@listener.route('/add-check/', methods=['POST'], provide_automatic_options = False)
@requires_admin_auth
def add_check():
    config = listener.config['iconfig']
    existing_checks = [x for x in get_config_items('passive checks') if x[0] not in listener.config['iconfig'].defaults()]

    cfg_file = None
    sed_cmds = []

    try:
        if environment.SYSTEM == "Windows":
            cfg_file = os.path.join('C:\\', 'Program Files', 'NCPA', 'etc', 'ncpa.cfg.d', 'example.cfg')
        else:
            cfg_file = os.path.join('/', 'usr', 'local', 'ncpa', 'etc', 'ncpa.cfg.d', 'example.cfg')

        with open(cfg_file, 'r') as configfile:
            lines = configfile.readlines()
            configfile.close()
        
        # detect if [passive checks] section exists and is uncommented so we know if we need to uncomment it
        section_exists = False
        for line in lines:
            if line.startswith("[passive checks]"):
                section_exists = True
                break

        if not section_exists:
            sed_cmds.append(f"sed -i 's/#\[passive checks\]/\[passive checks\]/' {cfg_file}")

        values_dict = {}

        hostname = None
        for (option, value) in request.form.items():
            value = sanitize_for_configparser(value)
            if option == 'host_name':
                pattern = r"^[^\r\n]+$"
                hostname = value
            elif option == 'service_name':
                for check in existing_checks:
                    if check[0].split('|')[0] == hostname and check[0].split('|')[1] == value:
                        return jsonify({'type': 'danger', 'message': 'A check with that name already exists.'})
                pattern = r"^[^\r\n]+$"
            elif option == 'check_interval':
                pattern = r"^\d*$"
            elif option == 'check_value':
                pattern = r"^[^\r\n]+$"

            if not re.match(pattern, value):
                return jsonify({'type': 'danger', 'message': 'Invalid input: %s' % option})
            else:
                values_dict[option] = value

        new_check = None
        if not values_dict['check_interval']:
            new_check = f"{values_dict['host_name']}|{values_dict['service_name']} = {values_dict['check_value']}"
            sed_cmds.append(f"sed -i '/\[passive checks\]/a {new_check}' {cfg_file}")
        else:
            new_check = f"{values_dict['host_name']}|{values_dict['service_name']}|{values_dict['check_interval']} = {values_dict['check_value']}"
            sed_cmds.append(f"sed -i '/\[passive checks\]/a {new_check}' {cfg_file}")
        # add check to running configuration so it will be displayed in the GUI before restarting NCPA
        # this does NOT make NCPA start monitoring the check until it is restarted
        new_check_parts = new_check.split('=')
        config.set('passive checks', new_check_parts[0].strip(), new_check_parts[1].strip())

        for sed_cmd in sed_cmds:                
                if environment.SYSTEM == "Windows":
                    match = re.match(r's/(.*)/(.*)/', sed_cmd)
                    if not match:
                        continue
                    pattern, replacement = match.groups()
                    # Convert sed syntax to PowerShell equivalent
                    powershell_cmd = f"Get-Content {cfg_file} | Foreach-Object {{ $_ -replace '{pattern}', '{replacement}' }} | Set-Content {cfg_file}"
                    command = ["powershell", "-Command", powershell_cmd]
                    logging.debug("add_check() - Powershell command: %s", command)
                    running_check = subprocess.run(
                        command, 
                        shell=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT
                    )
                else:
                    running_check = subprocess.run(
                        sed_cmd, 
                        shell=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setsid
                    )

                if running_check.returncode != 0:
                    logging.error("add_check() - sed_cmd failed: %s", running_check.stdout)
                    return jsonify({'type': 'danger', 'message': 'Failed to add check.'})

    except Exception as e:
        logging.exception(e)
        return jsonify({'type': 'danger', 'message': 'Failed to add check.'})

    new_check = new_check.replace('\/', '/') # unescape the slashes that were escaped for the sed command
    return jsonify({'type': 'success', 'message': 'Check added. <b>Note</b>: You may need to <b>restart NCPA</b> for all changes to take effect.', 'check': str(new_check)})

# ------------------------------
# API Endpoint
# ------------------------------


@listener.route('/api/', methods=['GET', 'POST'], provide_automatic_options = False)
@listener.route('/api/<path:accessor>', methods=['GET', 'POST'], provide_automatic_options = False)
@requires_token_or_auth
def api(accessor=''):
    """
    The function that serves up all the metrics. Given some path/to/a/metric it will
    retrieve the metric and do the necessary walking of the tree.

    :param accessor: The path/to/the/desired/metric
    :rtype: flask.Response
    """

    # Setup sane/safe arguments for actually getting the data. We take in all
    # arguments that were passed via GET/POST. If they passed a config variable
    # we clobber it, as we trust what is in the config.
    sane_args = {}
    for value in request.values:
        sane_args[value] = request.args.getlist(value)

    # Set the full requested path
    full_path = request.path

    # Set the accessor and variables
    sane_args['debug'] = request.args.get('debug', True)
    sane_args['remote_addr'] = request.remote_addr
    sane_args['accessor'] = accessor

    # Add config to sane_args
    config = listener.config['iconfig']
    sane_args['config'] = config

    # Check if we are running a check or not
    if not 'check' in sane_args:
        sane_args['check'] = request.args.get('check', False)

    # Try to get the node that was specified
    try:
        node = psapi.getter(accessor, config, full_path, request.args)
    except ValueError as exc:
        logging.exception(exc)
        return error(msg='Referencing node that does not exist: %s' % accessor)
    except IndexError as exc:
        # Hide the actual exception and just show nice output to users about changes in the API functionality
        return error(msg='Could not access location specified. Changes to API calls were made in NCPA v1.7, check documentation on making API calls.')

    # Check for default unit in the config values
    default_units = get_config_value('general', 'default_units')
    if default_units:
        if not 'units' in sane_args:
            sane_args['units'] = default_units

    if sane_args['check']:
        value = node.run_check(**sane_args)
    else:
        value = node.walk(**sane_args)

    # Generate page and add cross-domain loading
    response = Response(json.dumps(dict(value), ensure_ascii=False), mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
