posix-environment:
	yum localinstall http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm --nogpgcheck -y
	yum install python26 python26-devel gcc glibc python26-setuptools -y
	wget http://downloads.sourceforge.net/project/cx-freeze/4.3.1/cx_Freeze-4.3.1.tar.gz?r=http%3A%2F%2Fcx-freeze.sourceforge.net%2F&ts=1369769807&use_mirror=hivelocity
	tar xf cx_Freeze-4.3.1.tar.gz 
	pushd cx_Freeze-4.3.1
	python26 setup.py install
	pushd
	pip-2.6 install -r ../requirements.txt

posix-statics:
	touch var/ncpa_listener.log
	touch var/ncpa.log  
	touch var/ncpa_passive.log

posix-build: posix-statics
	python2.6 posix.py build_exe

clean:
	rm dist -rf
	rm built -rf
	rm buildtest -rf
