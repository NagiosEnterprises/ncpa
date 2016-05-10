= Testing

A quick testing doc to hold us over until we get time to right a more
complete document.

== Idea

The idea is to have our testing and our development boxes totally separate and
parallelizable. So the current setup is to have your ncpa dev container. Lets
say I've initialized it with:

```
docker run -i -t --name ncpadev -v /path/to/ncpa/:/src/ncpa ncpadev
```

Now you'r dev box is running and you're humming along.

Create the testing container, note the paths are pretty important:

```
docker run -i -t --name ncpatesting -e
NCPA_TESTING_TARGET='NCPADEV_PORT_5693_TCP' --link ncpadev:ncpadev -v
/path/to/ncpa/testing:/tests ncpatesting /bin/bash
```

A long command to be sure, but that will create the container. Then run the
tests (inside the container):

```
python /tests/run.py
```

There aren't many tests right now.

== Schema

Look at the form of the directories, they contain a name for the test, a URL to
hit to get API results and schema folder that is JSON that describes the exact
schema we should expect back. A lot of these will be generateable right now.
