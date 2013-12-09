.. _active-checks:
    
Active Checks
=============

Running active checks against the NCPA agent is trivial and follows in somewhat of a similar style as check_nrpe. There is a *check_ncpa.py* script that is available to use, and is the standard method for executing active checks.

.. note:: Everything on this particular page is referring to your Nagios server.  Active checks do not require you to change the NCPA agent's computer.

.. note:: Because of the design of NCPA, it makes it **very** easy to use your own methods to collect this data.

Specifying these checks will take some familiarity with the API tree. It may be useful to familiarize yourself with the documentation on the :ref:`API tree <introduction-api>`.

Getting check_ncpa.py
---------------------

check_ncpa.py is hosted on Nagios's assets server. Please download it from the following link:

    `check_ncpa.py <http://assets.nagios.com/downloads/ncpa/check_ncpa.py>`_

This file must exist on your Nagios server in order to use any of the following directives.

.. note:: The check_ncpa.py is downloaded and installed as part of the NCPA monitoring wizard in Nagios XI.

Using check_ncpa.py
-------------------

Once check_ncpa.py is installed in the nagios/libexec directory, you can use it like you would any other plugin. This is where knowing the tree comes in handy. You'll need to specify the path in the tree that you'd like to access. So if we were interested in getting the CPU Usage (percent-wise) of our NCPA agent, we would run the check_ncpa.py as follows::
    
    ./check_ncpa.py -H ncpaserver -t brody cpu/percent

Returns::
    
    OK: Percent was 6.8%,0.0%,7.5%,0.0%,5.5%,0.1%,7.0%,0.0%|'percent_0'=6.8% 'percent_1'=0.0% 'percent_2'=7.5% 'percent_3'=0.0% 'percent_4'=5.5% 'percent_5'=0.1% 'percent_6'=7.0% 'percent_7'=0.0%

The values returned are the CPU usage on each core of the system.

.. warning:: If you encounter problems with check_ncpa.py, enable -v when calling to enable verbose logging of problems.

It should also be noted that you can use check_ncpa.py to return a tree representing all the values you can moitor via NCPA.  This is very useful if say you are in the fairly common environment of a terminal without the luxury of a web browser, or the browser is simply too bothersome to bring up. You can use check_ncpa.py's --list command to have it list, rather than run a check, on a particular node::

    ./check_ncpa.py -H ncpaserver -t brody -M cpu --list

This command will return a tree representing all of the values you can monitor via NCPA under the cpu tree. To look at everything you could possibly monitor, simply omit the -M flag and its argument.

Specifying Arguments
--------------------

You can use the builtin --warning, --critical, etc of check_ncpa.py, or you can simply bundle those into the check address::
    
    ./check_ncpa.py -H ncpaserver -t brody api/cpu/percent --warning 10

and::
    
    ./check_ncpa.py -H ncpaserver -t brody api/cpu/percent&warning=10

Are identical calls. Either way, calling::
    
    ./check_ncpa.py --help

exists and is helpful. It might even solve a few head scratchers.
    
