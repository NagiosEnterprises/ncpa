#!/usr/bin/env python

from flask import Flask, render_template, redirect, request, url_for, jsonify, Response
import commands
import logging
import urllib
import ConfigParser
import os
import processor
import requests

listener = Flask(__name__)
listener.debug=True
config = None

@listener.route('/')
def index():
    try:
        return render_template('main.html')
    except Exception, e:
        logging.exception(e)

@listener.route('/error')
def error(msg=None):
    if not msg:
        msg = 'Error occurred during processing request.'
    return jsonify(error=msg)

@listener.route('/check')
def check():
    try:
        result = processor.check_metric(request.args, listener.config['iconfig'])
        return jsonify(**result)
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))

@listener.route('/nrdp')
def nrdp():
    try:
        forward_to = listener.config['iconfig'].get('nrdp', 'parent')
        logging.warning(forward_to)
        if request.method == 'get':
            response = requests.get(forward_to, params=request.args)
        else:
            response = requests.post(forward_to, params=request.args)
        resp = Response(response.content, 200, mimetype=response.headers['content-type'])
        return resp
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))

@listener.route('/config')
def config():
    try:
        return render_template('config.html', **{'config' : listener.config['iconfig'].__dict__['_sections']})
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))
    

@listener.route('/command')
def command():
    command = request.args.get('command', '')
    try:
        generic = getattr(commands, command)
    except Exception, e:
        logging.exception(e)
        return redirect(url_for('error', msg=str(e)))
    return generic(request)

if __name__ == "__main__":
    listener.run('0.0.0.0', 5692)
    url_for('static', filename='chinook.css')
    url_for('static', filename='jquery-1.8.3.min.js')
    url_for('static', filename='jquery-ui.css')
    url_for('static', filename='jquery-ui.js')
