from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_hiti_profile(apps, schema_editor):
    LibraryProfile = apps.get_model('main', 'LibraryProfile')
    Facility = apps.get_model('main', 'Facility')
    StudyPlan = apps.get_model('main', 'StudyPlan')
    StudySeat = apps.get_model('main', 'StudySeat')

    LibraryProfile.objects.get_or_create(
        name='Hiti Library and Study Center',
        defaults={
            'tagline': 'Quiet reading space, library access, and focused study seats',
            'description': 'A study-friendly library center with books, member records, reservations, seat booking, and librarian support.',
            'address': 'Exact location available on Google Maps.',
            'opening_hours': 'Open daily for focused study',
            'google_maps_url': 'https://maps.app.goo.gl/duKAnvRMtzUkqHdC8',
            'map_embed_url': 'https://www.google.com/maps?q=Hiti%20Library%20and%20Study%20Center&output=embed',
            'rating_label': 'Google Maps',
            'review_count_label': 'Public listing',
            'primary_color': '#075f46',
            'accent_color': '#f7c948',
        },
    )

    facilities = [
        ('Quiet Reading Hall', 'Focused study environment with calm seating.', 'QZ', 1),
        ('Study Seats', 'Members can book active study seats from the website.', 'ST', 2),
        ('Book Issue & Return', 'Books can be issued, returned, reserved, and tracked.', 'BR', 3),
        ('Due Date & Fine Tracking', 'Late returns can calculate fine records automatically.', 'FN', 4),
        ('WiFi Ready', 'Facility record for internet support and digital study needs.', 'WF', 5),
        ('Power Backup', 'Useful for uninterrupted study sessions.', 'PB', 6),
        ('CCTV & Safe Space', 'Study center safety and discipline support.', 'SF', 7),
        ('Help Desk', 'Members can contact librarian from the website.', 'HD', 8),
    ]
    for name, description, icon_label, sort_order in facilities:
        Facility.objects.get_or_create(
            name=name,
            defaults={'description': description, 'icon_label': icon_label, 'sort_order': sort_order},
        )

    plans = [
        ('Daily Study Pass', Decimal('0.00'), 'Daily', 'For short focused study sessions.', False, 1),
        ('Monthly Study Seat', Decimal('0.00'), 'Monthly', 'Best for regular students and exam preparation.', True, 2),
        ('Library Membership', Decimal('0.00'), 'Monthly', 'Book access, issue-return, reservations, and study support.', False, 3),
    ]
    for name, price, duration, description, is_featured, sort_order in plans:
        StudyPlan.objects.get_or_create(
            name=name,
            defaults={
                'price': price,
                'duration': duration,
                'description': description,
                'is_featured': is_featured,
                'sort_order': sort_order,
            },
        )

    for index in range(1, 25):
        StudySeat.objects.get_or_create(
            seat_number=f'S{index:02d}',
            defaults={'section': 'Reading Hall'},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_library_features'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=90)),
                ('description', models.TextField(blank=True)),
                ('icon_label', models.CharField(blank=True, max_length=8)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['sort_order', 'name'], 'verbose_name_plural': 'facilities'},
        ),
        migrations.CreateModel(
            name='LibraryProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Hiti Library and Study Center', max_length=160)),
                ('tagline', models.CharField(default='Quiet study space and complete library support', max_length=180)),
                ('description', models.TextField(blank=True)),
                ('address', models.CharField(blank=True, max_length=240)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('whatsapp', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('opening_hours', models.CharField(default='Open daily for focused study', max_length=120)),
                ('weekly_off', models.CharField(blank=True, max_length=80)),
                ('google_maps_url', models.URLField(blank=True)),
                ('map_embed_url', models.URLField(blank=True)),
                ('rating_label', models.CharField(blank=True, max_length=40)),
                ('review_count_label', models.CharField(blank=True, max_length=40)),
                ('hero_image_url', models.URLField(blank=True)),
                ('primary_color', models.CharField(default='#075f46', max_length=20)),
                ('accent_color', models.CharField(default='#f7c948', max_length=20)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'library profile', 'verbose_name_plural': 'library profile'},
        ),
        migrations.CreateModel(
            name='StudyPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=90)),
                ('price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8)),
                ('duration', models.CharField(default='Monthly', max_length=80)),
                ('description', models.TextField(blank=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['sort_order', 'price', 'name']},
        ),
        migrations.CreateModel(
            name='StudySeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_number', models.CharField(max_length=20, unique=True)),
                ('section', models.CharField(default='Reading Hall', max_length=80)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['section', 'seat_number']},
        ),
        migrations.CreateModel(
            name='SeatBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(default=django.utils.timezone.localdate)),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='active', max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='seat_bookings', to='main.studyplan')),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='main.studyseat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seat_bookings', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.RunPython(seed_hiti_profile, migrations.RunPython.noop),
    ]
