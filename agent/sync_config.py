#!/usr/bin/env python
import requests

url    = "http://192.168.2.29/nrdp/"
token  = "e9c6oudjfjs6"
cmd    = "getplugin"
plugin = "check_winping.exe"
os     = "Windows"
os_ver = "6.1.7601"
arch   = "x86"

def get_plugin(url, *args, **kwargs):
    kwargs['token'] = "e9c6oudjfjs6"
    for key in kwargs:
        print kwargs[key]
        
    #a = requests.get(url, params=kwargs)
    
    #print a
    #url_request = requests.get(url, params=**kwargs)
    #the_real_slim_shady = './plugins/' + kwargs['plugin']
    
    #with open(the_real_slim_shady, 'w') as plugin:
    #    plugin.write(url_request.content)
    
    
def test_var_kwargs(farg, **kwargs):
    print "formal arg:", farg
    for key in kwargs:
        print "another keyword arg: %s: %s" % (key, kwargs[key])

post_var = { plugin:'check_winping.exe' }
#~ test_var_kwargs(farg=1, myarg2="two", myarg3=3)
get_plugin(url, plugin='check_winping.exe', )

#CHUNK = 16 * 1024
#with open(plugin, 'wb') as fp:
#  while True:
#    chunk = resp.read(CHUNK)
#    if not chunk: break
#    fp.write(CHUNK)

#print "http://192.168.2.29/nrdp/?token=e9c6oudjfjs6&cmd=getplugin&plugin=check_winping.exe&os=Windows&os_ver=6.1.7601&arch=x86"
