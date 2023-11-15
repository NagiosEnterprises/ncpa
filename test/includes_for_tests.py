import os

# Required to prevent errors in test debug mode
# os.environ["GEVENT_SUPPORT"] = True

#Has to occur here because SSL is called implicitly before main code runs
# Monkey patch for gevent
from gevent import monkey

if os.name == 'posix':
    monkey.patch_all()
else:
    monkey.patch_all(subprocess=True, thread=False)
