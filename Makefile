.PHONY : clean test
.DEFAULT_GOAL := init

init:

	pipenv install --dev
	pipenv run pre-commit install

check: lint
	pipenv check
	pipenv run bandit --ini .bandit -r process_weather_stations/

lint:
	pipenv run pylint process_weather_stations

start:
	pipenv run func start

requirements:
	pipenv lock -r > requirements.txt

pre-commit: lint
	pipenv check

clean:
	rm -rf build dist .egg .eggs *.egg-info pip-wheel-metadata
	rm -rf htmlcov junit
	rm -f coverage.xml
	rm -f .coverage
