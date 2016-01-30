Development
===========

Getting a development environment right now is up limited to Linux at the
moment. It also requires docker to get up and going. For information on
installing docker please see `Docker Documentation <https://docs.docker.com/engine/installation/>`_.

Docker Build
*************

Pull the NCPA repo::

    git pull https://github.com/NagiosEnterprises/ncpa.git

Move into it::

    cd ncpa

Checkout the development branch::

    docker build -t ncpadev .

Go grab a coffee while it builds.

Active Agent
************

Simply running::

    docker run -i -t -p 5693:5693 ncpadev

It would probably be a good idea to alias this if you're going to be heavy development.

This will spin up an ncpa instance active instance. If you're running Mac OS X
or Windows as your host OS for docker, then you'll need to run docker-machine
(or whatever management they use) to use the IP address. At any rate, see your
platform specific documentation for finding the IP address.

When you want to edit the code, just edit the code in the git repo that you
checked out, and restart the docker container.

Passive Agent
*************

For this you'll need to go inside the docker container::

    docker run -i -t ncpadev python /src/ncpa/agent/ncpa_posix_passive.py -n

And the passive agent will be run in the foreground. Spamming the logs as usual.
