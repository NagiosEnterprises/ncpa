import jinja2
from html import HttpResponse, render_to_response
import logging
import os

def handle(request):
    rest = request.directive.split('/frontend', 1)[1]
    if rest == '' or rest == '/':
        return main(request)
    elif 'config' in rest:
        return config(request)

def plugin(request):
    return render_to_response('plugin.html', {})

def main(request):
    return render_to_response('main.html', {})

def config(request):
    return render_to_response('config.html', {'config' : request.server.config.__dict__['_sections']})
