from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session
import logging
import urllib
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


__VERSION__ = '2.0.0.a'
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

listener.jinja_env.line_statement_prefix = '#'


def make_info_dict():
    now = datetime.datetime.now()
    uptime = unicode(now - __STARTED__)
    uptime = uptime.split('.', 1)[0]

    return {'agent_version': __VERSION__,
            'uptime': uptime,
            'processor': platform.uname()[5],
            'node': platform.uname()[1],
            'system': platform.uname()[0],
            'release': platform.uname()[2],
            'version': platform.uname()[3]}


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.values.get('token', None)

        if __INTERNAL__ is True:
            # This is an internal call, we don't check. (Passive agent call.)
            pass
        elif session.get('logged', False) or token == ncpa_token:
            session['logged'] = True
        elif token is None:
            session['redirect'] = request.url
            return redirect(url_for('login'))
        elif token != ncpa_token:
            return error(msg='Incorrect credentials given.')
        return f(*args, **kwargs)

    return decorated


def requires_admin_auth(f):
    @functools.wraps(f)
    def decorated2(*args, **kwargs):
        try:
            admin_password = listener.config['iconfig'].get('listener', 'admin_password')
        except Exception as e:
            admin_password = ''

        if not admin_password:
            session['admin_logged'] = False

        return f(*args, **kwargs)

    return decorated2

@listener.route('/login', methods=['GET', 'POST'])
def login():

    # Verify authentication and redirect if we are authenticated
    if session.get('logged', False):
        return redirect(url_for('index'))

    ncpa_token = listener.config['iconfig'].get('api', 'community_string')
    message = session.get('message', None)
    url = session.get('redirect', None)
    token = request.values.get('token', None)

    template_args = { 'hide_page_links': True,
                      'message': message,
                      'url': url }

    session['message'] = None

    if token == ncpa_token:
        session['logged'] = True
        if url:
            session['redirect'] = None
            return redirect(url)
        else:
            return redirect(url_for('index'))
    elif token != ncpa_token and token is not None:
        template_args['error'] = 'Token was invalid.'

    return render_template('login.html', **template_args)


@listener.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged'] = False
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


@listener.errorhandler(403)
def error_page_not_found(e):
    template_args = {}
    if not session.get('logged', False):
        template_args = { 'hide_page_links': True }
    return render_template('errors/403.html', **template_args), 403


@listener.errorhandler(500)
def error_page_not_found(e):
    template_args = {}
    if not session.get('logged', False):
        template_args = { 'hide_page_links': True }
    return render_template('errors/500.html', **template_args), 500


# ------------------------------
# Basic GUI section
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


# Help section (just a frame for the actual help)
@listener.route('/gui/help')
@requires_auth
def help_section():
    return render_template('gui/help.html')


@listener.route('/gui/stats', methods=['GET', 'POST'])
@requires_auth
def live_stats():
    return render_template('gui/stats.html')


# ------------------------------
# Admin GUI section
# ------------------------------


@listener.route('/gui/admin', methods=['GET', 'POST'])
@requires_auth
@requires_admin_auth
def admin_config():
    tmp_args = {}
    tmp_args['config'] = listener.config['iconfig']
    return render_template('admin/config.html', **tmp_args)


# ------------------------------
# API access sections
# ------------------------------


@listener.route('/api-websocket/<path:accessor>', methods=['GET', 'POST'])
@requires_auth
def api_websocket(accessor=None):
    """Meant for use with the websocket and API.

    Make a connection to this function, and then pass it the API
    path you wish to receive. Function returns only the raw value
    and unit in list form.

    """
    sane_args = dict(request.args)
    sane_args['accessor'] = accessor

    # Refresh the root node before creating the websocket
    psapi.refresh()

    if request.environ.get('wsgi.websocket'):
        config = listener.config['iconfig']
        ws = request.environ['wsgi.websocket']
        while True:
            try:
                message = ws.receive()
                node = psapi.getter(message, config, request.path, cache=True)
                prop = node.name
                val = node.walk(first=True, **sane_args)
                jval = json.dumps(val[prop])
                ws.send(jval)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.debug(e)
                ws.close()
                break
    return ''


@listener.route('/gui/top', methods=['GET', 'POST'])
@requires_auth
def top_base():
    return render_template('gui/top.html')


@listener.route('/top', methods=['GET', 'POST'])
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


@listener.route('/top-websocket/')
@requires_auth
def top_websocket():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            load = psutil.cpu_percent()
            vir_mem = psutil.virtual_memory().percent
            swap_mem = psutil.swap_memory().percent
            processes = processes.get_process_dict()

            process_list = []

            for process in processes:
                process_list.append(process)

            json_val = json.dumps({'load': load, 'vir': vir_mem, 'swap': swap_mem, 'process': process_list})
            try:
                ws.send(json_val)
                gevent.sleep(1)
            except Exception as e:
                # Socket was probably closed by the browser changing pages
                logging.debug(e)
                ws.close()
                break
    return ''


