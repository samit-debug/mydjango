"""
WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()

if os.getenv('RUN_MIGRATIONS_ON_START', 'True').lower() in {'1', 'true', 'yes', 'on'}:
    try:
        call_command('migrate', interactive=False, verbosity=0)
        call_command('ensure_admin', verbosity=0)
    except Exception as exc:
        print(f'Startup database setup failed: {exc}', file=sys.stderr)
