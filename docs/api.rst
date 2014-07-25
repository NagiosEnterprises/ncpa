.. _introduction-api:
    
The API
=======================

The NCPA API may seem complex but it is actually very simple. NCPA was designed to make it easy for administrators to set-up checks, troubleshoot, test new checks, and keep the options for running these checks very flexible.

Let's try out a quick example to illustrate what this means. In these following examples I will be running my checks against "ncpaserver", a fictitious server, so when addresses are used. Substitute the IP of your NCPA agent's computer in for "ncpaserver" as well as your NCPA token for the token "nagios" that I use.

Looking at the tree
-------------------

Open up your web browser, and navigate to::
    
    https://ncpaserver:5693/api/?token=nagios

This returns::
    
    --- snip ---
    {
    "value": {
      "root": {
        "process": [], 
        "user": {
          "count": 1, 
          "list": [
            "nscott"
          ]
        }, 
        "memory": {
          "swap": {
            "used": [
              8245542912, 
              "b"
            ],
    --- snip ---

Looks like a very large list. If you take a close look at this list, you'll see that amongst all the weird characters, there are actual numbers and descriptions of those numbers. This format is JSON, and those who are familiar with accessing APIs should be familiar with it.

Accessing specific items in the tree
------------------------------------

So notice that there is a "memory" string. Let us amend our address a bit and see what comes out. Try::
    
    https://ncpaserver:5693/api/memory?token=nagios

This returns::
    
    <snip>
    "value": {
        "memory": {
          "swap": {
            "used": [
              8202797056, 
              "b"
            ], 
            "total": [
              17087578112, 
              "b"
            ], 
            "percent": [
              48.0, 
              "%"
            ], 
            "free": [
              8884781056, 
              "b"
            ]
          }, 
          "virtual": {
            "available": [
    <snip>

It cut out everything except all the items that had to do with memory. This is because the API is a tree we explicitly specified we wanted only the "memory" branch. We did this by adding the memory item in the URL. 

.. topic:: Accessible Branches
    
    There are a few selectable branches in the main root of the tree, they are:
    
    * memory
    * interface
    * agent
    * cpu
    * disk
    * agent
    * process
    * services
    
    These are meant to provide a platform independent way of accessing basic metrics on a server that are most often monitored. These are not run from plugins, these are built into the NCPA program itself.
    
    Each of these branches contains its own metrics. Some of these metrics are enumerated upon NCPA server start-up. For instance, disks and interfaces will be enumerated and will be listed in this tree as well.

.. caution:: Accessing disks is indicated with the pipe | character, rather than the / or \\ character to avoid escaping issues. Keep this in mind when writing queries. The | character is a special character in bash, so you will generally have to wrap it in single quotes when using it as an argument to avoid problems. 

So hopefully, you're noticing what's going on here. To be overt, we can pare down the information to the actual metric we want in much the same way that we specify the file we want to a computer. We specify a path and then we access that file or directory. The individual metrics we wish to find (CPU Usage, Memory Usage, etc) are the files, while the general groupings (CPU, Memory) are the directories, in this analogy.

So now let us make a bigger leap and actually grab a specific memory metric. Let us grab the the percent of real memory used. If you look at the tree, you'd notice that the accessors URL is::

    api/memory/virtual/available

So let us try plugging that in to our fictitious "ncpaserver"::
    
    https://ncpaserver:5693/api/memory/virtual/available?token=nagios

This returns::
    
    {
      "value": {
        "available": [
          1115017216, 
          "b"
        ]
      }
    }

So we see that we have exactly 1115017216 bytes of available RAM.

Take this method that we've done, going through the tree one thing at a time to find other metrics. 

Getting Nagios return results
-----------------------------

Well it's good that we can pull these numbers, but it would pretty cool if we could turn these into Nagios return results. Now that we've spoke about accessing these items, lets talk about what we can do with these.

When you are working on a metric, rather than a group of metrics, you can turn it into a Nagios result very easily. The NCPA API supports quite a bit of specifications using GET (or POST) variables. To illustrate this let's turn the above RAM number into a Nagios return results.

We are going to add *&warning=60&critical=80&check=true* onto the end of the above URL::
    
    https://ncpaserver:5693/api/memory/virtual/available?token=nagios&warning=1&critical=2&check=true

Returns::
    
    {
      "value": {
        "returncode": 2, 
        "stdout": "CRITICAL: Available was 1112682496.0b|'available_0'=1112682496.0b;1;2"
      }
    }

Using a GET request (we could also use POST, with the same variables) we were able to have the NCPA API dump this Nagios result formatted JSON output. We can clearly see the output which has a return code and the standard out that will give the status information for a service.

Bytes are kind of ugly though and I'd rather that number be in GB. So add &unit=G to the end of the request::
    
    {
      "value": {
        "returncode": 1, 
        "stdout": "WARNING: Available was 1.114Gb|'available_0'=1.114Gb;1;2"
      }
    }

That's better, much more human readable.

.. topic:: Nagios Check Result Specifiers
    
    There are a couple things we can tack onto the request URL to get what we want out of our check
    
    .. glossary::
        
        check
            Set to true if you'd like to result to be transformed into a check result rather than just raw data.
        
        warning
            Specify the Nagios warning threshold.*
        
        critical
            Specify the Nagios critical threshold.*
        
        unit
            Accepts K (for kilo), M (for mega), G (for giga) and T (for tera).
        
        delta
            There are some results that are counters. Specifically, the interface counters simply count the bytes that pass through the interface. Set delta=1 for the NCPA server to calculate the change in the counter divided by the amount of time that has past since last check to create bytes/sec.

Using Nagios Plugins
--------------------

Using existing Nagios plugins is not an issue either. In fact we can list all the plugins that are installed on the system by accessing the address::
    
    https://ncpaserver:5693/api/agent/plugin

This returns::
    
    {
      "value": {
        "plugin": [
          "check_msmq.vbs", 
          "test.vbs", 
        ]
      }
    }

Which shows all of the plugins that are installed. Now if we want to execute those plugins, we follow the same logic as we did above (for the non-plugin metrics). One new introduction is for plugins that take arguments. Simply separate them with the forward slashes. So for instance, to pass one argument to my test.vbs script, I would call::
    
    https://ncpaserver:5693/api/agent/plugin/test.vbs/"First Arg"?token=nagios

Which shows us the output::
    
    {
      "value": {
        "returncode": 2, 
        "stdout": "This worked! First Arg\n"
      }
    }

Which is what our script is supposed to do, return 2 and print "This Worked!" along with the first argument.

.. note:: For plugins, the Check Result Specified do not apply. The result specified will work only for NCPA tree results.

Monitoring Services
-------------------

Monitoring services is easy with NCPA. You can see the existing services and their current status. Its under the service tree::

    https://ncpaserver:5693/api/service

This should give you a list of all the services on your system. Now if you would like to see a specific service, such as 'ALG' in our instance, try::

    https://ncpaserver:5693/api/service/ALG
    
    {
        "value": {
            "ALG": "stopped"
        }
    }

This will return whether or not the service is running. You can short-circuit this and add running or stopped to get it to return true or false::

    https://ncpaserver:5693/api/service/ALG/stopped
    
    {
        "value": {
            "ALG": true
        }
    }

Now what this does is allows us to use it as a check::

    https://ncpaserver:5693/api/service/ALG/stopped?check=True
    
    {
        "value": {
            "returncode": 0, 
            "stdout": "ALG's status was as expected."
        }
    }

Using this particular address is how you will check to see if a service is running or not. If you're using check_ncpa.py simply use the address::

    service/ALG/stopped

To get metric data use -M and you will get the return value you want.
    
Conclusion
----------

Using the API is simple and will be useful to access your own checks later. While intimate knowledge is certainly not necessary, it does give a strange feeling of power.
