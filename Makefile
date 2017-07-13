install-test:
	pip install -r requirements/test.txt

install-local:
	pip install -r requirements/local.txt

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