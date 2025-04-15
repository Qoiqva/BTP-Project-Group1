import os

from django.core.wsgi import get_wsgi_application


WSGI_APPLICATION = 'api.wsgi.app'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenpie.settings')

application = get_wsgi_application()
