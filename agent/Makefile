.PHONY: build
build:
	python2.6  posix.py build_exe
	cp build_resources/build_package.sh .

install:
	mv build/exe.linux-i686-2.6 /usr/local/ncpa

clean:
	rm dist -rf
	rm built -rf
	rm buildtest -rf
	rm postinstall-pak -f
	rm postremove-pak -f
	rm description-pak -f
	rm build_package.sh -f
