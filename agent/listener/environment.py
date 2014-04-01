import platform

puname = platform.uname()[0]

if puname == u'Windows':
    SYSTEM = u'Windows'
elif puname == u'Darwin':
    SYSTEM = u'Darwin'
else:
    SYSTEM = u'Linux'

if puname == u'Windows':
    SERVICE_TYPE = u'Windows'
elif puname == u'Darwin':
    SERVICE_TYPE = u'Darwin'
else:
    SERVICE_TYPE = u'Initd'
