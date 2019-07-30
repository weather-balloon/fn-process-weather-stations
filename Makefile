.PHONY : clean test
.DEFAULT_GOAL := init

init:
	/usr/bin/env python3 -m pip install pipenv --upgrade

	# Use --pre as the Azure libs aren't at final release yet
	pipenv install --dev --pre

check:
	pipenv check

lint:
	pylint ProcessWeatherStations

#test: 
	#pipenv run tox

start:
	pipenv run func start

pre-commit: lint 	

clean:
	rm -rf build dist .egg .eggs *.egg-info pip-wheel-metadata
	rm -rf htmlcov junit
	rm -f coverage.xml
	rm -f .coverage
