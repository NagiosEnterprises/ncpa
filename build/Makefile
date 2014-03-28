PYTHONVER = 'python3.5'
PIPVER = 'pip3.5'

.PHONY: build_exe build_doc update_packages update_git build_rpm

build_exe: build_doc
	echo -n '' > ../agent/var/ncpa_{listener,passive}.log
	cd ../agent && $(PYTHONVER) posix.py build_exe
	mv ../docs/_build/html ../agent/build/*/listener/static/help	

build_doc: 
	cd ../docs && make html

update_packages:
	$(PIPVER) install -r ../requirements.txt --upgrade

update_git:
	git pull origin master

build_rpm: update_git update_packages build_exe
	echo 'Building rpm'
