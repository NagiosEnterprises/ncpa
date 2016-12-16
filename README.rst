NCPA
====

The *Nagios Cross-Platform Agent*; a single monitoring agent that installs on all major operating systems. NCPA allows both active checks via check_ncpa.py and passive checks via NRDP. NCPA comes with a built-in web GUI, documentation, websocket graphing, and is secured with SSL by default.

Downloads
---------

Current versions:

+---------+-------------+----------------------------------------------------------------------+
| Current | **2.0.0**   | `Downloads <https://assets.nagios.com/downloads/ncpa/download.php>`_ |
+---------+-------------+----------------------------------------------------------------------+

`Older Versions <https://assets.nagios.com/downloads/ncpa/archived/>`_

We currently build for the following operating systems:

- Windows (Vista+)
- Mac OS X (10.7+)
- CentOS / RHEL (5+)
- Debian (7+)
- Ubuntu (12+)
- OpenSUSE (11+)
- Oracle (6+)

Other systems we will build for soon:

- SLES (11+)
- Fedora

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
