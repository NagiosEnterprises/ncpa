Name:           ncpa
Version:        __VERSION__
Release:        1
Vendor:         Nagios Enterprises, LLC
Summary:        A cross-platform active and passive monitoring agent
BuildRoot:      __BUILDROOT__/BUILDROOT/
Prefix:         /usr/local
Group:          Network/Monitoring
License:        Nagios Open Software License Version 1.3
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
mkdir -p %{buildroot}/usr/local/ncpa
mkdir -p %{buildroot}/usr/local/ncpa/var/run
mkdir -p %{buildroot}/etc/init.d/
touch %{buildroot}/usr/local/ncpa/ncpa.crt
touch %{buildroot}/usr/local/ncpa/ncpa.key
cp -rf $RPM_BUILD_DIR/ncpa-%{version}/* %{buildroot}/usr/local/ncpa/
chown -R nagios:nagios %{buildroot}/usr/local/ncpa
installbsd -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/listener_init %{buildroot}/etc/init.d/ncpa_listener
installbsd -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/passive_init %{buildroot}/etc/init.d/ncpa_passive

%clean
rm -rf %{buildroot}

%pre
if [ "$1" == "1" ]; then
    # Install the nagios user and group on fresh install
    if ! lsgroup nagios > /dev/null;
    then
        mkgroup nagios
    fi
    if ! lsuser nagios > /dev/null;
    then
        mkuser groups=nagios nagios
    fi
elif [ "$1" = "2" ]; then
    # Upgrades require the daemons to be stopped
    stopsrc -s ncpa_listener -f
    stopsrc -s ncpa_passive -f
    sleep 2
fi

%post
if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

mkssys -s ncpa_listener -p $RPM_INSTALL_PREFIX/ncpa/ncpa_listener -u 0 -S -n 15 -f 9 -a '-n'
mkssys -s ncpa_passive -p $RPM_INSTALL_PREFIX/ncpa/ncpa_passive -u 0 -S -n 15 -f 9 -a '-n'

# Add entries into inittab
chitab "ncpa_listener:2:once:/usr/bin/startsrc -s ncpa_listener >/dev/null 2>&1"
chitab "ncpa_passive:2:once:/usr/bin/startsrc -s ncpa_passive >/dev/null 2>&1"

# Remove empty cert and key files
if [ "$1" == "1" ]; then
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.crt
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.key
fi

startsrc -s ncpa_listener >/dev/null 2>&1
startsrc -s ncpa_passive >/dev/null 2>&1

%preun
stopsrc -s ncpa_listener -f
stopsrc -s ncpa_passive -f

%files
%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg
%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg.d/example.cfg

%defattr(0755,root,root,-)
/etc/init.d/ncpa_listener
/etc/init.d/ncpa_passive

%defattr(0775,nagios,nagios,-)
/usr/local/ncpa
