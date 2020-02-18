# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session, make_response, abort
import logging
import urllib
import urlparse
import os
import sys
import platform
import requests
import psapi
import functools
import jinja2
import datetime
import json
import re
import psutil
import gevent
import geventwebsocket
import processes
import database
import math
import ipaddress


__VERSION__ = '2.2.1'
__STARTED__ = datetime.datetime.now()
__INTERNAL__ = False

base_dir = os.path.dirname(sys.path[0])


# The following if statement is a workaround that is allowing us to run this
# in debug mode, rather than a hard coded location.

tmpl_dir = os.path.join(base_dir, 'listener', 'templates')
if not os.path.isdir(tmpl_dir):
    tmpl_dir = os.path.join(base_dir, 'agent', 'listener', 'templates')

stat_dir = os.path.join(base_dir, 'listener', 'static')
if not os.path.isdir(stat_dir):
    stat_dir = os.path.join(base_dir, 'agent', 'listener', 'static')

if os.name == 'nt':
    logging.info(u"Looking for templates at: %s", tmpl_dir)
    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)
    listener.jinja_loader = jinja2.FileSystemLoader(tmpl_dir)
else:
    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)


# Set some settings for Flask
listener.jinja_env.line_statement_prefix = '#'
listener.url_map.strict_slashes = False


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
    uptime = unicode(now - __STARTED__)
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
             'processor': proc_type,
             'node': uname[1],
             'system': uname[0],
             'release': uname[2],
             'version': uname[3],
             'total_checks': format(total_checks, ",d"),
             'check_logging_time': check_logging_time }


# ------------------------------
# Authentication Wrappers
# ------------------------------


@listener.before_request
def before_request():
    allowed_hosts = get_config_value('listener', 'allowed_hosts')
    if allowed_hosts and __INTERNAL__ is False:
        if request.remote_addr:
            ipaddr = ipaddress.ip_address(unicode(request.remote_addr))
            allowed_networks = [ipaddress.ip_network(unicode(_network.strip())) for _network in allowed_hosts.split(',')]
            allowed = [ipaddr in _network for _network in allowed_networks]
            if True not in allowed:
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

        # This is an internal call, we don't check
        if __INTERNAL__ is True:
            pass
        elif session.get('logged', False) or token == ncpa_token:
            pass
        elif token is None:
            session['redirect'] = request.url
            return redirect(url_for('login'))
        elif token != ncpa_token:
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


@listener.route('/login', methods=['GET', 'POST'])
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

    template_args = { 'hide_page_links': True,
                      'message': message,
                      'url': url,
                      'has_admin_password': has_admin_password,
                      'admin_auth_only': admin_auth_only }

    session['message'] = None

    # Do actual authentication check
    if token == ncpa_token and not admin_auth_only:
        session['logged'] = True
    elif token == admin_password and admin_password is not None:
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
            if token != ncpa_token or token != admin_password:
                template_args['error'] = 'Invalid token or password.'
        else:
            if token == ncpa_token:
                template_args['error'] = 'Admin authentication only.'
            else:
                template_args['error'] = 'Invalid password.'

    return render_template('login.html', **template_args)


@listener.route('/gui/admin/login', methods=['GET', 'POST'])
@requires_auth
def admin_login():

    # Verify authentication and redirect if we are authenticated
    if session.get('admin_logged', False):
        return redirect(url_for('admin'))

    # Admin password
    admin_password = get_config_value('listener', 'admin_password', None)

    message = session.get('message', None)
    password = request.values.get('password', None)
    template_args = { 'hide_page_links': False,
                      'message': message }

    session['message'] = None

    if password == admin_password and admin_password is not None:
        session['admin_logged'] = True
        return redirect(url_for('admin'))
    elif password is not None:
        template_args['error'] = 'Password was invalid.'

    return render_template('admin/login.html', **template_args)


@listener.route('/logout', methods=['GET', 'POST'])
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


@listener.route('/')
@requires_auth
def index():
    return redirect(url_for('gui_index'))


@listener.route('/gui/')
@requires_auth
def gui_index():
    info = make_info_dict()
    try:
        return render_template('gui/dashboard.html', **info)
    except Exception, e:
        logging.exception(e)


@listener.route('/gui/checks')
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
        link_vals += '&ctype=' + str(status)
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


@listener.route('/gui/stats', methods=['GET', 'POST'])
@requires_auth
def live_stats():
    return render_template('gui/stats.html')


@listener.route('/gui/top', methods=['GET', 'POST'])
@requires_auth
def top_base():
    return render_template('gui/top.html')


@listener.route('/gui/tail', methods=['GET', 'POST'])
@requires_auth
def tail_base():
    return render_template('gui/tail.html')


