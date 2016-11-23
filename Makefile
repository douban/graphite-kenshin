init:
	test -d ${GraphiteKenshinVenv} || virtualenv ${GraphiteKenshinVenv}

install: init
	source ${GraphiteKenshinVenv}/bin/activate; pip install -r pip-req.txt
	source ${GraphiteKenshinVenv}/bin/activate; python setup.py install

restart_web:
	${RestartGraphiteAPI}
