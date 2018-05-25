Contributing to NCPA
====================

We are always happy to get pull request for really anything that will help make this project great. 
Bug fixes and feature requests require a bit more effort to get included but if you follow this then your 
pull request should get included in no time.

Note that you don't need to know how to write Python in order to contribute! Testing our latest builds in 
your environment is also extremely helpful. Any information on problems you face could help us make NCPA
even better.

Create Your Repo
~~~~~~~~~~~~~~~~

Create your own fork on GitHub to commit your changes to. You may want to use your own branch once you fork 
to make multiple pull requests easier.

Build Your Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to get your NCPA development environment up and running you need to make sure all the pre-reqs have 
been installed and working.

**Set Up Windows Environment**

You will need to install git for windows. Then, download and install:

* `Python 2.7.14 on Windows <https://www.python.org/downloads/release/python-2714/>`_
* OpenSSL for Windows (`Download <https://slproweb.com/download/Win32OpenSSL-1_1_0c.exe>`_)

To set up the python requirements, in `cmd.exe` clone the NCPA repo and run::

	python -m pip install -r resources/requires.txt


**Set Up Linux / Mac OS X Environment**

You will need `git` installed in order to clone the repo to do the following.

Once cloned, to install the prereqs::

    cd ncpa
    ./build/scripts/linux_build_prereqs.sh
    ./build/scripts/linux_build_setup.sh

Running NCPA in Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The below examples assume you are inside the NCPA git working directory.

*Note: You can run both the listener and passive service at the same time.*

**On Windows**

NCPA Listener::

	python agent/windows_debug.py listener

NCPA Passive::

	python agent/windows_debug.py passive

**On Linux / Mac OS X**

NCPA Listener::

	python2.7 agent/ncpa_listener.py -n

NCPA Passive::

	python2.7 agent/ncpa_passive.py -n

Code Readability
~~~~~~~~~~~~~~~~

We suggest following the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ Python coding guidelines as
close as possible, however it is not a requirement to get your code into NCPA. We will work with you to fix
any issues that we see that involve PEP8 or our own styling guidelines.

Test Your Code
~~~~~~~~~~~~~~

Be sure to thoroughly test your code. We do not have full tests set up yet and without them, we need to 
be sure that each pull request does not break functionality. We can help you with this, and will test it
ourselves too, but please make sure to verify your code before submitting your pull requst.

Send A Pull Request
~~~~~~~~~~~~~~~~~~~

Once your code changes are completed, tested, and verified, send the pull request.

The easist way to do this is `from inside GitHub <https://help.github.com/articles/creating-a-pull-request/>`_ 
but you can also run it from the command line. 
