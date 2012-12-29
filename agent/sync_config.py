#!/usr/bin/env python
#import urllib2
#from httplib2 import Http
from urllib import urlencode
#h = Http()
import urllib


url    = "http://192.168.2.29/nrdp/"
token  = "e9c6oudjfjs6"
cmd    = "getplugin"
plugin = "check_winping.exe"
os     = "Windows"
os_ver = "6.1.7601"
arch   = "x86"

data = dict(token=token, cmd=cmd, plugin=plugin, os=os, os_ver=os_ver, arch=arch)
#resp, content = h.request(url, "POST", urlencode(data))

retrieve_url   = url + urlencode( data )
full_plug_path = "./plugins/" + plugin

urllib.urlretrieve (retrieve_url, full_plug_path)


#CHUNK = 16 * 1024
#with open(plugin, 'wb') as fp:
#  while True:
#    chunk = resp.read(CHUNK)
#    if not chunk: break
#    fp.write(CHUNK)

print "http://192.168.2.29/nrdp/?token=e9c6oudjfjs6&cmd=getplugin&plugin=check_winping.exe&os=Windows&os_ver=6.1.7601&arch=x86"
