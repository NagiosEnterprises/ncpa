NCPA
====

.. image:: https://travis-ci.org/NagiosEnterprises/ncpa.svg?branch=master
    :target: https://travis-ci.org/NagiosEnterprises/ncpa

The *Nagios Cross-Platform Agent*; a single monitoring agent that installs on all major operating systems. NCPA allows both active checks via check_ncpa.py and passive checks via NRDP. NCPA comes with a built-in web GUI, documentation, websocket graphing, and is secured with SSL by default.

Downloads
---------

Current versions:

+---------+-------------+-------------------------------------------------------+
| Current | **3.2.1**   | `Downloads <https://www.nagios.org/ncpa/#downloads>`_ |
+---------+-------------+-------------------------------------------------------+

Note: If your nagios repo is outdated when installing NCPA, you must first update your GPG key using the following:

CentOS/RHEL/Oracle::

    yum clean all
    rpm --import https://repo.nagios.com/GPG-KEY-NAGIOS-V3

Ubuntu/Debian::

    wget -qO - https://repo.nagios.com/GPG-KEY-NAGIOS-V3 | apt-key add -

NOTE: If you're using Debian 11 or one of the other newer OSes and you see an "E: gnupg, gnuph2 and gnupg1 do not seem to be installed..." error when adding the public key you can either install gnupg (apt-get install gnupg) or you can read `how to add the GPG key the new, more secure way <https://stackoverflow.com/questions/68992799/warning-apt-key-is-deprecated-manage-keyring-files-in-trusted-gpg-d-instead>`_.

`Older Versions <https://www.nagios.org/ncpa/archive.php>`_

We currently build for the following operating systems on x86-64 architectures:

- CentOS 9+
- RHEL 8+
- Oracle 8+
- Debian 11+
- Ubuntu 20+
- OpenSuSE 15+
- SLES 15+
- Amazon Linux 2
- Windows 10+
- Windows Server 2016+
- MacOS Ventura+ (13+)
- Solaris 11.4 SRU78+

Older systems that have been supported by NCPA in the past:

- Mac OS X 10.7-10.10           - v2.4.0
- Mac OS X 10.11-12             - v2.4.1
- Raspbian 10 - Buster          - v2.2.2
- Ubuntu 12.04                  - v2.1.4
- Ubuntu 14.04                  - v2.2.2
- Ubuntu 16.04 32b, 18.04 32b   - v2.4.1
- Ubuntu 20                     - v3.1.0
- Debian 7                      - v2.1.4
- Debian 8 32b, 9 32b           - v2.4.1
- Debian 10                     - v3.1.0
- OpenSUSE 11, 12, 13           - v2.1.4
- SLES 11                       - v2.4.0
- SLES 12                       - v2.4.1
- AIX 6                         - v2.1.1
- AIX 7                         - v2.2.1
- CentOS / RHEL 5               - v2.0.6
- CentOS / RHEL 6               - v2.2.2
- CentOS / RHEL 7               - v3.1.0
- CentOS 8                      - v3.1.0
- CentOS Stream 8 - ARM         - v2.4.0
- Oracle 5                      - v2.0.6
- Oracle 6                      - v2.2.2
- Oracle 7                      - v3.1.0
- Windows XP/Vista              - v1.8.1
- Windows 7+ 32-bit             - v2.4.1
- Solaris 10
- Solaris 11                    - v2.4.0

If you're looking for older builds you can find them `in the archives <https://www.nagios.org/ncpa/archive.php>`_.

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

