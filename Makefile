
output_dir = dist
ifeq ($(OS),Windows_NT)
	RM := rmdir /S /Q
else
	RM := rm -rf
endif

cleandir:
	-$(RM) $(output_dir)

standalone:
	make cleandir
	pyinstaller --clean --noconfirm .build/piveilance.spec

wheel:
	make cleandir
	python setup.py sdist --formats=gztar  bdist_wheel

all:
	make wheel
	make standalone

upload:
	twine upload dist/*.tar.gz dist/*.whl