# sample ninja makefile

build:
	ninja -v

ninja: build.ninja targets.ninja

build.ninja:
	render-template.py build.ninja srcdir=. bindir=. > $@

targets.ninja:
	render-template.py targets.ninja --srcdir=. --bindir=. targets.yaml > $@

seppuku:
	rm -f targets.ninja

clean:
	ninja -v -t clean
	rm -rf build

.PHONY: build clean build.ninja targets.ninja

# vim: ft=make
# EOF