@listener.route('/tail-websocket/<path:accessor>')
@requires_auth
def tail_websocket(accessor=None):
    if request.environ.get('wsgi.websocket'):
        last_ts = datetime.datetime.now()
        ws = request.environ['wsgi.websocket']
        while True:
            try:
                last_ts, logs = listener.tail_method(last_ts=last_ts, **request.args)

                if logs:
                    json_log = json.dumps(logs)
                    ws.send(json_log)

                gevent.sleep(2)
            except Exception as e:
                ws.close()
                logging.exception(e)
                return
    return


@listener.route('/tail/<path:accessor>', methods=['GET', 'POST'])
@requires_auth
def tail(accessor=None):
    info = {'tail_path': accessor,
            'tail_hash': hash(accessor)}

    query_string = request.query_string
    info['query_string'] = urllib.quote(query_string)

    return render_template('tail.html',
                           **info)


@listener.route('/graph/<path:accessor>', methods=['GET', 'POST'])
@requires_auth
def graph(accessor=None):
    """
    Accessor method for fetching the HTML for the real-time graphing.

    :param accessor: The API path to be accessed (see /api)
    :type accessor: unicode
    :rtype: flask.Response
    """
    info = {'graph_path': accessor,
            'graph_hash': hash(accessor)}

    # Refresh the root node before creating the websocket
    psapi.refresh()

    node = psapi.getter(accessor, listener.config['iconfig'], request.path, cache=True)
    prop = node.name

    if request.values.get('delta'):
        info['delta'] = 1
    else:
        info['delta'] = 0

    info['graph_prop'] = prop
    query_string = request.query_string
    info['query_string'] = urllib.quote(query_string)

    return render_template('graph.html',
                           **info)


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


@listener.route('/gui/graphs', methods=['GET', 'POST'])
@requires_auth
def graph_picker():
    """
    This function renders the graph picker page, which can be though of the
    the explorer for the graphs.

    """
    return render_template('gui/graphs.html')


@listener.route('/gui/api', methods=['GET', 'POST'])
@requires_auth
def view_api():
    info = make_info_dict()
    return render_template('gui/api.html', **info)


@listener.route('/api/', methods=['GET', 'POST'])
@listener.route('/api/<path:accessor>', methods=['GET', 'POST'])
@requires_auth
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

    #
    # As of version 2.0.0 there are now 3 different paths that are backwards
    # compatible using this section. After looking into it further the location
    # of this should be around here. Changing the incoming request is the only
    # way to make something happen without updating the way the API looks/returns.
    # You can think of these as aliases. Below explains the aliases and when they
    # will be removed. As of 2.0.0 they are deprecated. Will be removed in 2.1.0.
    #
    # Deprecated Aliases:
    #
    #   Aliases (up to 1.8.1)     || Location (2.0.0)
    #   ---------------------------------------------------------------------
    #   api/service/<servicename> -> api/services?service=<servicename>
    #   api/process/<processname> -> api/processes?name=<processname>
    #   api/agent/plugin/<plugin> -> api/plugins/<plugin>
    #
    path = [re.sub('%2f', '/', x, flags=re.I) for x in accessor.split('/') if x]
    if len(path) > 0 and path[0] == 'api':
        path = path[1:]
    if len(path) > 0:
        node_name, rest_path = path[0], path[1:]

        if node_name == "service":
            accessor = "services"
            if len(rest_path) > 0:
                sane_args['service'] = [rest_path[0]]
                if len(rest_path) == 2:
                    sane_args['status'] = [rest_path[1]]
                    sane_args['check'] = True;
        elif node_name == "process":
            accessor = "processes"
            if len(rest_path) > 0:
                sane_args['name'] = [rest_path[0]]
                if len(rest_path) == 2:
                    if rest_path[1] == "count":
                        sane_args['check'] = True
        elif node_name == "agent":
            accessor = "plugins"
            if 'plugin' in rest_path[0] and len(rest_path) > 1:
                accessor = "plugins/" + rest_path[1]

    # Set the full requested path
    full_path = request.path

    try:
        config = listener.config['iconfig']
        node = psapi.getter(accessor, config, full_path)
    except ValueError as exc:
        logging.exception(exc)
        return error(msg='Referencing node that does not exist: %s' % accessor)
    except IndexError as exc:
        # Hide the actual exception and just show nice output to users about changes in the API functionality
        return error(msg='Could not access location specified. Changes to API calls were made in NCPA v1.7, check documentation on making API calls.')

    # Set the accessor and variables
    sane_args['accessor'] = accessor
    sane_args['config'] = config
    if not 'check' in sane_args:
        sane_args['check'] = request.args.get('check', False);

    if sane_args['check']:
        value = node.run_check(**sane_args)
    else:
        value = node.walk(**sane_args)

    return Response(json.dumps(dict(value),
                    indent=None if request.is_xhr else 4),
                    mimetype='application/json')
