Name:           ncpa
Version:        __VERSION__
Release:        1%{?dist}
Vendor:         Nagios Enterprises, LLC
Summary:        A cross-platform active and passive monitoring agent
BuildRoot:      __BUILDROOT__/BUILDROOT/
Prefix:         /usr/local
Group:          Network/Monitoring
License:        Nagios Open Software License Version 1.3
URL:            http://assets.nagios.com/downloads/ncpa/docs/html/index.html
Source:         ncpa-%{version}.tar.gz
AutoReqProv:    no

%description
The Nagios Cross-Platform Agent is used with Nagios XI and Nagios Core to run active
and/or passive checks on any operating system. Installs with zero requirements using a
bundled version of Python.

%prep
%setup -q

%build

%install
rm -rf %{buildroot} 
mkdir -p %{buildroot}/usr/local/ncpa
mkdir -p %{buildroot}/etc/init.d/
cp -rf $RPM_BUILD_DIR/ncpa-%{version}/* %{buildroot}/usr/local/ncpa/
chown nagios:nagcmd %{buildroot}/usr/local/ncpa -R
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/listener_init %{buildroot}/etc/init.d/ncpa_listener
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/passive_init %{buildroot}/etc/init.d/ncpa_passive

%clean
rm -rf %{buildroot}

%pre
if ! getent group nagcmd > /dev/null;
then
    groupadd -r nagcmd
fi
if ! getent passwd nagios 2> /dev/null;
then
    useradd -r -g nagcmd nagios
else
    %if 0%{?suse_version} && 0%{?suse_version} < 1210
        usermod -A nagcmd nagios
    %else
        usermod -a -G nagcmd nagios
    %endif
fi

%post
if which chkconfig > /dev/null;
then
    chkconfig --level 3,5 --add ncpa_listener
    chkconfig --level 3,5 --add ncpa_passive
elif which update-rc.d > /dev/null;
then
    update-rc.d ncpa_listener defaults
    update-rc.d ncpa_passive defaults
fi

# Set the directory inside the init scripts
dir=$RPM_INSTALL_PREFIX/ncpa
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa_listener
sed -i "s|_BASEDIR_|BASEDIR=\x22$dir\x22|" /etc/init.d/ncpa_passive

/etc/init.d/ncpa_listener start
/etc/init.d/ncpa_passive start

%preun
/etc/init.d/ncpa_listener stop
/etc/init.d/ncpa_passive stop

%files
%defattr(0755,root,root,-)
/etc/init.d/ncpa_listener
/etc/init.d/ncpa_passive

%defattr(0775,nagios,nagcmd,-)
/usr/local/ncpa
%config /usr/local/ncpa/etc/ncpa.cfg
