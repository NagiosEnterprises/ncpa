PYTHONVER = python2.7
PIPVER = pip2.7
SPHINXBUILD = $(shell which sphinx-build)
NCPAVER = $(shell cat ../VERSION.md)
INSTALLTARGET = /usr/local/ncpa/

.PHONY: build_exe build_doc update_packages update_git build_rpm build_spec

build_exe: build_doc
	mkdir -p ../agent/{plugins,var} 
	echo -n '' > ../agent/var/ncpa_passive.log
	echo -n '' > ../agent/var/ncpa_listener.log
	cd ../agent && $(PYTHONVER) posix.py build_exe
	mv ../docs/_build/html ../agent/build/*/listener/static/help	

build_doc: 
	cd ../docs && make -e SPHINXBUILD="$(PYTHONVER) $(SPHINXBUILD)" html

update_packages:
	$(PIPVER) install -r ../requirements.txt --upgrade

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
	rm -rf ../agent/build

build_rpm: build_spec
	rpmdev-setuptree
	/bin/cp ncpa-$(NCPAVER).tar.gz ~/rpmbuild/SOURCES/
	rm -f ~/rpmbuild/SPECS/ncpa.spec
	/bin/cp -f ncpa.spec ~/rpmbuild/SPECS/
	QA_RPATHS='$[ 0x0002 ]' rpmbuild ~/rpmbuild/SPECS/ncpa.spec -bb
	
