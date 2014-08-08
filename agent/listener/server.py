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

__VERSION__ = '1.7.1'
__STARTED__ = datetime.datetime.now()
__INTERNAL__ = False

base_dir = os.path.dirname(sys.path[0])

#~ The following if statement is a workaround that is allowing us to run this in debug mode, rather than a hard coded
#~ location.

if os.name == 'nt':
    tmpl_dir = os.path.join(base_dir, 'listener', 'templates')
    if not os.path.isdir(tmpl_dir):
        tmpl_dir = os.path.join(base_dir, 'agent', 'listener', 'templates')

    stat_dir = os.path.join(base_dir, 'listener', 'static')
    if not os.path.isdir(stat_dir):
        stat_dir = os.path.join(base_dir, 'agent', 'listener', 'static')

    logging.info(u"Looking for templates at: %s", tmpl_dir)
    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)
    listener.jinja_loader = jinja2.FileSystemLoader(tmpl_dir)
else:
    tmpl_dir = os.path.join(base_dir, 'agent', 'listener', 'templates')
    if not os.path.isdir(tmpl_dir):
        tmpl_dir = os.path.join('/usr', 'local', 'ncpa', 'listener', 'templates')

    stat_dir = os.path.join(base_dir, 'agent', 'listener', 'static')
    if not os.path.isdir(stat_dir):
        stat_dir = os.path.join('/usr', 'local', 'ncpa', 'listener', 'static')

    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)

listener.jinja_env.line_statement_prefix = '#'


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.args.get('token', None)

        if __INTERNAL__ is True:
            # This is an internal call, we don't check. (Passive agent call.)
            pass
        elif session.get('logged', False) or token == ncpa_token:
            session['logged'] = True
        elif token is None:
            return redirect(url_for('login'))
        elif token != ncpa_token:
            return error(msg='Incorrect credentials given.')
        return f(*args, **kwargs)

    return decorated


@listener.route('/login', methods=['GET', 'POST'])
def login():
    ncpa_token = listener.config['iconfig'].get('api', 'community_string')
    if request.method == 'GET':
        token = request.args.get('token', None)
    elif request.method == 'POST':
        token = request.form.get('token', None)
    else:
        token = None

    if token is None:
        return render_template('login.html')
    if token == ncpa_token:
        session['logged'] = True
        return redirect(url_for('index'))
    if token != ncpa_token:
        return render_template('login.html', error='Token was invalid.')


@listener.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html')


@listener.route('/logout')
def logout():
    if session.get('logged', False):
        session['logged'] = False
        return render_template('login.html', info='Successfully logged out.')
    else:
        return redirect(url_for('login'))


def make_info_dict():
    now = datetime.datetime.now()
    uptime = unicode(now - __STARTED__)

    return {'agent_version': __VERSION__,
            'uptime': uptime,
            'processor': platform.uname()[5],
            'node': platform.uname()[1],
            'system': platform.uname()[0],
            'release': platform.uname()[2],
            'version': platform.uname()[3]}


@listener.route('/')
@requires_auth
def index():
    info = make_info_dict()
    try:
        return render_template('main.html', **info)
    except Exception, e:
        logging.exception(e)


@listener.route('/api-websocket/<path:accessor>')
@requires_auth
def api_websocket(accessor=None):
    """Meant for use with the websocket and API.

    Make a connection to this function, and then pass it the API
    path you wish to receive. Function returns only the raw value
    and unit in list form.

    """
    config = listener.config['iconfig']

    sane_args = dict(request.args)

    if request.environ.get('wsgi.websocket'):
        config = listener.config['iconfig']
        ws = request.environ['wsgi.websocket']
        while True:
            message = ws.receive()
            node = psapi.getter(message, config)
            prop = node.name
            val = node.walk(first=True, **sane_args)
            jval = json.dumps(val[prop])
            ws.send(jval)
    return


@listener.route('/top-base')
@requires_auth
def top_base():
    return render_template('top-base.html')


@listener.route('/top')
@requires_auth
def top():
    display = request.args.get('display', 0)
    highlight = request.args.get('highlight', None)
    warning = request.args.get('warning', 0)
    critical = request.args.get('critical', 0)
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

    return render_template('top.html',
                           **info)


@listener.route('/top-websocket/')
@requires_auth
def top_websocket():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            load = psutil.cpu_percent()
            vir_mem = psutil.virtual_memory().percent
            swap_mem = psutil.swap_memory().percent
            processes = psutil.process_iter()
            process_list = []
            for process in processes:
                process_dict = process.as_dict(['username',
                                                'get_memory_percent',
                                                'get_cpu_percent',
                                                'name',
                                                'pid'])
                process_list.append(process_dict)
            json_val = json.dumps({'load': load, 'vir': vir_mem, 'swap': swap_mem, 'process': process_list})
            ws.send(json_val)
            gevent.sleep(1)
    return


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
            except geventwebsocket.WebSocketError as exc:
                ws.close()
                logging.exception(exc)
                return
            except BaseException as exc:
                ws.close()
                logging.exception(exc)
    return


@listener.route('/tail/<path:accessor>')
@requires_auth
def tail(accessor=None):
    info = {'tail_path': accessor,
            'tail_hash': hash(accessor)}

    query_string = request.query_string
    info['query_string'] = urllib.quote(query_string)

    return render_template('tail.html',
                           **info)


@listener.route('/graph/<path:accessor>')
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

    if request.args.get('delta'):
        info['delta'] = 1
    else:
        info['delta'] = 0

    unit = request.args.get('title_unit', 'a').upper()
    if unit in ['K', 'M', 'G']:
        info['title_unit'] = unit
    else:
        info['title_unit'] = ''

    factor = 1
    if unit == 'K':
        factor = 1e3
    elif unit == 'M':
        factor = 1e6
    elif unit == 'G':
        factor = 1e9
    info['factor'] = factor

    node = psapi.getter(accessor, listener.config['iconfig'])
    prop = node.name

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


@listener.route('/testconnect/')
def testconnect():
    """
    Method meant for testing connecting with monitoring applications and wizards.

    :rtype: flask.Response
    """
    ncpa_token = listener.config['iconfig'].get('api', 'community_string')
    token = request.args.get('token', None)
    if ncpa_token != token:
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


@listener.route('/graph-picker/')
@requires_auth
def graph_picker():
    """This function renders the graph picker page, which can be though of the
    the explorer for the graphs.

    """
    return render_template('graph-picker.html')

@listener.route('/api/')
@listener.route('/api/<path:accessor>')
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
    sane_args = dict(request.args)

    # TODO: Rewrite this part, this needs to be moved to the Service/Process nodes rather than here.
    # Special cases for 'service' and 'process' to make NCPA v1.7 backwards compatible
    # with probably the most disgusting code ever written but needed to work ASAP for
    # those who had checks set up before the changes.
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
            
    try:
        config = listener.config['iconfig']
        node = psapi.getter(accessor, config)
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
    return jsonify({'value': value})
