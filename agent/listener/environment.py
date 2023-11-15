import platform

puname = platform.uname()[0]

if puname == 'Windows':
    SYSTEM = 'Windows'
elif puname == 'Darwin':
    SYSTEM = 'Darwin'
else:
    SYSTEM = 'Linux'

if puname == 'Windows':
    SERVICE_TYPE = 'Windows'
elif puname == 'Darwin':
    SERVICE_TYPE = 'Darwin'
else:
    SERVICE_TYPE = 'Initd'
