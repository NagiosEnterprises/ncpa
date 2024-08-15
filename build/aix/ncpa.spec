%define _source_filedigest_algorithm 8
%define _binary_filedigest_algorithm 8

Name:           ncpa
Version:        __VERSION__
Release:        1
Vendor:         Nagios Enterprises, LLC
Summary:        A cross-platform active and passive monitoring agent
BuildRoot:      __BUILDROOT__/BUILDROOT/
Prefix:         /usr/local
Group:          Network/Monitoring
License:        Nagios Community Software License Version 1.3
URL:            https://www.nagios.org/ncpa/help.php
Source:         ncpa-%{version}.tar.gz
AutoReqProv:    no

%description
The Nagios Cross-Platform Agent is used with Nagios XI and Nagios Core to run active
and/or passive checks on any operating system. Installs with zero requirements using a
bundled version of Python.

%prep
%setup -q

%build
%define _python_bytecompile_errors_terminate_build 0

%install
rm -rf %{buildroot} 
mkdir -p %{buildroot}/usr/local
cp -rf $RPM_BUILD_DIR/ncpa-%{version} %{buildroot}/usr/local/ncpa
mkdir -p %{buildroot}/usr/local/ncpa/var/run
chown -R nagios:nagios %{buildroot}/usr/local/ncpa

%clean
rm -rf %{buildroot}

%pre
if [ "$1" == "1" ]; then
    # Install the nagios user and group on fresh install
    if ! lsgroup nagios >/dev/null 2>&1;
    then
        mkgroup nagios
    fi
    if ! lsuser nagios >/dev/null 2>&1;
    then
        mkuser groups=nagios nagios
    fi
elif [ "$1" = "2" ]; then
    # Upgrades require the daemons to be stopped
    if lssrc -s ncpa | grep -q "active"; then
        stopsrc -s ncpa -f >/dev/null 2>&1
    fi
    sleep 2
fi

%post
if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Install/update SRC and add entries into inittab and remove blank files on install
if [ "$1" == "1" ]; then
    mkssys -s ncpa -p $RPM_INSTALL_PREFIX/ncpa/ncpa -u 0 -S -n 15 -f 9 >/dev/null 2>&1

    mkitab "ncpa:2:once:/usr/bin/startsrc -s ncpa >/dev/null 2>&1"
    rm -rf $RPM_INSTALL_PREFIX/ncpa/var/ncpa.*
elif [ "$1" == "2" ]; then
    chitab "ncpa:2:once:/usr/bin/startsrc -s ncpa >/dev/null 2>&1"
fi

# Start the daemons using SRC
startsrc -s ncpa >/dev/null 2>&1

%preun
if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Only stop on actual uninstall not upgrades
if [ "$1" != "1" ]; then

    if lssrc -s ncpa | grep -q "active"; then
        stopsrc -s ncpa >/dev/null 2>&1
    fi

    # Make sure listener is stopped
    stopped=`lssrc -s ncpa | sed -n '$p' | awk '{print $NF}'`
    while [[ "$stopped" != "inoperative" ]]; do
        sleep 3
        stopped=`lssrc -s ncpa | sed -n '$p' | awk '{print $NF}'`
        if [ "$stopped" == "file." ]; then
            break
        fi
    done
    
    # Remove from inittab
    rmitab "ncpa"

    # Remove from SRC
    rmssys -s ncpa >/dev/null 2>&1
    
    # Remove key, certs, and db
    rm -f $RPM_INSTALL_PREFIX/ncpa/var/ncpa.key
    rm -f $RPM_INSTALL_PREFIX/ncpa/var/ncpa.crt
    rm -f $RPM_INSTALL_PREFIX/ncpa/var/ncpa.db
fi

%files
%defattr(0755,root,root,0755)
%dir /usr/local/ncpa
/usr/local/ncpa/ncpa

%defattr(0755,root,root,0755)
/usr/local/ncpa/*.so*

%defattr(0644,root,root,0755)
/usr/local/ncpa/*.a
/usr/local/ncpa/*.py
/usr/local/ncpa/*.zip
/usr/local/ncpa/build_resources
/usr/local/ncpa/listener
/usr/local/ncpa/plugins

%defattr(0664,root,nagios,0775)
%dir /usr/local/ncpa/etc
%dir /usr/local/ncpa/etc/ncpa.cfg.d
/usr/local/ncpa/var

%defattr(0640,root,nagios,0755)
%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg
%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg.d/example.cfg
/usr/local/ncpa/etc/ncpa.cfg.sample
/usr/local/ncpa/etc/ncpa.cfg.d/README.txt
