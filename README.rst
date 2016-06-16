NCPA
====

The *Nagios Cross-Platform Agent*, a single monitoring agent that installs on all major operating systems. Compatible with both active checks via check_ncpa.py and passive checks via NRDP.

Downloading NCPA
----------------

`Download from the Nagios Official Builds <http://assets.nagios.com/downloads/ncpa/download.php>`_.

We currently build for Windows, Mac OS X, RHEL/CentOS 5/6/7, Fedora 21, Debian/Ubuntu, SLES 11/12, and OpenSUSE 11/12/13. If your operating system of choice is not on the list and none of the builds work for you, then you can request it to be added here at GitHub.

Building NCPA
-------------

While we recommend using our pre-built solutions above, if you'd like to build NCPA yourself there are a few things you may run into that can cause problems with your build.

There are known build issues involving *cx_Freeze*, if you run into an issue refer to the bug report on the *cx_Freeze* `project bug page <https://bitbucket.org/anthony_tuininga/cx_freeze/issue/42/recent-versions-of-gevent-break#comment-11421289>`_.
