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

test:
	DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test