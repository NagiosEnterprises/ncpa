Name:           ncpa
Version:        __VERSION__
Release:        1%{?dist}
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

%global debug_package %{nil}
%global _build_id_links alldebug

%prep
%setup -q

%build
%define _python_bytecompile_errors_terminate_build 0

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/local
cp -rf $RPM_BUILD_DIR/ncpa-%{version} %{buildroot}/usr/local/ncpa
mkdir -p %{buildroot}/usr/local/ncpa/var/run
mkdir -p %{buildroot}/etc/init.d
touch %{buildroot}/usr/local/ncpa/var/ncpa.db
chown nagios:nagios %{buildroot}/usr/local/ncpa -R
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/default-init %{buildroot}/etc/init.d/ncpa

%clean
rm -rf %{buildroot}

%pre
if command -v systemctl > /dev/null
then
    systemctl stop ncpa &> /dev/null || true
else
    service ncpa stop &> /dev/null || true
fi

if ! getent group nagios > /dev/null
then
    groupadd -r nagios
fi

if ! getent passwd nagios > /dev/null
then
    useradd -r -g nagios nagios
else
    %if 0%{?suse_version} && 0%{?suse_version} < 1210
        usermod -A nagios nagios
    %else
        usermod -a -G nagios nagios
    %endif
fi

%post
if which chkconfig > /dev/null; then
    chkconfig --level 3,5 --add ncpa &> /dev/null
elif which update-rc.d > /dev/null; then
    update-rc.d ncpa defaults &> /dev/null
fi

if [ -z $RPM_INSTALL_PREFIX ]
then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Set the directory inside the init scripts
dir=$RPM_INSTALL_PREFIX/ncpa
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa

# Remove empty cert and key files
if [ -f $RPM_INSTALL_PREFIX/ncpa/ncpa.crt ]
then
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.crt
fi

if [ -f $RPM_INSTALL_PREFIX/ncpa/ncpa.key ]
then
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.key
fi

if command -v systemctl > /dev/null
then
    systemctl daemon-reload
    systemctl start ncpa
else
    service ncpa start
fi

%preun
# Only stop on actual uninstall not upgrades
# TODO: Make upgrades from NCPA 2 -> 3 seemless (stop old services)
if [ "$1" != "1" ]; then
    if [ `command -v systemctl` ]; then
        systemctl stop ncpa
    else
        service ncpa stop
    fi
fi

%postun
# Only do systemctl daemon-reload after uninstall
if [ "$1" == "0" ]
then
    if command -v systemctl > /dev/null
    then
        systemctl daemon-reload
    fi
fi

%posttrans
if [ -z $RPM_INSTALL_PREFIX ]
then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Only run on upgrades (restart fixes db removal issue)
if [ ! -f "$RPM_INSTALL_PREFIX/ncpa/var/ncpa.db" ]
then
    if command -v systemctl > /dev/null
    then
        systemctl restart ncpa
    else
        service ncpa restart
    fi
fi

%files
/usr/local/ncpa/python*
/usr/local/ncpa/python*.*

%defattr(0755,root,root,0755)
%dir /usr/local/ncpa
/usr/local/ncpa/ncpa
/etc/init.d/ncpa

%defattr(0755,root,root,0755)
/usr/local/ncpa/lib/*.so*

%defattr(0644,root,root,0755)
/usr/local/ncpa/lib/*.py
/usr/local/ncpa/lib/*.zip
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
