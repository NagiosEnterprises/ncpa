PYTHONVER = python2.7
PIPVER = pip2.7
CXFREEZEVER = cx_Freeze-4.3.4
PYTHONBIN = $(shell which python2.7)
SPHINXBIN = $(shell which sphinx-build)
NCPAVER = $(shell cat ../VERSION.md)
BUILDBRANCH = $(shell cat /vagrant/buildbranch || echo "master")
INSTALLTARGET = /usr/local/ncpa/
BUILDROOT = /usr/src/redhat

#BASEDIR = ~/Development/ncpa
# Full path of the last Makefile make read. We haven't included other files, so that's us.
makefile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
# Makefile's parent directory with no trailing slash (something like: .../ncpa/build).
makefile_dir := $(patsubst %/,%,$(dir $(makefile_path)))
# The NCPA directory is the Makefiile's grandparent.
BASEDIR = $(patsubst %/,%,$(dir $(makefile_dir)))

FLAGS = ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future

.PHONY: build_exe build_doc update_git update_packages build_rpm build_spec update_version

build_exe: clean update_version build_doc
	find $(BASEDIR) -name *.pyc -delete
	mkdir -p $(BASEDIR)/agent/plugins
	mkdir -p $(BASEDIR)/agent/var
	echo -n '' > $(BASEDIR)/agent/var/ncpa_passive.log
	echo -n '' > $(BASEDIR)/agent/var/ncpa_listener.log
	cd $(BASEDIR)/agent && $(PYTHONVER) setup_posix.py build_exe
	cp -f $(BASEDIR)/docs/_build/html $(BASEDIR)/docs/_build/help || :
	/bin/cp -rf $(BASEDIR)/docs/_build/help $(BASEDIR)/agent/build/*/listener/static
	rm -rf $(BASEDIR)/docs/_build/help

build_doc:
	cd ../docs && make -e SPHINXBUILD="$(PYTHONVER) $(SPHINXBIN)" html

update_packages:
	$(FLAGS) $(PIPVER) install -r $(BASEDIR)/requirements.txt --upgrade
	wget http://assets.nagios.com/downloads/ncpa/dev/$(CXFREEZEVER)-patched.tar.gz
	tar xf $(CXFREEZEVER)-patched.tar.gz
	cd $(CXFREEZEVER) && $(PYTHONBIN) setup.py install

update_git:
	git pull
	git checkout -f $(BUILDBRANCH)

build_tarball: update_git update_packages build_exe
	rm -rf ncpa-$(NCPAVER)
	mv ../agent/build/* ncpa-$(NCPAVER)
	tar zcvf ncpa-$(NCPAVER).tar.gz ncpa-$(NCPAVER)

build_spec: build_tarball
	cat ncpa-partial.spec | sed s/__VERSION__/$(NCPAVER)/g | sed s@__BUILDROOT__@$(BUILDROOT)@g > ncpa.spec

clean:
	rm -rf ncpa-$(NCPAVER)
	rm -rf $(BASEDIR)/agent/build
	rm -rf NCPA-INSTALL-$(NCPAVER)
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
	mv NCPA-INSTALL-$(NCPAVER)/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$(NCPAVER)/install.sh
	hdiutil create -volname NCPA-$(NCPAVER) -srcfolder NCPA-INSTALL-$(NCPAVER) -ov -format UDZO ncpa-$(NCPAVER).dmg

update_version:
	$(PYTHONVER) $(BASEDIR)/apply_version.py
