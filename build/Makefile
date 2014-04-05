PYTHONVER = python2.7
PIPVER = pip2.7
SPHINXBUILD = $(shell which sphinx-build)
NCPAVER = $(shell cat ../VERSION.md)
INSTALLTARGET = /usr/local/ncpa/
BASEDIR = ~/Development/ncpa

.PHONY: build_exe build_doc update_packages update_git build_rpm build_spec

build_exe: build_doc
	mkdir -p $(BASEDIR)/agent/plugins 
	mkdir -p $(BASEDIR)/agent/var 
	echo -n '' > $(BASEDIR)/agent/var/ncpa_passive.log
	echo -n '' > $(BASEDIR)/agent/var/ncpa_listener.log
	cd $(BASEDIR)/agent && $(PYTHONVER) setup_posix.py build_exe
	mv $(BASEDIR)/docs/_build/html $(BASEDIR)/agent/build/*/listener/static/help	

build_doc: 
	cd ../docs && make -e SPHINXBUILD="$(PYTHONVER) $(SPHINXBUILD)" html

update_packages:
	$(PIPVER) install -r $(BASEDIR)/requirements.txt --upgrade

update_git:
	git pull origin master

build_tarball: update_git update_packages build_exe
	rm -rf ncpa-$(NCPAVER)
	mv ../agent/build/* ncpa-$(NCPAVER)
	tar zcvf ncpa-$(NCPAVER).tar.gz ncpa-$(NCPAVER)

build_spec: build_tarball
	cat ncpa-partial.spec | sed s/__VERSION__/$(NCPAVER)/g > ncpa.spec
	cd ncpa-$(NCPAVER) && find . -type f | sed 's|^\./\(.*\)|"$(INSTALLTARGET)\1"|g' >> ../ncpa.spec
	
clean:
	rm -rf ncpa-$(NCPAVER)
	rm -rf $(BASEDIR)/agent/build
	rm -f *.rpm
	rm -f *.dmg
	rm -f *.deb
	rm -f ncpa.spec
	rm -f *.tar.gz
	rm -rf debbuild

build_rpm: build_spec
	mkdir -p ~/rpmbuild/SPECS
	mkdir -p ~/rpmbuild/SRPMS
	mkdir -p ~/rpmbuild/RPMS
	mkdir -p ~/rpmbuild/SOURCES
	mkdir -p ~/rpmbuild/BUILD
	/bin/cp ncpa-$(NCPAVER).tar.gz ~/rpmbuild/SOURCES/
	rm -f ~/rpmbuild/SPECS/ncpa.spec
	/bin/cp -f ncpa.spec ~/rpmbuild/SPECS/
	QA_RPATHS='$[ 0x0002 ]' rpmbuild ~/rpmbuild/SPECS/ncpa.spec -bb
	find ~/rpmbuild/RPMS -name 'ncpa-$(NCPAVER)*' -exec cp {} . \;

build_deb: build_rpm
	mkdir debbuild
	cp *.rpm debbuild/
	cd debbuild && alien -c -k -v *.rpm
	cp debbuild/*.deb .
	
build_dmg: build_tarball
	echo 'hi'
