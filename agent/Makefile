posix-environment:
	yum localinstall http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm --nogpgcheck -y
	yum install python26 python26-devel gcc glibc python26-setuptools -y
	easy_install-2.6 pip cx_Freeze
	pip-2.6 install -r ../requirements.txt

posix-prereq:
	curl -L http://sourceforge.net/projects/pyinstaller/files/2.0/pyinstaller-2.0.tar.bz2/download?use_mirror=kent -o /tmp/pyinstaller.tar.bz2
	tar xf /tmp/pyinstaller.tar.bz2 --strip 1

posix-statics:
	touch var/ncpa_listener.log
	touch var/ncpa.log  
	touch var/ncpa_passive.log

posix-build: posix-environment posix-prereq posix-statics
	svn update ..
	python2.6 pyinstaller.py posix.spec
