all: install-test test

install-test:
	pip install -r requirements/test.txt

install-local:
	pip install -r requirements/local.txt

collectstatic:
	DJANGO_SETTINGS_MODULE=config.settings.local python manage.py collectstatic --no-input -c

makemigrations:
	DJANGO_SETTINGS_MODULE=config.settings.local python manage.py makemigrations

migrate:
	DJANGO_SETTINGS_MODULE=config.settings.local python manage.py migrate

show-urls:
	DJANGO_SETTINGS_MODULE=config.settings.local python manage.py show_urls

autoflake:
	find . -name '*.py'|grep -v migrations|xargs autoflake --in-place --remove-all-unused-imports --remove-unused-variables

autopep8:
	autopep8 --in-place --recursive --max-line-length=100 --exclude="*/migrations/*" .

lint: autoflake autopep8
	flake8

test: lint
	DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test

run-local:
	DJANGO_SETTINGS_MODULE=config.settings.local python manage.py runserver

build-local-image:
	docker-compose -f local.yml build

run-local-image:
	docker-compose -f local.yml up

build-production-image:
	docker-compose -f production.yml build

publish-image:
	docker login -u="${DOCKER_USERNAME}" -p="${DOCKER_PASSWORD}"
	docker push "${TRAVIS_REPO_SLUG}":"${DOCKER_TAG}"
