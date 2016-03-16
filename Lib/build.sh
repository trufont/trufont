if [ $(uname) == 'Darwin' ]; then
	python setup.py py2app
else
	pyinstaller --onefile TruFont.spec
fi
