"""
WSGI config for lddt_tracking_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os, sys

sys.path.append('/apps/www/tracking')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lddt_tracking_app.settings')

application = get_wsgi_application()
