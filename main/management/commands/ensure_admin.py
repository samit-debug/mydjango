import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


def _env_bool(name, default=False):
    value = os.getenv(name, str(default))
    return value.lower() in {'1', 'true', 'yes', 'on'}


class Command(BaseCommand):
    help = 'Create or update the initial owner admin from environment variables.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME') or os.getenv('ADMIN_USERNAME')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD') or os.getenv('ADMIN_PASSWORD')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL') or 'owner@hiti-library.local'

        if not username or not password:
            self.stdout.write('Admin env vars not set; skipping initial admin setup.')
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True

        if created or _env_bool('DJANGO_SUPERUSER_UPDATE_PASSWORD'):
            user.set_password(password)
            changed = True

        if changed:
            user.save()

        action = 'created' if created else 'ready'
        self.stdout.write(self.style.SUCCESS(f'Owner admin {action}: {username}'))