# This function renders the graph picker page, which can be though of the
# the explorer for the graphs.
@listener.route('/gui/graphs', methods=['GET', 'POST'])
@requires_auth
def graph_picker():
    return render_template('gui/graphs.html')


@listener.route('/gui/api', methods=['GET', 'POST'])
@requires_auth
def view_api():
    info = make_info_dict()
    return render_template('gui/api.html', **info)


# Help section (just a frame for the actual help)
@listener.route('/gui/help')
@requires_auth
def help_section():
    return render_template('gui/help.html')


# ------------------------------
# Admin GUI section
# ------------------------------


@listener.route('/gui/admin', methods=['GET', 'POST'])
@listener.route('/gui/admin/', methods=['GET', 'POST'])
@requires_admin_auth
def admin():
    tmp_args = {}
    tmp_args['config'] = listener.config['iconfig']
    return render_template('admin/index.html', **tmp_args)


@listener.route('/gui/admin/global', methods=['GET', 'POST'])
@requires_admin_auth
def admin_global():
    tmp_args = { 'no_nav': True,
                 'check_logging': int(get_config_value('general', 'check_logging', 1)),
                 'check_logging_time': get_config_value('general', 'check_logging_time', 30) }

    # Check session for flash message
    flash_msg_text = session.get('flash_msg_text', '')
    if flash_msg_text is not '':
        flash_msg_type = session.get('flash_msg_type', 'info')
        tmp_args['flash_msg_text'] = flash_msg_text
        tmp_args['flash_msg_type'] = flash_msg_type
        tmp_args['flash_msg'] = True
        session['flash_msg_text'] = ''

    return render_template('admin/global.html', **tmp_args)


@listener.route('/gui/admin/listener', methods=['GET', 'POST'])
@requires_admin_auth
def admin_listener_config():
    tmp_args = { 'no_nav': True,
                 'ip': get_config_value('listener', 'ip', '::'),
                 'port': get_config_value('listener', 'port', '5693'),
                 'uid': get_config_value('listener', 'uid', 'nagios'),
                 'gid': get_config_value('listener', 'gid', 'nagios'),
                 'ssl_version': get_config_value('listener', 'ssl_version', 'TLSv1_2'),
                 'certificate': get_config_value('listener', 'certificate', 'adhoc'),
                 'pidfile': get_config_value('listener', 'pidfile', 'var/run/ncpa_listener.pid'),
                 'loglevel': get_config_value('listener', 'loglevel', 'info'),
                 'logfile': get_config_value('listener', 'logfile', 'var/log/ncpa_listener.log'),
                 'logmaxmb': get_config_value('listener', 'logmaxmb', '5'),
                 'logbackups': get_config_value('listener', 'logbackups', '5'),
                 'admin_gui_access': int(get_config_value('listener', 'admin_gui_access', 1)),
                 'admin_auth_only': int(get_config_value('listener', 'admin_auth_only', 0)),
                 'delay_start': get_config_value('listener', 'delay_start', '0') }

    # Todo: add form actions when submitted

    return render_template('admin/listener.html', **tmp_args)


@listener.route('/gui/admin/passive', methods=['GET', 'POST'])
@requires_admin_auth
def admin_passive_config():
    handlers = get_config_value('passive', 'handlers', None)
    if handlers is None:
        handlers = []
    tmp_args = { 'no_nav': True,
                 'handlers': handlers,
                 'uid': get_config_value('passive', 'uid', 'nagios'),
                 'gid': get_config_value('passive', 'gid', 'nagios'),
                 'sleep': get_config_value('passive', 'sleep', '300'),
                 'pidfile': get_config_value('passive', 'pidfile', 'var/run/ncpa_listener.pid'),
                 'loglevel': get_config_value('passive', 'loglevel', 'info'),
                 'logfile': get_config_value('passive', 'logfile', 'var/log/ncpa_listener.log'),
                 'logmaxmb': get_config_value('passive', 'logmaxmb', '5'),
                 'logbackups': get_config_value('passive', 'logbackups', '5'),
                 'delay_start': get_config_value('passive', 'delay_start', '0') }

    # Todo: add form actions when submitted

    return render_template('admin/passive.html', **tmp_args)


@listener.route('/gui/admin/nrdp', methods=['GET', 'POST'])
@requires_admin_auth
def admin_nrdp_config():
    handlers = get_config_value('passive', 'handlers', None)
    if handlers is None:
        handlers = []
    tmp_args = { 'no_nav': True,
                 'handlers': handlers,
                 'nrdp_url': get_config_value('nrdp', 'parent', ''),
                 'nrdp_token': get_config_value('nrdp', 'token', ''),
                 'hostname': get_config_value('nrdp', 'hostname', 'NCPA') }
    return render_template('admin/nrdp.html', **tmp_args)


