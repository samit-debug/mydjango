from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_library(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Author = apps.get_model('main', 'Author')
    Book = apps.get_model('main', 'Book')
    LibraryNotice = apps.get_model('main', 'LibraryNotice')

    category_names = ['Fiction', 'Science', 'Programming', 'History', 'Children']
    categories = {
        name: Category.objects.get_or_create(name=name)[0]
        for name in category_names
    }

    authors = {
        'R. K. Narayan': Author.objects.get_or_create(name='R. K. Narayan')[0],
        'A. P. J. Abdul Kalam': Author.objects.get_or_create(name='A. P. J. Abdul Kalam')[0],
        'Eric Matthes': Author.objects.get_or_create(name='Eric Matthes')[0],
        'Yuval Noah Harari': Author.objects.get_or_create(name='Yuval Noah Harari')[0],
        'Ruskin Bond': Author.objects.get_or_create(name='Ruskin Bond')[0],
        'Robert C. Martin': Author.objects.get_or_create(name='Robert C. Martin')[0],
    }

    books = [
        {
            'title': 'Malgudi Days',
            'isbn': '9788185986173',
            'author': authors['R. K. Narayan'],
            'category': categories['Fiction'],
            'description': 'Classic short stories set in the fictional town of Malgudi.',
            'publisher': 'Indian Thought Publications',
            'publication_year': 1943,
            'language': 'English',
            'total_copies': 5,
            'available_copies': 5,
            'shelf_location': 'FIC-A1',
        },
        {
            'title': 'Wings of Fire',
            'isbn': '9788173711466',
            'author': authors['A. P. J. Abdul Kalam'],
            'category': categories['History'],
            'description': 'Autobiography of A. P. J. Abdul Kalam.',
            'publisher': 'Universities Press',
            'publication_year': 1999,
            'language': 'English',
            'total_copies': 4,
            'available_copies': 4,
            'shelf_location': 'BIO-B2',
        },
        {
            'title': 'Python Crash Course',
            'isbn': '9781593279288',
            'author': authors['Eric Matthes'],
            'category': categories['Programming'],
            'description': 'Beginner-friendly guide to Python programming.',
            'publisher': 'No Starch Press',
            'publication_year': 2019,
            'language': 'English',
            'total_copies': 3,
            'available_copies': 3,
            'shelf_location': 'PRO-C3',
        },
        {
            'title': 'Sapiens',
            'isbn': '9780099590088',
            'author': authors['Yuval Noah Harari'],
            'category': categories['Science'],
            'description': 'A brief history of humankind.',
            'publisher': 'Vintage',
            'publication_year': 2015,
            'language': 'English',
            'total_copies': 2,
            'available_copies': 2,
            'shelf_location': 'SCI-D4',
        },
        {
            'title': 'The Blue Umbrella',
            'isbn': '9788129119329',
            'author': authors['Ruskin Bond'],
            'category': categories['Children'],
            'description': 'A gentle story loved by young readers.',
            'publisher': 'Rupa Publications',
            'publication_year': 1980,
            'language': 'English',
            'total_copies': 6,
            'available_copies': 6,
            'shelf_location': 'KID-E5',
        },
        {
            'title': 'Clean Code',
            'isbn': '9780132350884',
            'author': authors['Robert C. Martin'],
            'category': categories['Programming'],
            'description': 'A practical guide to writing maintainable software.',
            'publisher': 'Prentice Hall',
            'publication_year': 2008,
            'language': 'English',
            'total_copies': 2,
            'available_copies': 2,
            'shelf_location': 'PRO-C4',
        },
    ]

    for data in books:
        Book.objects.get_or_create(isbn=data['isbn'], defaults=data)

    LibraryNotice.objects.get_or_create(
        title='Library hours',
        defaults={'body': 'Library Monday to Saturday, 9 AM to 6 PM open rahegi.'},
    )
    LibraryNotice.objects.get_or_create(
        title='Return reminder',
        defaults={'body': 'Books due date se pehle return karein to fine avoid hoga.'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('bio', models.TextField(blank=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'categories'},
        ),
        migrations.CreateModel(
            name='LibraryNotice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=140)),
                ('body', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('isbn', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField(blank=True)),
                ('publisher', models.CharField(blank=True, max_length=120)),
                ('publication_year', models.PositiveIntegerField(blank=True, null=True)),
                ('language', models.CharField(default='English', max_length=40)),
                ('total_copies', models.PositiveIntegerField(default=1)),
                ('available_copies', models.PositiveIntegerField(default=1)),
                ('shelf_location', models.CharField(blank=True, max_length=40)),
                ('cover_url', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='books', to='main.author')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='books', to='main.category')),
            ],
            options={'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='MemberProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership_id', models.CharField(blank=True, max_length=24, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='member_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['user__first_name', 'user__username']},
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issued_at', models.DateTimeField(auto_now_add=True)),
                ('due_at', models.DateTimeField()),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('borrowed', 'Borrowed'), ('returned', 'Returned'), ('overdue', 'Overdue')], default='borrowed', max_length=12)),
                ('fine_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loans', to='main.book')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-issued_at']},
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('fulfilled', 'Fulfilled'), ('cancelled', 'Cancelled')], default='active', max_length=12)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='main.book')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.RunPython(seed_library, migrations.RunPython.noop),
    ]
