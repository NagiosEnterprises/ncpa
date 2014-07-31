Introduction
============

The official documentation for NCPA! Here you'll find information on installation and management of NCPA.

What is NCPA?
-------------

NCPA stands for Nagios Cross Platform Agent. It strives to maintain cross-platform servitude. It's initial inception was at the North American Nagios World Conference 2012 where a very astute network admin noted::

    I have no idea why agents are so difficult.

Reflecting on that statement, we didn't have an answer. So NCPA was created to be simple and powerful but not at the expense of flexibility.

Why use NCPA?
-------------

NCPA seeks to be an abstraction between the sysadmin and the system. People monitor servers because servers are running important services. The required knowledge of the Operating System is secondary to the real reason for monitoring and is simply a necessary detail that must be known. The goal of NCPA is to be completely transparent after installation between Mac OS, Linux, Windows, etc. Once you can depend on this abstraction barrier you can monitor your system without regard to the operating system. You can leverage these abstract ideas against all of your systems; not just servers using NRPE versus NSClient++.

Can I use NCPA with Nagios Core?
--------------------------------

Absolutely. There is a `Nagios Core plug-in <http://exchange.nagios.org/directory/Plugins/Network-and-Systems-Management/check_ncpa/details>`_ available to download. This agent does not require using Nagios XI, however Nagios XI does come standard with a wizard for creating active checks with NCPA.