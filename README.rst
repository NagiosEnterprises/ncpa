NCPA
====

The *Nagios Cross-Platform Agent*; a single monitoring agent that installs on all major operating systems. NCPA allows both active checks via check_ncpa.py and passive checks via NRDP. NCPA comes with a built-in web GUI, documentation, websocket graphing, and is secure with SSL by default.

Downloads
---------

Current versions:

+--------+-----------+---------------------------------------------------------------------+
| Stable | **1.8.1** | `Downloads <http://assets.nagios.com/downloads/ncpa/download.php>`_ |
+--------+-----------+---------------------------------------------------------------------+

We currently build for the following operating systems:

- Windows
- Mac OS X
- CentOS / RHEL 5, 6, 7
- Fedora 21
- Debian / Ubuntu
- OpenSUSE 11, 12, 13
- SLES 11, 12

If your operating system of choice is not on the list and none of the builds work for you, then you can request it to be added here by creating a new GitHub issue.

Documentation
-------------

You can view the most current `HTML documentation <https://assets.nagios.com/downloads/ncpa/docs/html/>`_ online or view your current NCPA version's documentation using the NCPA web GUI from an installed agent. This is recommended if you are using an older version, since some features may not be available but may be used in newer documents.


Advanced
--------

**Building From Source**

While we recommend using the pre-built version above, sometimes you may find the need to build your own binaries from the source. Mostly, this consists of installing the newest version of *Python 2.7* and a few modules installed through pip. There are some issues on certain systems that are explained in the build docs below.

`Building for Windows <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst>`_

`Building for Linux <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst>`_
