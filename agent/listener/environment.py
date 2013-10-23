if platform.uname()[0] == 'Windows':
    SYSTEM = 'Windows'
else:
    SYSTEM = 'Linux'

if platform.uname()[0] == 'Windows':
    SERVICE_TYPE = 'Windows'
else:
    SERVICE_TYPE = 'SystemV'
