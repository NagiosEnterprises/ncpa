from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session
import logging
import urllib
import os
import sys
import platform
import requests
import psapi
import pluginapi
import functools
import jinja2
import datetime
import json
import re


__VERSION__ = 1.6
__STARTED__ = datetime.datetime.now()


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

    logging.info(u"Looking for templates at: %s" % tmpl_dir)
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

        if session.get('logged', False):
            pass
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
    my_json = api('disk/logical', raw=True)
    disks = [{'safe': re.sub(ur'[^a-zA-Z0-9]', '', x),
              'raw': x} for x in list(my_json.get('logical').keys())]
    my_json = api('interface/', raw=True)
    interfaces = [{'safe': re.sub(ur'[^a-zA-Z0-9]', '', x),
                   'raw': x} for x in list(my_json.get('interface').keys())]
    my_json = api('cpu/count', raw=True)
    cpu_count = my_json.get('count', 0)

    return render_template('dashboard.html',
                           disks=disks,
                           interfaces=interfaces,
                           cpucount=cpu_count)


@listener.route('/logout')
def logout():
    if session.get('logged', False):
        session['logged'] = False
        return render_template('login.html', info='Successfully logged out.')
    else:
        return redirect(url_for('login'))


def make_info_dict():
    global __VERSION__
    global __STARTED__

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
def api_websocket(accessor=None):
    """Meant for use with the websocket and API.

    Make a connection to this function, and then pass it the API
    path you wish to receive. Function returns only the raw value
    and unit in list form.

    """
    try:
        prop = accessor.rsplit('/', 1)[-1]
    except (IndexError, KeyError):
        prop = None

    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']
        while True:
            message = ws.receive()
            val = psapi.getter(message)
            jval = json.dumps(val[prop])
            ws.send(jval)
    return


@listener.route('/graph/<path:accessor>')
def graph(accessor=None):
    info = {'graph_path': accessor,
            'graph_hash': hash(accessor)}

    if request.args.get('delta'):
        info['delta'] = 1
    else:
        info['delta'] = 0

    unit = request.args.get('unit', 'a').upper()
    if unit in ['K', 'M', 'G']:
        info['unit'] = unit
    else:
        info['unit'] = ''

    factor = 1
    if unit == 'K':
        factor = 1e3
    elif unit == 'M':
        factor = 1e6
    elif unit == 'G':
        factor = 1e9
    info['factor'] = factor

    try:
        prop = accessor.rsplit('/', 1)[-1]
    except (IndexError, KeyError):
        prop = None

    info['graph_prop'] = prop

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
    ncpa_token = listener.config['iconfig'].get('api', 'community_string')
    token = request.args.get('token', None)
    if ncpa_token != token:
        return jsonify({'error': 'Bad token.'})
    else:
        return jsonify({'value': 'Success.'})


@listener.route('/nrdp/', methods=['GET', 'POST'])
def nrdp():
    try:
        forward_to = listener.config['iconfig'].get('nrdp', 'parent')
        if request.method == 'get':
            response = requests.get(forward_to, params=request.args)
        else:
            response = requests.post(forward_to, params=request.form)
        resp = Response(response.content, 200, mimetype=response.headers['content-type'])
        return resp
    except Exception, e:
        logging.exception(e)
        return error(msg=unicode(e))


@listener.route('/api/agent/plugin/<plugin_name>/')
@listener.route('/api/agent/plugin/<plugin_name>/<path:plugin_args>')
@requires_auth
def plugin_api(plugin_name=None, plugin_args=None):
    config = listener.config['iconfig']
    if plugin_args:
        logging.info(plugin_args)
        plugin_args = [urllib.unquote(x) for x in plugin_args.split('/')]
    try:
        response = pluginapi.execute_plugin(plugin_name, plugin_args, config)
    except Exception, e:
        logging.exception(e)
        return error(msg='Error running plugin: %s' % unicode(e))
    return jsonify({'value': response})


@listener.route('/api/')
@listener.route('/api/<path:accessor>')
@requires_auth
def api(accessor='', raw=False):
    if request.args.get('check'):
        url = accessor + '?' + urllib.urlencode(request.args)
        return jsonify({'value': internal_api(url, listener.config['iconfig'])})
    try:
        plugin_path = listener.config['iconfig'].get('plugin directives', 'plugin_path')
        response = psapi.getter(accessor, plugin_path)
    except Exception, e:
        logging.exception(e)
        return error(msg='Referencing node that does not exist.')
    if raw:
        return response
    else:
        return jsonify({'value': response})


def internal_api(accessor=None, listener_config=None):
    logging.debug('Accessing internal API with accessor %s', accessor)
    accessor_name, accessor_args, plugin_name, plugin_args = parse_internal_input(accessor)
    if accessor_name:
        try:
            logging.debug('Accessing internal API with accessor %s', accessor_name)
            acc_response = psapi.getter(accessor_name)
        except IndexError, e:
            logging.exception(e)
            logging.warning("User request invalid node: %s" % accessor_name)
            result = {'returncode': 3, 'stdout': 'Invalid entry specified. No known node by %s' % accessor_name}
        else:
            result = pluginapi.make_plugin_response_from_accessor(acc_response, accessor_args)
    elif plugin_name:
        result = pluginapi.execute_plugin(plugin_name, plugin_args, listener_config)
    else:
        result = {'stdout': 'ERROR: Non-node value requested. Requested a tree.',
                  'returncode': 3}
    return result


def parse_internal_input(accessor):
    ACCESSOR_REGEX = re.compile('(/api)?/?([^?]+)\??(.*)')
    PLUGIN_REGEX = re.compile('(/api)?(/?agent/)?plugin/([^/]+)(/(.*))?')

    accessor_name = None
    accessor_args = None
    plugin_name = None
    plugin_args = None

    plugin_result = PLUGIN_REGEX.match(accessor)
    accessor_result = ACCESSOR_REGEX.match(accessor)

    if plugin_result:
        plugin_name = plugin_result.group(3)
        plugin_args = plugin_result.group(5)
    elif accessor_result:
        accessor_name = accessor_result.group(2)
        accessor_args = accessor_result.group(3)
    return accessor_name, accessor_args, plugin_name, plugin_args
