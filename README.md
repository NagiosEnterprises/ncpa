NCPA
====

The awesome NCPA agent - one agent to rule them all.


Building NCPA
====

There are known build issues involving cx_Freeze, if you run into an issue refer to the bug report on the cx_Freeze project page here: https://bitbucket.org/anthony_tuininga/cx_freeze/issue/42/recent-versions-of-gevent-break#comment-11421289


Building on CentOS 5
====

Building on CentOS 5 requires pyOpenSSL v0.12 instead of 0.13. In order to get ncpa to build you must change the <code>requirements.txt</code> file's pyOpenSSL requirement line to:
<pre>
pyOpenSSL==0.12
</pre>

This should then allow ncpa to be built granting you have already installed all required dependencies.
