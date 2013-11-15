Introduction
============

Welcome to the official documentation for NCPA! Here you'll find information and how-tos on the NCPA agent.

What is NCPA?
-------------

NCPA stands for Nagios Cross Platform Agent. It strives to maintain cross-platform servitude. It's initial inception was at NWCNA 2012 where a very astute network admin noted::

    I have no idea why agents are so difficult.

Simple and correct. NCPA strives to be simple yet powerful and flexible.

Why use NCPA?
-------------

NCPA seeks to be an abstraction between the sysadmin and the system. People monitor servers because servers are running important services, the required knowledge of OS is secondary to the real point of monitoring, and is simply a necessary detail that must be known. With NCPA, the goal is that after installation, it is completely transparent between Mac OS, Linux, Windows, etc. Once you can depend on this abstraction barrier you can monitor your system without regard to the operating system, you can leverage these abstract ideas against all of your systems, not just servers using NRPE versus NSClient++. Obviously, this is an optimistic situation, but that is the goal.