@listener.route('/gui/admin/plugin-directives', methods=['GET', 'POST'])
@requires_admin_auth
def admin_plugin_config():
    try:
        directives = [x for x in get_config_items('plugin directives') if x[0] not in listener.config['iconfig'].defaults()]
    except Exception as e:
        directives = []
    tmp_args = { 'no_nav': True,
                 'plugin_path': get_config_value('plugin directives', 'plugin_path', 'plugins/'),
                 'plugin_timeout': get_config_value('plugin directives', 'plugin_timeout', '60'),
                 'directives': directives }
    return render_template('admin/plugins.html', **tmp_args)


@listener.route('/gui/admin/passive-checks', methods=['GET', 'POST'])
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
@listener.route('/gui/admin/clear-check-log', methods=['GET', 'POST'])
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


@listener.route('/ws/api/<path:accessor>')
@requires_token_or_auth
def api_websocket(accessor=None):
    """Meant for use with the websocket and API.

    Make a connection to this function, and then pass it the API
    path you wish to receive. Function returns only the raw value
    and unit in list form.

    """
    sane_args = dict(request.args)
    sane_args['accessor'] = accessor

    config = listener.config['iconfig']

    encoding = sys.stdin.encoding
    if encoding is None:
        encoding = sys.getdefaultencoding()

    # Refresh the root node before creating the websocket
    psapi.refresh(config)

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            try:
                message = ws.receive()
                node = psapi.getter(message, config, request.path, request.args)
                prop = node.name
                val = node.walk(first=True, **sane_args)
                jval = json.dumps(val[prop], encoding=encoding)
                ws.send(jval)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.debug(e)
                ws.close()
                break
    return ''


@listener.route('/ws/top')
@requires_token_or_auth
def top_websocket():

    encoding = sys.stdin.encoding
    if encoding is None:
        encoding = sys.getdefaultencoding()

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
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

            
            json_val = json.dumps({'load': load, 'vir': vir_mem, 'swap': swap_mem, 'process': process_list},
                                  encoding=encoding)

            try:
                ws.send(json_val)
                gevent.sleep(1)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.debug(e)
                ws.close()
                break
    return ''


@listener.route('/ws/tail')
@requires_token_or_auth
def tail_websocket():

    encoding = sys.stdin.encoding
    if encoding is None:
        encoding = sys.getdefaultencoding()

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        last_ts = datetime.datetime.now()
        while True:
            try:
                last_ts, logs = listener.tail_method(last_ts=last_ts, **request.args)

                if logs:
                    json_log = json.dumps(logs, encoding=encoding)
                    ws.send(json_log)

                gevent.sleep(5)
            except Exception as e:
                logging.debug(e)
                ws.close()
                break
    return ''


# ------------------------------
# Internal (loaded internally)
# ------------------------------


@listener.route('/top')
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


@listener.route('/tail')
@requires_token_or_auth
def tail(accessor=None):
    info = { }

    query_string = request.query_string
    info['query_string'] = urllib.quote(query_string)

    return render_template('tail.html', **info)


@listener.route('/graph/<path:accessor>', methods=['GET', 'POST'])
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
    info['query_string'] = urllib.quote(query_string)

    url = urlparse.urlparse(request.url)
    info['load_from'] = url.scheme + '://' + url.netloc
    info['load_websocket'] = url.netloc

    # Generate page and add cross-domain loading
    response = make_response(render_template('graph.html', **info))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


# ------------------------------
# Misc Endpoints
# ------------------------------


@listener.route('/error/')
@listener.route('/error/<msg>')
def error(msg=None):
    if not msg:
        msg = 'Error occurred during processing request.'
    return jsonify(error=msg)


@listener.route('/testconnect/', methods=['GET', 'POST'])
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


@listener.route('/nrdp/', methods=['GET', 'POST'])
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
        return error(msg=unicode(exc))


# ------------------------------
# API Endpoint
# ------------------------------


@listener.route('/api/', methods=['GET', 'POST'])
@listener.route('/api/<path:accessor>', methods=['GET', 'POST'])
@requires_token_or_auth
def api(accessor=''):
    """
    The function that serves up all the metrics. Given some path/to/a/metric it will
    retrieve the metric and do the necessary walking of the tree.

    :param accessor: The path/to/the/desired/metric
    :type accessor: unicode
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
    sane_args['debug'] = request.args.get('debug', False)
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
    json_data = json.dumps(dict(value), ensure_ascii=False, indent=None if request.is_xhr else 4)
    response = Response(json_data, mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
