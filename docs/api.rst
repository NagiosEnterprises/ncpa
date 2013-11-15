.. _introduction-api:
    
Introduction to the API
=======================

These words might sound a bit daunting, but its really quite simple.

NCPA was designed to make it easy for adminstrators to setup checks, troubleshoot and test new checks and keep the options for running these checks very flexible.

Let us try out a quick example to illustrate what this means. In these following examples I will be running my checks against ncpaserver, so when addresses are used, substitute the IP of your NCPA agent's computer in for ncpaserver, as well as the NCPA agents token for the token that I will use.

Looking at the tree
-------------------

Open up your web browser, and navigate to::
    
    https://ncpaserver:5693/api/?token=brody

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
    
    https://ncpaserver:5693/api/memory?token=brody

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
    
    These are meant to provide a platform independent way of accessing basic metrics on a server that are most oftenly monitored. These are not run from plugins, these are built into the NCPA program itself.
    
    Each of these branches contains its own metrics. Some of these metrics are enumerated upon NCPA server startup. For instance, disks and interfaces will be enumerates and will be listed in this tree as well.

.. caution:: Accessing disks is indicated with the pipe | character, rather than the / or \\ character to avoid escaping issues. Keep this in mind when writing queries. The | character is a special character in bash, so you will generally have to wrap it in single quotes when using it as an argument to avoid problems. 

So hopefully, you're noticing whats going on here. To be overt, we can pare down the information to the actual metric we want in much the same way that we specify the file we want to a computer. We specify a path and then we access that file or directory. The individual metrics we wish to find (CPU Usage, Memory Usage, etc) are the files, while the general groupings (CPU, Memory) are the directories, in this analogy.

So now let us make a bigger leap and actually grab a specific memory metric. Let us grab the the percent of real memory used. If you look at the tree, you'd notice that the accessor URL is::

    api/memory/virtual/available

So let us try plugging that in to our ncpaserver::
    
    https://ncpaserver:5693/api/memory/virtual/available?token=brody

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

Well its all well and good that we can pull these numbers, but what we it would pretty cool if we could turn these into Nagios return results. Now that we've spoke about accessing these items, lets talk about what we can do with these.

When you are working on a metric, rather than a group of metrics, you can turn it into a Nagios result very easily. This API supports quite a bit of specifications using GET or POST variables, to illustrate that, let us turn the above RAM number into a Nagios return results.

We are going to add &warning=60&critical=80&check=true onto the end of the above URL. If you're familiar with URLs, you'll see that this is specifying GET variables passed to the server. If you're unfamiliar with URLs, you just learned something!::
    
    https://ncpaserver:5693/api/memory/virtual/available?token=brody&warning=1&critical=2&check=true

Returns::
    
    {
      "value": {
        "returncode": 2, 
        "stdout": "CRITICAL: Available was 1112682496.0b|'available_0'=1112682496.0b;1;2"
      }
    }

This is the JSON for dump to Nagios. We see it has its return code, and its standard out that will be the status information for a service.

Its kind of ugly though, I'd rather that number be in GB. So add &unit=G to the end of the request::
    
    {
      "value": {
        "returncode": 1, 
        "stdout": "WARNING: Available was 1.114Gb|'available_0'=1.114Gb;1;2"
      }
    }

There thats better, much more human readable.

.. topic:: Nagios Check Result Specifiers
    
    So there are a couple things we can tack onto the end of the request URL to get what we want out our check
    
    .. glossary::
        
        check
            Set to true if you'd like to result to be transformed into a check result rather than just raw data.
        
        warning
            Specify the Nagios warning threshold.*
        
        critical
            Specify the Nagios critical threshold.*
        
        unit
            Expects K (for kilo), M (for mega), G (for giga) and T (for tera).
        
        delta
            There are some results that simply counters. Specifically, the interface counters simply count the bytes that pass through the interface. Set delta=1 for the NCPA server to calculate the change in the counter divided by the amount of time that has past since last check (bytes/sec).

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
    
    https://ncpaserver:5693/api/agent/plugin/test.vbs/"First Arg"?token=brody

Which shows us the output::
    
    {
      "value": {
        "returncode": 2, 
        "stdout": "This worked! First Arg\n"
      }
    }

Which is what our script is supposed to do, return 2 and print "This Worked!" along with the first argument.

.. note:: For plugins, the Check Result Specified do not apply. The result specified will work only for NCPA tree results.

Conclusion
----------

Using the API is simple, and will be useful to access your own checks later. While intimate knowledge is certainly not necessary, it does give a strange feeling of power.
