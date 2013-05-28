%define _topdir	 	/tmp/ncpa/agent/build
%define name		NCPA
%define release		1
%define version 	1.0
%define buildroot %{_topdir}/%{name}-%{version}-root

Summary: NCPA a cross-platform agent
Name: ncpa
Version: %{version}
Release: %{release}
License: GPL
Group: Monitoring
Source: %{name}-%{version}.tar.gz
BuildRoot: /var/tmp/%{name}-buildroot

%description
Monitor all of your servers with the same agent.

%prep
%setup -q

%install
mkdir -p $RPM_BUILD_ROOT/usr/local/ncpa
mv * $RPM_BUILD_ROOT/usr/local/ncpa/
chown nagios.nagcmd /usr/local/ncpa -R
chmod 755 /usr/local/ncpa -R

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/local/ncpa/
/usr/local/ncpa/itertoolsmodule.so
/usr/local/ncpa/zlibmodule.so
/usr/local/ncpa/_socketmodule.so
/usr/local/ncpa/_codecs_jp.so
/usr/local/ncpa/cPickle.so
/usr/local/ncpa/build_resources
/usr/local/ncpa/build_resources/passive_init
/usr/local/ncpa/build_resources/NagiosSoftwareLicense.txt
/usr/local/ncpa/build_resources/listener_init
/usr/local/ncpa/selectmodule.so
/usr/local/ncpa/_codecs_tw.so
/usr/local/ncpa/_sha512module.so
/usr/local/ncpa/_randommodule.so
/usr/local/ncpa/passive
/usr/local/ncpa/passive/nrds.pyc
/usr/local/ncpa/passive/abstract.py
/usr/local/ncpa/passive/nrds.py
/usr/local/ncpa/passive/__init__.py
/usr/local/ncpa/passive/nrdp.py
/usr/local/ncpa/passive/utils.py
/usr/local/ncpa/passive/__init__.pyc
/usr/local/ncpa/passive/nrdp.pyc
/usr/local/ncpa/passive/utils.pyc
/usr/local/ncpa/passive/abstract.pyc
/usr/local/ncpa/_codecs_kr.so
/usr/local/ncpa/unicodedata.so
/usr/local/ncpa/libpython2.6.so.1.0
/usr/local/ncpa/mathmodule.so
/usr/local/ncpa/etc
/usr/local/ncpa/etc/ncpa.cfg
/usr/local/ncpa/_ctypes.so
/usr/local/ncpa/_ssl.so
/usr/local/ncpa/_localemodule.so
/usr/local/ncpa/_json.so
/usr/local/ncpa/stropmodule.so
/usr/local/ncpa/_psutil_linux.so
/usr/local/ncpa/_codecs_iso2022.so
/usr/local/ncpa/plugins
/usr/local/ncpa/plugins/yancyforprez.sh
/usr/local/ncpa/pyexpat.so
/usr/local/ncpa/fcntlmodule.so
/usr/local/ncpa/OpenSSL.crypto.so
/usr/local/ncpa/_collectionsmodule.so
/usr/local/ncpa/grpmodule.so
/usr/local/ncpa/_elementtree.so
/usr/local/ncpa/OpenSSL.SSL.so
/usr/local/ncpa/_md5module.so
/usr/local/ncpa/_weakref.so
/usr/local/ncpa/_struct.so
/usr/local/ncpa/bz2.so
/usr/local/ncpa/binascii.so
/usr/local/ncpa/ncpa_posix_passive
/usr/local/ncpa/timemodule.so
/usr/local/ncpa/termios.so
/usr/local/ncpa/readline.so
/usr/local/ncpa/arraymodule.so
/usr/local/ncpa/datetime.so
/usr/local/ncpa/_functoolsmodule.so
/usr/local/ncpa/_bisectmodule.so
/usr/local/ncpa/ncpa_posix_listener
/usr/local/ncpa/_hashlib.so
/usr/local/ncpa/var
/usr/local/ncpa/var/ncpa_passive.log
/usr/local/ncpa/var/ncpa_listener.log
/usr/local/ncpa/_codecs_cn.so
/usr/local/ncpa/library.zip
/usr/local/ncpa/_codecs_hk.so
/usr/local/ncpa/_heapq.so
/usr/local/ncpa/operator.so
/usr/local/ncpa/OpenSSL.rand.so
/usr/local/ncpa/_multibytecodecmodule.so
/usr/local/ncpa/_bytesio.so
/usr/local/ncpa/_sha256module.so
/usr/local/ncpa/_fileio.so
/usr/local/ncpa/cStringIO.so
/usr/local/ncpa/_psutil_posix.so
/usr/local/ncpa/listener
/usr/local/ncpa/listener/templates
/usr/local/ncpa/listener/static
/usr/local/ncpa/_shamodule.so
