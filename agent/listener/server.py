#!/usr/bin/env python

from flask import Flask, render_template, redirect, request, url_for
import commands
import logging
import json
import urllib
import ConfigParser
import os

listener = Flask(__name__)
listener.debug=False
config = None

@listener.route('/')
def index():
    try:
        return render_template('main.html')
    except Exception, e:
        logging.exception(e)

@listener.route('/error/', methods=['GET', 'POST'])
def error():
    msg = request.args.get('msg', '')
    if not msg:
        msg = 'Error occurred during processing request.'
    return json.dumps({ 'error' : msg })

#~ @listener.router('/check')
#~ def check():
    

@listener.route('/config/')
def config():
    try:
        return render_template('config.html', **{'config' : listener.config['iconfig'].__dict__['_sections']})
        #~ return render_template('config.html', {'config' : {'hi' : 'there'}})
    except Exception, e:
        logging.exception(e)
        params = urllib.urlencode({'msg' : str(e)})
        redirect(url_for('/error/?%s' % params))
    

@listener.route('/command/')
def command():
    command = request.args.get('command', '')
    if command:
        try:
            generic = getattr(commands, command)
        except Exception, e:
            logging.exception(e)
            params = urllib.urlencode({'msg' : str(e)})
            return redirect('/error/?%s' % params )
    return generic(request)

if __name__ == "__main__":
    listener.run('0.0.0.0', 5692)
    url_for('static', filename='chinook.css')
    url_for('static', filename='jquery-1.8.3.min.js')
    url_for('static', filename='jquery-ui.css')
    url_for('static', filename='jquery-ui.js')
