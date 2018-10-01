PYTHONVER = python2.7
PYTHONBIN = $(shell which python2.7)
NCPAVER = $(shell cat ../VERSION)
INSTALLTARGET = /usr/local/ncpa/
BUILDROOT = /usr/src/redhat

# Full path of the last Makefile make read. We haven't included other files, so that's us.
makefile_path := $(abspath $(lastword $(MAKEFILE_LIST)))

# Makefile's parent directory with no trailing slash (something like: .../ncpa/build).
makefile_dir := $(patsubst %/,%,$(dir $(makefile_path)))

# The NCPA directory is the Makefile's grandparent.
BASEDIR = $(patsubst %/,%,$(dir $(makefile_dir)))

FLAGS = ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future

.PHONY: build_exe update_git update_packages build_rpm build_spec


build_tarball: update_packages build_exe
	rm -rf ncpa-$(NCPAVER)
	mv ../agent/build/* ncpa-$(NCPAVER)
	tar zcvf ncpa-$(NCPAVER).tar.gz ncpa-$(NCPAVER)

build_spec: build_tarball
	cat resources/ncpa-partial.spec | sed s/__VERSION__/$(NCPAVER)/g | sed s@__BUILDROOT__@$(BUILDROOT)@g > ncpa.spec

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
	rm -rf debbuild
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
	QA_RPATHS='$[ 0x0002 ]' rpmbuild $(BUILDROOT)/SPECS/ncpa.spec -bb --define '_topdir /usr/src/redhat'
	find $(BUILDROOT)/RPMS -name 'ncpa-$(NCPAVER)*' -exec cp {} . \;

build_deb: build_rpm
	mkdir -p debbuild
	cp *.rpm debbuild/
	cd debbuild && alien -c -k -v *.rpm
	cp debbuild/*.deb .

build_dmg: build_tarball
	mkdir NCPA-INSTALL-$(NCPAVER)
	mv ncpa-$(NCPAVER) NCPA-INSTALL-$(NCPAVER)/ncpa
	cp NCPA-INSTALL-$(NCPAVER)/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$(NCPAVER)/ncpa/uninstall.sh
	mv NCPA-INSTALL-$(NCPAVER)/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$(NCPAVER)/install.sh
	install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$(NCPAVER)/ncpa/ncpa_listener
	install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$(NCPAVER)/ncpa/ncpa_passive
	hdiutil create -volname NCPA-$(NCPAVER) -srcfolder NCPA-INSTALL-$(NCPAVER) -ov -format UDZO ncpa-$(NCPAVER).dmg

