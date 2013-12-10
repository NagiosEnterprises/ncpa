#!/usr/bin/env python

from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session
import logging
import urllib
import ConfigParser
import os
import sys
import platform
import requests
import psapi
import pluginapi
import functools
import jinja2
import jinja2.ext
import datetime
import re

__VERSION__ = 1.2
__STARTED__ = datetime.datetime.now()


base_dir = os.path.dirname(sys.path[0])

#~ The following if statement is a workaround that is allowing us to run this in debug mode, rather than a hard coded
#~ location.

if os.name == 'nt':
    tmpl_dir = os.path.join(base_dir, 'listener', 'templates')
    if(not os.path.isdir(tmpl_dir)):
        tmpl_dir = os.path.join(base_dir, 'agent', 'listener', 'templates')

    stat_dir = os.path.join(base_dir, 'listener', 'static')
    if(not os.path.isdir(stat_dir)):
        stat_dir = os.path.join(base_dir, 'agent', 'listener', 'static')

    logging.info("Looking for templates at: %s" % tmpl_dir)
    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)
    listener.jinja_loader = jinja2.FileSystemLoader(tmpl_dir)
else:
    tmpl_dir = os.path.join(base_dir, 'agent', 'listener', 'templates')
    if(not os.path.isdir(tmpl_dir)):
        tmpl_dir = os.path.join('/usr', 'local', 'ncpa', 'listener', 'templates')

    stat_dir = os.path.join(base_dir, 'agent', 'listener', 'static')
    if(not os.path.isdir(stat_dir)):
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
    myjson = api('disk/logical', raw=True)
    disks = [{'safe': re.sub(r'[^a-zA-Z0-9]', '', x),
              'raw': x} for x in myjson.get('logical').keys()]
    myjson = api('interface/', raw=True)
    interfaces = [{'safe': re.sub(r'[^a-zA-Z0-9]', '', x),
                   'raw': x} for x in myjson.get('interface').keys()]
    myjson = api('cpu/count', raw=True)
    cpucount = myjson.get('count', 0)

    return render_template('dashboard.html',
                           disks=disks,
                           interfaces=interfaces,
                           cpucount=cpucount)


@listener.route('/navigator')
@requires_auth
def navigator():
    return render_template('navigator.html')


@listener.route('/config', methods=['GET', 'POST'])
@requires_auth
def config():
    if request.method == 'POST':
        new_config = save_config(request.form, listener.config_filename)
        listener.config['iconfig'] = new_config
        config_fp = open(listener.config_filename, 'w')
        new_config.write(config_fp)
        config_fp.close()

    section = request.args.get('section')
    if section:
        try:
            return jsonify(**listener.config['iconfig'].__dict__['_sections'][section])
        except Exception, e:
            logging.exception(e)
    return render_template('config.html', **{'config': listener.config['iconfig'].__dict__['_sections']})


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
    uptime = str(now - __STARTED__)

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
        return error(msg=str(e))


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
        return error(msg='Error running plugin.')
    return jsonify({'value': response})


@listener.route('/api/')
@listener.route('/api/<path:accessor>')
@requires_auth
def api(accessor='', raw=False):
    if request.args.get('check'):
        url = accessor + '?' + urllib.urlencode(request.args)
        return jsonify({'value': internal_api(url, listener.config['iconfig'])})
    try:
        response = psapi.getter(accessor, listener.config['iconfig'].get('plugin directives', 'plugin_path'))
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
        except IndexError as e:
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


def save_config(dconfig, writeto):
    viv = vivicate_dict(dconfig)
    config = ConfigParser.ConfigParser()

    #~ Do the normal sections
    for s in ['listener', 'passive', 'nrdp', 'nrds', 'api']:
        config.add_section(s)
        for t in viv[s]:
            config.set(s, t, viv[s][t])

    #~ Do the plugin directives
    directives = viv['directives']
    config.add_section('plugin directives')

    config.set('plugin directives', 'plugin_path', directives['plugin_path'])
    del directives['plugin_path']

    dkeys = [x for x in directives.keys() if 'suffix|' in x]
    for x in dkeys:
        _, suffix = x.split('|')
        config.set('plugin directives', suffix, directives['exec|' + suffix])

    pchecks = viv['passivecheck']
    config.add_section('passive checks')

    pkeys = [x for x in pchecks.keys() if 'name|' in x]
    for x in pkeys:
        _, pid = x.split('name|', 1)
        config.set('passive checks', pchecks[x], pchecks['exec|' + pid])

    return config


def vivicate_dict(d, delimiter='|'):
    result = {}
    for x in d:
        if delimiter in x:
            key, value = x.split(delimiter, 1)
            if key in result:
                result[key][value] = d[x]
            else:
                result[key] = {value: d[x]}
        else:
            result[x] = d[x]

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
        logging.debug('Plugin result!')
        plugin_name = plugin_result.group(3)
        plugin_args = plugin_result.group(5)
    elif accessor_result:
        logging.debug('Accessor result!')
        accessor_name = accessor_result.group(2)
        accessor_args = accessor_result.group(3)
    return accessor_name, accessor_args, plugin_name, plugin_args
