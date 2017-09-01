NCPA
====

.. image:: https://travis-ci.org/NagiosEnterprises/ncpa.svg?branch=master
    :target: https://travis-ci.org/NagiosEnterprises/ncpa

The *Nagios Cross-Platform Agent*; a single monitoring agent that installs on all major operating systems. NCPA allows both active checks via check_ncpa.py and passive checks via NRDP. NCPA comes with a built-in web GUI, documentation, websocket graphing, and is secured with SSL by default.

Downloads
---------

Current versions:

+---------+-------------+-------------------------------------------------------+
| Current | **2.0.5**   | `Downloads <https://www.nagios.org/ncpa/#downloads>`_ |
+---------+-------------+-------------------------------------------------------+

`Older Versions <https://www.nagios.org/ncpa/archive.php>`_

We currently build for the following operating systems:

- Windows (Vista+)
- Mac OS X (10.7+)
- CentOS / RHEL (5+)
- Debian (7+)
- Ubuntu (12+)
- OpenSUSE (11+)
- SLES (11+)
- Oracle (5+)
- AIX (6.1+) (*still a little experimental*)

Other systems we are working on builds for:

- Fedora
- Solaris

If your operating system of choice is not on the list and none of the builds work for you, then you can request it to be added here by creating a new GitHub issue.

Documentation
-------------

You can view the most current `HTML documentation <https://nagios.org/ncpa/help.php>`_ online or view your current NCPA version's documentation using the NCPA web GUI from an installed agent. This is recommended if you are using an older version, since some features may not be available but may be used in newer documents.

Advanced
--------

**Contributing**

We are always looking to improve NCPA. If you can add a feature or fix a bug, your help is greatly appreciated. Even testing is a great help! In order to contribute, you should start by following the instructions in the `contribute docs <https://github.com/NagiosEnterprises/ncpa/blob/master/CONTRIBUTING.rst>`_.

**Building From Source**

While we recommend using the pre-built version above, sometimes you may find the need to build your own binaries from the source. Mostly, this consists of installing the newest version of *Python 2.7* and a few modules installed through pip. There are some issues on certain systems that are explained in the build docs below.

+------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
| `Building for Windows <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-windows>`_ | `Building for Linux <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-linux>`_ | `Building for Mac OS X <https://github.com/NagiosEnterprises/ncpa/blob/master/BUILDING.rst#building-on-mac-os-x>`_ |
+------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
