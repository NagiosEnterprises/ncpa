Name:           ncpa
Version:        __VERSION__ 
Release:        1%{?dist}
Summary:        A Cross Platform Monitoring Agent
BuildRoot:	~/rpmbuild/BUILDROOT/
Group:          Network/Monitoring
License:        NOSL
URL:            http://assets.nagios.com/downloads/ncpa/docs/html/index.html
Source:         ncpa-%{version}.tar.gz
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
cp -rf $RPM_BUILD_DIR/ncpa-%{version}/* %{buildroot}/usr/local/ncpa/ 
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/listener_init %{buildroot}/etc/init.d/ncpa_listener
install -m 755 $RPM_BUILD_DIR/ncpa-%{version}/build_resources/passive_init %{buildroot}/etc/init.d/ncpa_passive

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
/etc/init.d/ncpa_listener
/etc/init.d/ncpa_passive
/usr/local/ncpa/plugins
%config /usr/local/ncpa/etc/ncpa.cfg

