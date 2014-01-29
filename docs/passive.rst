.. _passive-checks:
    
Passive Checks
==============

Specifying passive checks with NCPA is done by amending the [passive checks] section on the ncpa.cfg. 

.. note:: Specifying a host and service on the Nagios side to receive these checks is beyond the scope of this document. Please refer to the `Nagios documentation <http://nagios.sourceforge.net/docs/3_0/passivechecks.html>`_ for a better understanding of passive checks.

Specifying these checks will take some familiarity with the API tree. For on that see the documentation on the :ref:`API tree <introduction-api>`.

Specifying the Nagios Server
-----------------------------------

You'll need to specify where the passive checks will be sent to. This can be accomplished by setting the [nrdp] section with the proper values, where the *parent* would be the target NRDP address to send check results to. While the *token* is the connection token that particular NRDP server is expecting. Once this is set, you can move on.

Specifying Checks
-----------------

In the ncpa.cfg, there is a section titled [passive checks]. In the default ncpa.cfg, there are example services specified. Lets analyze one::
    
    %HOSTNAME%|CPU Usage = /cpu/percent --warning 20 --critical 30

When NCPA is running, it parses through this config file, and looks for all the entries under the passive checks section.

For each entry in this section, it takes the string of text before the equals, and splits it on \|. The result is the hostname and servicename, while the instructions to execute to find its status are on the left hand side of the = sign.

To be more generic, the general form goes like this::
    
    <hostname>|<servicename> = <instructions>

.. topic:: Hostname Hijinks
    
    %HOSTNAME% is a magic word that gets replaced by what is specified in the [nrdp] hostname's declaration.
    
    This might seem backwards at first, but it allows for some flexibility. If you wanted a certain NCPA agent to exist in a remote network, and do all the monitoring on this network, and just send it's results back, you would do
    
    computer1|cpu usage = /agent/plugin/<plugin that checks cpu on remote system>
    computer2|cpu usage = /agent/plugin/<plugin that checks cpu on other remote system>
    %HOSTNAME%|cpu usage = /agent/cpu/percent
    
    This will make the NCPA send back results under hostnames computer1, computer2 and itself. Allowing you to put a bunch of checks for different computers on this particular NCPA agent.

.. note:: While the NCPA HTTP server does not have to active in order for the passive agent to work, the <instructions> must be an API address.



