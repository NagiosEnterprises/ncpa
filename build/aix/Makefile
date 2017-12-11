PYTHONVER = python2.7
PYTHONBIN = $(shell which python2.7)
NCPAVER = $(shell cat ../VERSION)
INSTALLTARGET = /usr/local/ncpa/
BUILDROOT = /tmp/test/usr/src/redhat
BASEDIR = /tmp/test/ncpa

FLAGS = ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future

.PHONY: build_exe build_rpm build_spec

build_exe: clean
	find $(BASEDIR) -name *.pyc -exec rm -rf {} \;
	mkdir -p $(BASEDIR)/agent/plugins
	mkdir -p $(BASEDIR)/agent/var
	mkdir -p $(BASEDIR)/agent/build
	echo -n '' > $(BASEDIR)/agent/var/log/ncpa_passive.log
	echo -n '' > $(BASEDIR)/agent/var/log/ncpa_listener.log
	cd $(BASEDIR)/agent && $(PYTHONVER) setup_posix.py build_exe
	mv $(BASEDIR)/agent/build/exe.* $(BASEDIR)/agent/build/NCPA

build_tarball: build_exe
	rm -rf ncpa-$(NCPAVER)
	mv ../../agent/build/* ncpa-$(NCPAVER)
	tar cvf ncpa-$(NCPAVER).tar ncpa-$(NCPAVER)
	gzip ncpa-$(NCPAVER).tar

build_spec: build_tarball
	cat ncpa-aix-partial.spec | sed s/__VERSION__/$(NCPAVER)/g | sed s@__BUILDROOT__@$(BUILDROOT)@g > ncpa.spec

clean:
	rm -rf ncpa-*
	rm -rf $(BASEDIR)/agent/build
	rm -rf NCPA-INSTALL-*
	rm -f *.rpm
	rm -f *.dmg
	rm -f *.deb
	rm -f ncpa.spec
	rm -f *.tar.gz
	rm -rf $(BUILDROOT)
	rm -f *.log

build_rpm: build_spec
	mkdir -p $(BUILDROOT)/SPECS
	mkdir -p $(BUILDROOT)/SRPMS
	mkdir -p $(BUILDROOT)/RPMS
	mkdir -p $(BUILDROOT)/SOURCES
	mkdir -p $(BUILDROOT)/BUILD
	/bin/cp ncpa-$(NCPAVER).tar.gz $(BUILDROOT)/SOURCES/
	rm -f $(BUILDROOT)/SPECS/ncpa.spec
	/bin/cp -f ncpa.spec $(BUILDROOT)/SPECS/
	rpmbuild -bb --define '_topdir $(BUILDROOT)' $(BUILDROOT)/SPECS/ncpa.spec
	find $(BUILDROOT)/RPMS -name 'ncpa-$(NCPAVER)*' -exec cp {} . \;
