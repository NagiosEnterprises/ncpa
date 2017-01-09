Name:           ncpa
Version:        __VERSION__
Release:        1%{?dist}
Vendor:         Nagios Enterprises, LLC
Summary:        A cross-platform active and passive monitoring agent
BuildRoot:      __BUILDROOT__/BUILDROOT/
Prefix:         /usr/local
Group:          Network/Monitoring
License:        Nagios Open Software License Version 1.3
URL:            https://www.nagios.org/ncpa/
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
chown nagios:nagios %{buildroot}/usr/local/ncpa -R
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/ncpa_init %{buildroot}/etc/init.d/ncpa

%clean
rm -rf %{buildroot}

%pre
if [ `command -v systemctl` ]; then
    systemctl stop ncpa_listener &> /dev/null || true
    systemctl stop ncpa_passive &> /dev/null || true
    systemctl stop ncpa &> /dev/null || true
else
    service ncpa_listener stop &> /dev/null || true
    service ncpa_passive stop &> /dev/null || true
    service ncpa stop &> /dev/null || true
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
    chkconfig --level 3,5 --add ncpa &> /dev/null
elif which update-rc.d > /dev/null; then
    update-rc.d ncpa defaults &> /dev/null
fi

if [ -z $RPM_INSTALL_PREFIX ]; then
    RPM_INSTALL_PREFIX="/usr/local"
fi

# Set the directory inside the init scripts
dir=$RPM_INSTALL_PREFIX/ncpa
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa

# Remove empty cert and key files
rm $RPM_INSTALL_PREFIX/ncpa/ncpa.crt
rm $RPM_INSTALL_PREFIX/ncpa/ncpa.key

if [ `command -v systemctl` ]; then
    systemctl daemon-reload
    systemctl start ncpa
else
    service ncpa start
fi

%preun
if [ `command -v systemctl` ]; then
    systemctl stop ncpa
else
    service ncpa stop
fi

%files
%defattr(0755,root,root,-)
/etc/init.d/ncpa

%defattr(0775,nagios,nagios,-)
/usr/local/ncpa

%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg
%config(noreplace) /usr/local/ncpa/etc/ncpa.cfg.d/example.cfg
