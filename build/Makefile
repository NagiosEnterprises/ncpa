PYTHONVER = 'python3.5'
PIPVER = 'pip3.5'

.PHONY: build_exe build_doc update_packages update_git

build_exe: build_doc
	cd ../agent && $(PYTHONVER) posix.py build_exe
	mv ../docs/_build/html ../agent/build/*/listener/static/help	

build_doc: 
	cd ../docs && make html

update_packages:
	$(PIPVER) install -r ../requirements.txt --upgrade

update_git:
	git pull origin master
