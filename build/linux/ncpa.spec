Name:           ncpa
Version:        __VERSION__
Release:        1%{?dist}
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
chown -R nagios:nagios %{buildroot}/usr/local/ncpa
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/listener_init %{buildroot}/etc/init.d/ncpa_listener
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/passive_init %{buildroot}/etc/init.d/ncpa_passive

%clean
rm -rf %{buildroot}

%pre
if [ `command -v systemctl` ]; then
    systemctl stop ncpa_listener &> /dev/null || true
    systemctl stop ncpa_passive &> /dev/null || true
else
    service ncpa_listener stop &> /dev/null || true
    service ncpa_passive stop &> /dev/null || true
fi

if ! getent group nagios > /dev/null;
then
    groupadd -r nagios
fi
if ! getent passwd nagios > /dev/null;
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
    chkconfig --level 3,5 --add ncpa_listener &> /dev/null
    chkconfig --level 3,5 --add ncpa_passive &> /dev/null
elif which update-rc.d > /dev/null; then
    update-rc.d ncpa_listener defaults &> /dev/null
    update-rc.d ncpa_passive defaults &> /dev/null
fi

if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Set the directory inside the init scripts
dir=$RPM_INSTALL_PREFIX/ncpa
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa_listener
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa_passive

# Remove empty cert and key files
if [ -f $RPM_INSTALL_PREFIX/ncpa/ncpa.crt ]; then
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.crt
fi
if [ -f $RPM_INSTALL_PREFIX/ncpa/ncpa.key ]; then
    rm $RPM_INSTALL_PREFIX/ncpa/ncpa.key
fi

if [ `command -v systemctl` ]; then
    systemctl daemon-reload
    systemctl start ncpa_listener
    systemctl start ncpa_passive
else
    service ncpa_listener start
    service ncpa_passive start
fi

%preun
# Only stop on actual uninstall not upgrades
if [ "$1" != "1" ]; then
    if [ `command -v systemctl` ]; then
        systemctl stop ncpa_listener
        systemctl stop ncpa_passive
    else
        service ncpa_listener stop
        service ncpa_passive stop
    fi
fi

%posttrans
if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Only run on upgrades (restart fixes db removal issue)
if [ ! -f "$RPM_INSTALL_PREFIX/ncpa/var/ncpa.db" ]; then
    if [ `command -v systemctl` ]; then
        systemctl restart ncpa_listener
        systemctl restart ncpa_passive
    else
        service ncpa_listener restart
        service ncpa_passive restart
    fi
fi

%files
%defattr(0755,root,root,0755)
%dir /usr/local/ncpa
/usr/local/ncpa/ncpa_listener
/usr/local/ncpa/ncpa_passive
/etc/init.d/ncpa_listener
/etc/init.d/ncpa_passive

%defattr(0755,root,root,0755)
/usr/local/ncpa/*.so*

%defattr(0644,root,root,0755)
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
