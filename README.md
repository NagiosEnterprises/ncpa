NCPA
====

The awesome NCPA agent - one agent to rule them all.

Downloading NCPA
----

You can download the official builds for NCPA at: http://assets.nagios.com/downloads/ncpa/download.php

Building NCPA
----
We recommend using our pre-built solutions above but if you'd like to build NCPA yourself there are a few things you may run into that can cause problems with your build.

There are known build issues involving *cx_Freeze*, if you run into an issue refer to the bug report on the *cx_Freeze* project page here: https://bitbucket.org/anthony_tuininga/cx_freeze/issue/42/recent-versions-of-gevent-break#comment-11421289

#### RPM Build Location Errors ####

This is most relevant for _Cent OS 5_ and for _openSUSE 13_ but may occur on other systems.

If you get an error about not finding the .tar in the RPM build location you will need to create an `.rpmmacros` file in your home directory for the user you are building with that contains these three lines:

    %_topdir %(echo $HOME)/rpmbuild
    %_smp_mflags -j3
    %__arch_install_post /usr/lib/rpm/check-rpaths /usr/lib/rpm/check-buildroot

#### Building on CentOS 5 and Mac OS X ####

Building on _CentOS 5_ and _Mac OS X_ requires *pyOpenSSL* v0.12 instead of v0.13. In order to get ncpa to build you must change the `requirements.txt` file's pyOpenSSL requirement line to:

    pyOpenSSL==0.12

This should then allow ncpa to be built granting you have already installed all required dependencies.
