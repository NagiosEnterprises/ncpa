Configuration
==================

NCPA should start working right out of the box. However, to tailor it to your needs and for security reasons, you should at least change the API's community string for non-Windows installations.

If you wish to send passive results, you will also need to specify additional information related to passive checks to the configuration file. 

This document is meant to be a reference as to what these directives mean, not necessarily a friendly way to define them.

One last item that should be noted is that you do not need to restart the NCPA server upon changing any of the configuration used by the passive agent. Every time the passive agent wakes up, it re-parses its configuration file. However, for the active agent there are some items that are parsed once at service start, mainly the section named '[listener]'. For this reason you should restart the NCPA service if you want to reflect the changes made for active checks.

Config File Location
--------------------

In order to configure NCPA, you will need to edit its configuration file, which is kept on the file system.

Windows keeps this file at::
    
    C:\Program Files\Nagios\NCPA\etc\ncpa.cfg
    
    or
    
    C:\Program Files (x86)\Nagios\NCPA\etc\ncpa.cfg

Linux keeps this file at::
    
    /usr/local/ncpa/etc/ncpa.cfg

Once you have located this file, you can start editing it. This file is a standard INI file.

Config File Directives
----------------------

Lets take a look at some of the directives in a the configuration file. Note that the config file is sectioned off by the square brackets. These different sections affect different portions of NCPA's operation.

We will break the configuration file down by section.

.. note:: You might notice that there appears to be duplicate entries. For instance, both [listener] and [passive] sections have a specification for *logfile*. They maintain separate log files as they are considered two different processes and are treated as such.

[listener]
++++++++++

This section controls NCPA's active check settings including how you actively connect to this agent to ask it for information. NCPA starts up an HTTP server to handle Nagios requests which makes much of the specification in this section relevant to that server. 

.. glossary::
    
    ip
        This determines what IP the agent will listen on. By default, it will listen on 0.0.0.0, which means it will listen on all interfaces and all name references. Specify this if you would only like the agent to listen on a specific IP or name.
    
    port
        This specifies the TCP port the NCPA server will bind to. 
    
    uid
        Determines which user the NCPA server will run as.
    
    gid
        Determines the group by which the NCPA server will run as.
    
    pidfile
        The named file location where the PID file for the NCPA server will be stored and maintained.
    
    logfile
        The named file location where the log file for the NCPA server will be stored.
    
    certificate
        EXPERIMENTAL. Allows you to specify the file name for the SSL certificate you wish to use with the NCPA server. If left adhoc, a new self-signed certificate will be generated and used for the server.

[api]
+++++

This section controls how the API is accessed, and currently sports only one item.

.. glossary::
    
    community_string
        The token that you use to authenticate when accessing the web interface. This should be something non-trivial.

[passive]
+++++++++

This section controls how the passive service behaves. It will specify things such as what it should do and how often it should be done. 

.. glossary::
    
    sleep
        The time in seconds which the service will wait until running again. Upon waking up, the service will check to see if it has anything to do. If it has nothing to do it will sleep again for the specified time.
    
    handlers
        This is where the magic happens with the NCPA passive agent. Handlers are items that are run whenever the passive daemon wakes up. The currently supported handlers are nrds and nrdp. This handlers list should be a comma-delimited list of handlers that are to be run. To run both nrds and nrdp handlers, this entry would be *handlers = nrds,nrdp*. More information is provided about what each of these handlers do under the `[nrds]`_ and `[nrdp]`_ sections, respectively.
    
    uid
        Determines which user the NCPA passive service will run as during execution.
    
    gid
        Determines the group by which the NCPA passive service will run as during execution.
    
    pidfile
        The named file location where the PID file for the NCPA passive service will be stored and maintained.
    
    logfile
        The named file location where the log file for the NCPA passive service will be stored.

[nrdp]
++++++

The value *nrdp* must be present in the passive handlers declaration (above) to send any results back to the Nagios server. This section dictates where NRDP results will be sent and what tokens will be used.

.. glossary::
    
    parent
        The IP address of the Nagios server to which the passive check results should be sent. The wording on this may seem a bit confusing, but it's for a reason. The NCPA agent can also function as a NRDP forwarder. If you sent NRDP results to the NCPA listener's IP with the proper token, it will forward the NRDP check results to its parent which is this directive. This allows for you to have a chain of NRDP forwards if firewall constraints are incredibly heavy.
    
    token
        The token to use to access its parent. Should not be the same as the token NCPA uses for its own server for security reasons.

[nrds]
++++++

The value *nrds* must be present in the passive handler declaration (above) in order to pull down any new configuration. `NRDS <http://exchange.nagios.org/directory/Addons/Components/Nagios-Remote-Data-Sender-(NRDS)/details>`_ is a slick way to manage your configuration files. Many of these directives are boilerplate. The interesting directives are identified in the following. For more information on NRDS see the above link for further definitions of these terms.

.. glossary::
    
    CONFIG_NAME
        This is the name that the NCPA passive service will query for updates and is set up in Nagios XI. 
    
    TOKEN
        The token the NCPA passive service will use when connecting to the NRDS server.
    
    URL
        The URL to be queried for NRDS information.
    
    UPDATE_CONFIG
        If this is set to 1, then the config will be updated automatically when a new config becomes available. If anything else, it will not be updated.
    
    UPDATE_PLUGINS
        If this is set to 1, then the plugins in the plugins/ directory will be automatically maintained using NRDS.

[passive checks]
++++++++++++++++

This section does have a hard and fast set of concrete instructions. For information on setting up passive checks, see the section :ref:`Setting Up Passive Checks <passive-checks>`.

[plugin directives]
+++++++++++++++++++

This section is where you can specify both the plugin directory and special operations that should be executed when a given file type is executed as part of a service check. Some examples for the special directives are given.

.. glossary::
    
    plugin_path
        The path to the directory containing any third party plugins that need to be run.
    
    
