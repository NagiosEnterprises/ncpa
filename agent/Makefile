.PHONY: build
build: clean
	python2.6 posix.py build_exe
	cp build_resources/build_package.sh .

install:
	mv build/exe.linux-* /usr/local/ncpa

clean:
	rm dist -rf
	rm build -rf
	rm buildtest -rf
	rm postinstall-pak -f
	rm postremove-pak -f
	rm description-pak -f
	rm build_package.sh -f
	rm build-pkg -rf
	rm *.tgz -f
	rm *.deb -f
	rm *.rpm -f
