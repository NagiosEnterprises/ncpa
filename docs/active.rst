.. _active-checks:
    
Active Checks
=============

Running active checks against the NCPA agent is trivial and follows in a somewhat similar style as check_nrpe. There is a `check_ncpa.py plugin script <http://exchange.nagios.org/directory/Plugins/Network-and-Systems-Management/check_ncpa/details>`_ that is available to use. This plugin is the standard method for executing active checks. However, because of the design of NCPA, it makes it **very** easy to use your own methods to collect data at perform active checks.

.. note:: Everything on this particular page is referring to your Nagios server. Active checks do not require you to change the NCPA agent's computer.

Specifying these checks will take some familiarity with the API tree. It may be useful to familiarize yourself with the documentation on the :ref:`API tree <introduction-api>`.

Getting check_ncpa.py
---------------------

The check_ncpa.py plugin script is hosted on Nagios's plugin exchange. Please download it from the following link:

    `check_ncpa.py <http://exchange.nagios.org/directory/Plugins/Network-and-Systems-Management/check_ncpa/details>`_

This file must exist on your Nagios server in order to use any of the following directives.

.. note:: The check_ncpa.py is downloaded and installed as part of the NCPA monitoring wizard in Nagios XI.

Using check_ncpa.py
-------------------

Once check_ncpa.py is installed in the nagios/libexec directory, you can use it like you would any other plugin. This is where knowing the tree comes in handy. You'll need to specify the path in the tree that you'd like to access. So if we were interested in getting the CPU Usage (percent-wise) of our NCPA agent, we would run the check_ncpa.py as follows::
    
    ./check_ncpa.py -H ncpaserver -t yourtoken -M cpu/percent

Returns::
    
    OK: Percent was 6.8%,0.0%,7.5%,0.0%,5.5%,0.1%,7.0%,0.0%|'percent_0'=6.8% 'percent_1'=0.0% 'percent_2'=7.5% 'percent_3'=0.0% 'percent_4'=5.5% 'percent_5'=0.1% 'percent_6'=7.0% 'percent_7'=0.0%

The values returned are the CPU usage on each core of the system.

.. warning:: If you encounter problems with check_ncpa.py, enable -v when calling to enable verbose logging of problems.

It should also be noted that you can use check_ncpa.py to return a tree representing all the values you can monitor via NCPA. This is very useful if you are in a terminal without the luxury of a web browser. You can use check_ncpa.py's --list command to have it list, rather than run a check, on a particular node::

    ./check_ncpa.py -H ncpaserver -t yourtoken -M cpu --list

This command will return a tree representing all of the values you can monitor via NCPA under the cpu tree. To look at everything you could possibly monitor, simply omit the -M flag and its argument.

Specifying Arguments for NCPA Builtins
--------------------------------------

.. note::

    What is a NCPA built-in? Its a metric that is bundled with NCPA. For example, if you have a plugin you are using NCPA to execute, that is **not** considered a built-in.

You can use the built-in --warning, --critical, etc of check_ncpa.py, or you can simply bundle those into the check address::
    
    ./check_ncpa.py -H ncpaserver -t yourtoken -M cpu/percent --warning 10

.. warning::

    Please note that NCPA uses the | character when referring to file system. For example, on a Windows machine,
    the C:\ drive is referred to as C:|. This is to avoid escaping issues. However, it should be noted that | is
    a special character in sh (the shell). In order to get around this, when you are specifying disks, use single
    quotes around your disk call. Example:

    ./check_ncpa.py -H ncpaserver -t yourtoken -M 'disk/logical/C:|'

    So that the shell does not interpret the special character |.

Specifying Arguments for Plugins Run by NCPA
--------------------------------------------

In order to specify arguments plugins that NCPA will be running, you must use the -a flag when calling check_ncpa.py. You can also use the long argument for the -a flag, which is --arguments.

Imagine we are going to run the test.sh plugin installed on our NCPA server. If we were running the test.sh plugin on our server with NCPA installed we would run something like::

    /path/to/ncpa/plugins/test.sh -u 'one argument' -p 'another argument'

In order to run this properly with NCPA you would call check_ncpa.py like so::

    ./check_ncpa.py -H ncpaserver -t yourtoken -M agent/plugin/test.sh -a "-u 'one argument' -p 'another argument'"

Notice that items with spaces are wrapped in quotes. There is some shell splitting that goes on under
the hood with NCPA, so the quotes are important if you need to keep the spaces. Lets take
a look at what can happen.

How NCPA actually processes these is by calling the URL as follows::

    https://ncpaserver/api/agent/plugin/test.sh/-u/one argument/-p/another argument

You can also call it this way if you please, however I believe most people prefer
the -a method as it keeps some of the dirty details hidden away. Now if you remove
the quotes around 'one argument in the above example call, it would actually call::

    https://ncpaserver/api/agent/plugin/test.sh/-u/one/argument/-p/another argument

See the difference? It interprets as if it were the shell, so wrap the arguments
that need to maintain spaces in quotes.

When All Else Fails...
----------------------

Either way, calling::
    
    ./check_ncpa.py --help

Help does exist and is actually helpful. It might even solve a few head scratchers.
    
