"""
WSGI config for car_sharing project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_sharing.settings')

application = get_wsgi_application()
