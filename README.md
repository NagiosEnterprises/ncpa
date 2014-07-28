NCPA
====

The awesome NCPA agent - one agent to rule them all


Building on CentOS 5
====
Building on CentOS 5 requires pyOpenSSL v0.12 instead of 0.13. In order to get ncpa to build you must change the <code>requirements.txt</code> file's pyOpenSSL requirement line to:
<pre>
pyOpenSSL=0.12
</pre>

This should then allow ncpa to be built granting you have already installed all required dependencies.
