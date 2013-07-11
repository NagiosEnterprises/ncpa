#!/usr/bin/env python

from flask import Flask, render_template, redirect, request, url_for, jsonify, Response, session
import commands
import logging
import urllib
import re
import ConfigParser
import os
import sys
import platform
import requests
import json
import psapi
import pluginapi
import functools
import jinja2.ext
import unittest
import datetime

__VERSION__ = 1.0
__STARTED__ = datetime.datetime.now()

if os.name == 'nt': 
    base_dir = os.path.dirname(sys.path[0])
    tmpl_dir = os.path.join(base_dir, 'listener', 'templates')
    stat_dir = os.path.join(base_dir, 'listener', 'static')
    listener = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)
else:
    listener = Flask(__name__)

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.args.get('token', None)
        
        if session.get('logged', False):
            pass
        elif token == None:
            return redirect(url_for('login'))
        elif token != ncpa_token:
            return redirect(url_for('error', msg='Incorrect credentials given.'))
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
    
    if token == None:
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
    disks = myjson.get('logical').keys()
    myjson = api('interface/', raw=True)
    interfaces = myjson.get('interface').keys()
    return render_template('dashboard.html', disks=disks, interfaces=interfaces)

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
    
    return {'version': __VERSION__,
            'uptime': uptime,
            'processor': platform.uname()[5],
            'node': platform.uname()[1],
            'system': platform.uname()[0],
            'release': platform.uname()[2],
            'version': platform.uname()[3] }

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
        return redirect(url_for('error', msg=str(e)))

@listener.route('/config/')
@requires_auth
def config():
    try:
        return render_template('config.html', **{'config' : listener.config['iconfig'].__dict__['_sections']})
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))

@listener.route('/api/agent/plugin/<plugin_name>/')
@listener.route('/api/agent/plugin/<plugin_name>/<path:plugin_args>')
@requires_auth
def plugin_api(plugin_name=None, plugin_args=None):
    config = listener.config['iconfig']
    try:
        response = pluginapi.execute_plugin(plugin_name, plugin_args, config)
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg='Error running plugin.'))
    return jsonify({'value' : response})

@listener.route('/api/')
@listener.route('/api/<path:accessor>')
@requires_auth
def api(accessor='', raw=False):
    if request.args.get('check'):
        url = accessor + '?' + urllib.urlencode(request.args)
        return jsonify({'value' : internal_api(url, listener.config['iconfig'])})
    try:
        response = psapi.getter(accessor, listener.config['iconfig'].get('plugin directives', 'plugin_path'))
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg='Referencing node that does not exist.'))
    if raw:
        return response
    else:
        return jsonify({'value' : response})

def internal_api(accessor=None, config=None):
    logging.debug('Accessing internal API with accessor %s', accessor)
    accessor_name, accessor_args, plugin_name, plugin_args =  parse_internal_input(accessor)
    if accessor_name:
        try:
            logging.debug('Accessing internal API with accessor %s', accessor_name)
            acc_response = psapi.getter(accessor_name)
        except IndexError as e:
            logging.exception(e)
            logging.warning("User request invalid node: %s" % accessor_name)
            result = { 'returncode' : 3, 'stdout' : 'Invalid entry specified. No known node by %s' % accessor_name}
        else:
            result = pluginapi.make_plugin_response_from_accessor(acc_response, accessor_args)
    elif plugin_name:
        result = pluginapi.execute_plugin(plugin_name, plugin_args, config)
    else:
        result = {'stdout': 'ERROR: Non-node value requested. Requested a tree.', 'returncode': 3}
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
