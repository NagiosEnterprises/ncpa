#------------------------------------------------------------------------------
# Config.py
#   This file defines information about the service. The first four
# attributes are expected to be defined and if they are not an exception will
# be thrown when attempting to create the service:
#
#   NAME
#       the name to call the service with one %s place holder that will be used
#       to identify the service further.
#
#   DISPLAY_NAME
#       the value to use as the display name for the service with one %s place
#       holder that will be used to identify the service further.
#
#   MODULE_NAME
#       the name of the module implementing the service.
#
#   CLASS_NAME
#       the name of the class within the module implementing the service. This
#       class should accept no parameters in the constructor. It should have a
#       method called "Initialize" which will accept the configuration file
#       name. It should also have a method called "Run" which will be called
#       with no parameters when the service is started. It should also have a
#       method called "Stop" which will be called with no parameters when the
#       service is stopped using the service control GUI.
#
#   DESCRIPTION
#       the description of the service (optional)
#
#   AUTO_START
#       whether the service should be started automatically (optional)
#
#   SESSION_CHANGES
#       whether the service should monitor session changes (optional). If
#       True, session changes will call the method "SessionChanged" with the
#       parameters sessionId and eventTypeId.
#------------------------------------------------------------------------------

# when installing the service with the command
#   ncpaservice --install ncpa
# or
#   sc create ncpa binPath= "path/to/ncpa.exe"
#
# then
#   sc start ncpa
#
# the ncpa from the first command will be used as %s in the following values
# i.e. the following:
# NAME = "ncpa"                     -- name of the service
# DISPLAY_NAME = "Nagios - ncpa"    -- description of the service


# -------
# This is NOT used anymore. It is only here for reference.
# -------

from __future__ import annotations

NAME = "%s"
DISPLAY_NAME = "Nagios - %s"
MODULE_NAME = "ncpa"
CLASS_NAME = "WinService"
DESCRIPTION = "Nagios Cross-Platform Agent"
AUTO_START = False
SESSION_CHANGES = False
