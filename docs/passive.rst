.. _passive-checks:
    
Passive Checks
==============

Specifying passive checks with NCPA is done by amending the [passive checks] section on the ncpa.cfg. 

.. note:: Specifying a host and service on the Nagios side to receive these checks is beyond the scope of this document. Please refer to the `Nagios documentation on setting up passive checks <http://nagios.sourceforge.net/docs/nagioscore/4/en/passivechecks.html>`_ for a better understanding of how to manage passive checks.

Specifying these checks will take some familiarity with the NCPA API. For on that see the documentation on the :ref:`NCPA API <introduction-api>`.

Specifying the Nagios Server
-----------------------------------

You'll need to specify where the passive checks will be sent. This can be accomplished by setting the [nrdp] section with the proper values, where the *parent* would be the target NRDP address to send check results to. While the *token* is the connection token that particular NRDP server is expecting for authentication. Set these in the ncpa.cfg before continuing.

Specifying Checks
-----------------

In the ncpa.cfg there is a section titled [passive checks]. In the default configuration there are a few example services specified. Let's take a look at one::
    
    %HOSTNAME%|CPU Usage = /cpu/percent --warning 20 --critical 30

When NCPA is running, it parses through this config file and looks for all the entries under the passive checks section.

For each entry in this section, it takes the string of text before the equals, and splits it on \|. The result is the hostname and servicename, while the instructions to execute to find its status are on the left hand side of the = sign.

To be more generic, the general form goes like this::
    
    <hostname>|<servicename> = <instructions>

.. topic:: Hostname Hijinks
    
    %HOSTNAME% is a magic word that gets replaced by what is specified in the [nrdp] hostname's declaration.
    
    This might seem backwards at first, but it allows for flexibility. You could have the NCPA agent send results for checks made on remote computers or on a different host like so::
    
    computer1|cpu usage = /agent/plugin/<plugin that checks cpu on remote system>
    computer2|cpu usage = /agent/plugin/<plugin that checks cpu on other remote system>
    %HOSTNAME%|cpu usage = /agent/cpu/percent
    
    This will make the NCPA send back results under hostnames computer1, computer2 and itself.

.. note:: While the NCPA HTTP server does not have to be running and active in order for the passive agent to work, the <instructions> must be an API address.



