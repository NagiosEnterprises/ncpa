Name:           ncpa
Version:        1.4 
Release:        1%{?dist}
Summary:        A Cross Platform Monitoring Agent

Group:          Network/Monitoring
License:        NOSL
URL:            http://assets.nagios.com/downloads/ncpa/docs/html/index.html
Source:         ncpa-1.4.tar.gz
AutoReqProv:    no
%description
Installs on your system with zero requirements and allows for monitoring via
Nagios.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/local/ncpa
mkdir -p %{buildroot}/etc/init.d/
cp %{_builddir}/ncpa-1.4/* %{buildroot}/usr/local/ncpa/ -rf
cp %{_builddir}/ncpa-1.4/build_resources/listener_init %{buildroot}/etc/init.d/ncpa_listener
cp %{_builddir}/ncpa-1.4/build_resources/passive_init %{buildroot}/etc/init.d/ncpa_passive

%clean
rm -rf %{buildroot}

%pre

if ! grep 'nagcmd' /etc/group > /dev/null;
then
    groupadd nagcmd
fi

if ! id nagios 2> /dev/null;
then
    useradd nagios -g nagcmd
fi

%post

chkconfig --level 3,5 --add ncpa_listener
chkconfig --level 3,5 --add ncpa_passive
/etc/init.d/ncpa_listener start
/etc/init.d/ncpa_passive start

%files
%defattr(0775,nagios,nagcmd,-)
/usr/local/ncpa/_bisect.cpython-33m.so
/usr/local/ncpa/_cffi_backend.cpython-33m.so
/usr/local/ncpa/_codecs_cn.cpython-33m.so
/usr/local/ncpa/_codecs_hk.cpython-33m.so
/usr/local/ncpa/_codecs_iso2022.cpython-33m.so
/usr/local/ncpa/_codecs_jp.cpython-33m.so
/usr/local/ncpa/_codecs_kr.cpython-33m.so
/usr/local/ncpa/_codecs_tw.cpython-33m.so
/usr/local/ncpa/_ctypes.cpython-33m.so
/usr/local/ncpa/_datetime.cpython-33m.so
/usr/local/ncpa/_elementtree.cpython-33m.so
/usr/local/ncpa/_hashlib.cpython-33m.so
/usr/local/ncpa/_heapq.cpython-33m.so
/usr/local/ncpa/_json.cpython-33m.so
/usr/local/ncpa/_md5.cpython-33m.so
/usr/local/ncpa/_multibytecodec.cpython-33m.so
/usr/local/ncpa/_multiprocessing.cpython-33m.so
/usr/local/ncpa/_pickle.cpython-33m.so
/usr/local/ncpa/_posixsubprocess.cpython-33m.so
/usr/local/ncpa/_psutil_linux.cpython-33m.so
/usr/local/ncpa/_psutil_posix.cpython-33m.so
/usr/local/ncpa/_random.cpython-33m.so
/usr/local/ncpa/_sha1.cpython-33m.so
/usr/local/ncpa/_sha256.cpython-33m.so
/usr/local/ncpa/_sha512.cpython-33m.so
/usr/local/ncpa/_socket.cpython-33m.so
/usr/local/ncpa/_ssl.cpython-33m.so
/usr/local/ncpa/_struct.cpython-33m.so
/usr/local/ncpa/array.cpython-33m.so
/usr/local/ncpa/atexit.cpython-33m.so
/usr/local/ncpa/binascii.cpython-33m.so
/usr/local/ncpa/build_resources/NagiosSoftwareLicense.txt
/usr/local/ncpa/build_resources/listener_init
/etc/init.d/ncpa_listener
/etc/init.d/ncpa_passive
/usr/local/ncpa/build_resources/passive_init
%config /usr/local/ncpa/etc/ncpa.cfg
/usr/local/ncpa/fcntl.cpython-33m.so
/usr/local/ncpa/grp.cpython-33m.so
/usr/local/ncpa/libpython3.3m.so.1.0
/usr/local/ncpa/library.zip
/usr/local/ncpa/listener/static/css/bootstrap-responsive.css
/usr/local/ncpa/listener/static/css/bootstrap-responsive.min.css
/usr/local/ncpa/listener/static/css/bootstrap.css
/usr/local/ncpa/listener/static/css/bootstrap.min.css
/usr/local/ncpa/listener/static/css/configuration.css
/usr/local/ncpa/listener/static/css/navigator.css
/usr/local/ncpa/listener/static/css/ncpa.css
/usr/local/ncpa/listener/static/help/.buildinfo
/usr/local/ncpa/listener/static/help/_images/windows_installer.jpg
/usr/local/ncpa/listener/static/help/_sources/active.txt
/usr/local/ncpa/listener/static/help/_sources/api.txt
/usr/local/ncpa/listener/static/help/_sources/configuration.txt
/usr/local/ncpa/listener/static/help/_sources/index.txt
/usr/local/ncpa/listener/static/help/_sources/installation.txt
/usr/local/ncpa/listener/static/help/_sources/passive.txt
/usr/local/ncpa/listener/static/help/_static/ajax-loader.gif
/usr/local/ncpa/listener/static/help/_static/basic.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/css/bootstrap-responsive.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/css/bootstrap-responsive.min.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/css/bootstrap.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/css/bootstrap.min.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/img/glyphicons-halflings-white.png
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/img/glyphicons-halflings.png
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/js/bootstrap.js
/usr/local/ncpa/listener/static/help/_static/bootstrap-2.3.2/js/bootstrap.min.js
/usr/local/ncpa/listener/static/help/_static/bootstrap-sphinx.css
/usr/local/ncpa/listener/static/help/_static/bootstrap-sphinx.js
/usr/local/ncpa/listener/static/help/_static/brillant.png
/usr/local/ncpa/listener/static/help/_static/comment-bright.png
/usr/local/ncpa/listener/static/help/_static/comment-close.png
/usr/local/ncpa/listener/static/help/_static/comment.png
/usr/local/ncpa/listener/static/help/_static/contents.png
/usr/local/ncpa/listener/static/help/_static/doctools.js
/usr/local/ncpa/listener/static/help/_static/down-pressed.png
/usr/local/ncpa/listener/static/help/_static/down.png
/usr/local/ncpa/listener/static/help/_static/f6.css
/usr/local/ncpa/listener/static/help/_static/file.png
/usr/local/ncpa/listener/static/help/_static/jquery.js
/usr/local/ncpa/listener/static/help/_static/js/jquery-1.9.1.js
/usr/local/ncpa/listener/static/help/_static/js/jquery-1.9.1.min.js
/usr/local/ncpa/listener/static/help/_static/js/jquery-fix.js
/usr/local/ncpa/listener/static/help/_static/minus.png
/usr/local/ncpa/listener/static/help/_static/navigation.png
/usr/local/ncpa/listener/static/help/_static/plus.png
/usr/local/ncpa/listener/static/help/_static/pygments.css
/usr/local/ncpa/listener/static/help/_static/searchtools.js
/usr/local/ncpa/listener/static/help/_static/solar.css
/usr/local/ncpa/listener/static/help/_static/solarized-dark.css
/usr/local/ncpa/listener/static/help/_static/sphinxdoc.css
/usr/local/ncpa/listener/static/help/_static/subtle_dots.png
/usr/local/ncpa/listener/static/help/_static/underscore.js
/usr/local/ncpa/listener/static/help/_static/up-pressed.png
/usr/local/ncpa/listener/static/help/_static/up.png
/usr/local/ncpa/listener/static/help/_static/websupport.js
/usr/local/ncpa/listener/static/help/active.html
/usr/local/ncpa/listener/static/help/api.html
/usr/local/ncpa/listener/static/help/configuration.html
/usr/local/ncpa/listener/static/help/genindex.html
/usr/local/ncpa/listener/static/help/html/.buildinfo
/usr/local/ncpa/listener/static/help/html/_images/windows_installer.jpg
/usr/local/ncpa/listener/static/help/html/_sources/active.txt
/usr/local/ncpa/listener/static/help/html/_sources/api.txt
/usr/local/ncpa/listener/static/help/html/_sources/configuration.txt
/usr/local/ncpa/listener/static/help/html/_sources/index.txt
/usr/local/ncpa/listener/static/help/html/_sources/installation.txt
/usr/local/ncpa/listener/static/help/html/_sources/introduction.txt
/usr/local/ncpa/listener/static/help/html/_sources/passive.txt
/usr/local/ncpa/listener/static/help/html/_static/ajax-loader.gif
/usr/local/ncpa/listener/static/help/html/_static/basic.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/css/bootstrap-responsive.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/css/bootstrap-responsive.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/css/bootstrap.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/css/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/img/glyphicons-halflings-white.png
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/img/glyphicons-halflings.png
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/js/bootstrap.js
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-2.3.2/js/bootstrap.min.js
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap-theme.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap-theme.css.map
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap-theme.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap.css.map
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/css/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/fonts/glyphicons-halflings-regular.eot
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/fonts/glyphicons-halflings-regular.svg
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/fonts/glyphicons-halflings-regular.ttf
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/fonts/glyphicons-halflings-regular.woff
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/js/bootstrap.js
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-3.1.0/js/bootstrap.min.js
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-sphinx.css
/usr/local/ncpa/listener/static/help/html/_static/bootstrap-sphinx.js
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/amelia/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/cerulean/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/cosmo/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/cyborg/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/flatly/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/journal/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/readable/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/simplex/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/slate/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/spacelab/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/spruce/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/superhero/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-2.3.2/united/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/amelia/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/cerulean/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/cosmo/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/cupid/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/cyborg/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/flatly/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/fonts/glyphicons-halflings-regular.eot
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/fonts/glyphicons-halflings-regular.svg
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/fonts/glyphicons-halflings-regular.ttf
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/fonts/glyphicons-halflings-regular.woff
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/journal/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/lumen/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/readable/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/simplex/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/slate/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/spacelab/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/superhero/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/united/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/bootswatch-3.1.0/yeti/bootstrap.min.css
/usr/local/ncpa/listener/static/help/html/_static/comment-bright.png
/usr/local/ncpa/listener/static/help/html/_static/comment-close.png
/usr/local/ncpa/listener/static/help/html/_static/comment.png
/usr/local/ncpa/listener/static/help/html/_static/doctools.js
/usr/local/ncpa/listener/static/help/html/_static/down-pressed.png
/usr/local/ncpa/listener/static/help/html/_static/down.png
/usr/local/ncpa/listener/static/help/html/_static/file.png
/usr/local/ncpa/listener/static/help/html/_static/jquery.js
/usr/local/ncpa/listener/static/help/html/_static/js/jquery-1.11.0.min.js
/usr/local/ncpa/listener/static/help/html/_static/js/jquery-fix.js
/usr/local/ncpa/listener/static/help/html/_static/minus.png
/usr/local/ncpa/listener/static/help/html/_static/plus.png
/usr/local/ncpa/listener/static/help/html/_static/pygments.css
/usr/local/ncpa/listener/static/help/html/_static/searchtools.js
/usr/local/ncpa/listener/static/help/html/_static/underscore.js
/usr/local/ncpa/listener/static/help/html/_static/up-pressed.png
/usr/local/ncpa/listener/static/help/html/_static/up.png
/usr/local/ncpa/listener/static/help/html/_static/websupport.js
/usr/local/ncpa/listener/static/help/html/active.html
/usr/local/ncpa/listener/static/help/html/api.html
/usr/local/ncpa/listener/static/help/html/configuration.html
/usr/local/ncpa/listener/static/help/html/genindex.html
/usr/local/ncpa/listener/static/help/html/index.html
/usr/local/ncpa/listener/static/help/html/installation.html
/usr/local/ncpa/listener/static/help/html/introduction.html
/usr/local/ncpa/listener/static/help/html/objects.inv
/usr/local/ncpa/listener/static/help/html/passive.html
/usr/local/ncpa/listener/static/help/html/search.html
/usr/local/ncpa/listener/static/help/html/searchindex.js
/usr/local/ncpa/listener/static/help/index.html
/usr/local/ncpa/listener/static/help/installation.html
/usr/local/ncpa/listener/static/help/objects.inv
/usr/local/ncpa/listener/static/help/passive.html
/usr/local/ncpa/listener/static/help/search.html
/usr/local/ncpa/listener/static/help/searchindex.js
/usr/local/ncpa/listener/static/img/glyphicons-halflings-white.png
/usr/local/ncpa/listener/static/img/glyphicons-halflings.png
/usr/local/ncpa/listener/static/js/bootstrap-collapse.js
/usr/local/ncpa/listener/static/js/bootstrap.js
/usr/local/ncpa/listener/static/js/bootstrap.min.js
/usr/local/ncpa/listener/static/js/d3.v3.min.js
/usr/local/ncpa/listener/static/js/jquery-1.8.3.min.js
/usr/local/ncpa/listener/templates/base.html
/usr/local/ncpa/listener/templates/config.html
/usr/local/ncpa/listener/templates/dashboard.html
/usr/local/ncpa/listener/templates/login.html
/usr/local/ncpa/listener/templates/main.html
/usr/local/ncpa/listener/templates/navigator.html
/usr/local/ncpa/listener/templates/plugins.html
/usr/local/ncpa/listener/templates/processes.html
/usr/local/ncpa/markupsafe._speedups.so
/usr/local/ncpa/math.cpython-33m.so
/usr/local/ncpa/mmap.cpython-33m.so
/usr/local/ncpa/ncpa_posix_listener
/usr/local/ncpa/ncpa_posix_passive
/usr/local/ncpa/parser.cpython-33m.so
/usr/local/ncpa/passive/__init__.py
/usr/local/ncpa/passive/abstract.py
/usr/local/ncpa/passive/nrdp.py
/usr/local/ncpa/passive/nrdp_test.py
/usr/local/ncpa/passive/nrds.py
/usr/local/ncpa/passive/requirements.txt
/usr/local/ncpa/passive/utils.py
/usr/local/ncpa/passive/welf.py
/usr/local/ncpa/pyexpat.cpython-33m.so
/usr/local/ncpa/select.cpython-33m.so
/usr/local/ncpa/termios.cpython-33m.so
/usr/local/ncpa/time.cpython-33m.so
/usr/local/ncpa/unicodedata.cpython-33m.so
/usr/local/ncpa/var/ncpa_listener.log
/usr/local/ncpa/var/ncpa_passive.log
/usr/local/ncpa/zlib.cpython-33m.so
"/usr/local/ncpa/listener/static/js/d3.js - LICENSE"
%changelog
