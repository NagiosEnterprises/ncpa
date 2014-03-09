Name:           ncpa
Version:        1.4 
Release:        1%{?dist}
Summary:        A Cross Platform Monitoring Agent

Group:          Network/Monitoring
License:        NOSL
URL:            http://assets.nagios.com/downloads/ncpa/docs/html/index.html
Source:         ncpa-1.4.tar.gz

%description
Installs on your system with zero requirements and allows for monitoring via
Nagios.

%prep
%setup -q


%build
#%configure
#make %{?_smp_mflags}


%install
#rm -rf $RPM_BUILD_ROOT
#make install DESTDIR=$RPM_BUILD_ROOT


%clean
#rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc



%changelog
