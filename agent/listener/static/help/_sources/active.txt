.. _active-checks:
    
Active Checks
=============

Running active checks against the NCPA agent is trivial and follows in someone style with check_nrpe. There is a *check_ncpa.py* script that is available to use, and is the standard method for checking these.

.. note:: Everything on this particular page is referring to your Nagios server and will not have to touch the NCPA agent's computer.

.. note:: Because of the design of NCPA, it makes it **very** easy to use your own methods to collect this data.

.. note:: If you encounter problems with check_ncpa.py, enable -v when calling to enable verbose logging of problems.

Specifying these checks will take some familiarity with the API tree. For on that see the documentation on the :ref:`API tree <introduction-api>`.

Using check_ncpa.py
-------------------

Once check_ncpa.py is installed in the nagios/libexec directory, you can use it like you would any other plugin. This is where knowing the tree comes in handy. You'll need to specify the path in the tree that you'd like to access. So if we were interested in getting the CPU Usage (percent-wise) of our NCPA agent, we would run the check_ncpa.py as follows::
    
    ./check_ncpa.py -H ncpaserver -t brody api/cpu/percent

Returns::
    
    OK: Percent was 6.8%,0.0%,7.5%,0.0%,5.5%,0.1%,7.0%,0.0%|'percent_0'=6.8% 'percent_1'=0.0% 'percent_2'=7.5% 'percent_3'=0.0% 'percent_4'=5.5% 'percent_5'=0.1% 'percent_6'=7.0% 'percent_7'=0.0%

Which is the CPU usage on each core of the system!

.. note:: In the above example I specified *api/cpu/percent* as the address. The *api/* portion is completely optional and the URL without it would work just fine.

Specifying Arguments
--------------------

You can use the builtin --warning, --critical, etc of check_ncpa.py, or you can simply bundle those into the check address::
    
    ./check_ncpa.py -H ncpaserver -t brody api/cpu/percent --warning 10

and::
    
    ./check_ncpa.py -H ncpaserver -t brody api/cpu/percent&warning=10

Are identical calls. Either way, calling::
    
    ./check_ncpa.py --help

exists and is helpful. It might even solve a head scratchers.
    
