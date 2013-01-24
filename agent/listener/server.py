#!/usr/bin/env python

from flask import Flask, render_template, redirect, request, url_for, jsonify, Response
import commands
import logging
import urllib
import ConfigParser
import os
import sys
import processor
import requests
import json
import psapi
import pluginapi
import functools

listener = Flask(__name__)
listener.debug=True
config = None

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        ncpa_token = listener.config['iconfig'].get('api', 'community_string')
        token = request.args.get('token', None)
        if token != ncpa_token:
            return redirect(url_for('error', msg='Incorrect credentials given.'))
        return f(*args, **kwargs)
    return decorated

@listener.route('/')
@requires_auth
def index():
    try:
        return render_template('main.html')
    except Exception, e:
        logging.exception(e)

@listener.route('/error/')
@listener.route('/error/<msg>')
def error(msg=None):
    if not msg:
        msg = 'Error occurred during processing request.'
    return jsonify(error=msg)

@listener.route('/check/')
@requires_auth
def check():
    try:
        result = processor.check_metric(request.args, listener.config['iconfig'])
        return jsonify(**result)
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))

@listener.route('/nrdp/', methods=['GET', 'POST'])
def nrdp():
    try:
        forward_to = listener.config['iconfig'].get('nrdp', 'parent')
        logging.warning(forward_to)
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
def api(accessor=''):
    try:
        response = psapi.getter(accessor)
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg='Referencing node that does not exist.'))
    return jsonify({'value' : response})

@listener.route('/processes/')
@requires_auth
def processes():
    procs = json.loads(commands.enumerate_processes(request=request))
    header = procs.get('header', [])
    procs = procs.get('procs', [])
    return render_template('processes.html', header=header, procs=procs)

@listener.route('/command/')
@requires_auth
def command():
    logging.debug('Accessing command...')
    command = request.args.get('command', '')
    try:
        logging.debug('Getting function')
        generic = getattr(commands, command)
    except Exception, e:
        logging.debug('We failed.')
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))
    return generic(request=request)

if __name__ == "__main__":
    listener.run('0.0.0.0', 5692)
    url_for('static', filename='chinook.css')
    url_for('static', filename='jquery-1.8.3.min.js')
    url_for('static', filename='jquery-ui.css')
    url_for('static', filename='jquery-ui.js')
