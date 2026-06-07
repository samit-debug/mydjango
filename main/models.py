from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    NEW = 'new'
    CONTACTED = 'contacted'
    RESOLVED = 'resolved'

    STATUS_CHOICES = [
        (NEW, 'New'),
        (CONTACTED, 'Contacted'),
        (RESOLVED, 'Resolved'),
    ]

    name = models.CharField(max_length=80)
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=NEW)
    staff_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=120, unique=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=180)
    isbn = models.CharField(max_length=20, unique=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='books')
    description = models.TextField(blank=True)
    publisher = models.CharField(max_length=120, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=40, default='English')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    shelf_location = models.CharField(max_length=40, blank=True)
    cover_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.is_active and self.available_copies > 0


class MemberProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member_profile')
    membership_id = models.CharField(max_length=24, unique=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__username']

    def save(self, *args, **kwargs):
        if not self.membership_id and self.user_id:
            self.membership_id = f'LIB{self.user_id:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Loan(models.Model):
    BORROWED = 'borrowed'
    RETURNED = 'returned'
    OVERDUE = 'overdue'

    STATUS_CHOICES = [
        (BORROWED, 'Borrowed'),
        (RETURNED, 'Returned'),
        (OVERDUE, 'Overdue'),
    ]

    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='loans')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    issued_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=BORROWED)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'{self.book} - {self.user}'

    @property
    def is_overdue(self):
        return self.status == self.BORROWED and timezone.now() > self.due_at

    def calculate_fine(self):
        if not self.is_overdue:
            return Decimal('0.00')
        overdue_days = (timezone.now().date() - self.due_at.date()).days
        return Decimal(max(overdue_days, 0) * 5)


class Reservation(models.Model):
    ACTIVE = 'active'
    FULFILLED = 'fulfilled'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (FULFILLED, 'Fulfilled'),
        (CANCELLED, 'Cancelled'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ACTIVE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.book} reserved by {self.user}'


class LibraryNotice(models.Model):
    title = models.CharField(max_length=140)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class LibraryProfile(models.Model):
    name = models.CharField(max_length=160, default='Hiti Library and Study Center')
    tagline = models.CharField(max_length=180, default='Quiet study space and complete library support')
    description = models.TextField(blank=True)
    owner_name = models.CharField(max_length=120, default='Sumit Kumar Patel')
    owner_photo = models.FileField(upload_to='owner_photos/', blank=True)
    address = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    support_phone = models.CharField(max_length=30, default='08429395336', blank=True)
    helpline_phone = models.CharField(max_length=30, default='08429395336', blank=True)
    email = models.EmailField(blank=True)
    upi_id = models.CharField(max_length=80, blank=True)
    payment_qr = models.FileField(upload_to='payment_qr/', blank=True)
    payment_note = models.TextField(blank=True)
    support_note = models.TextField(blank=True)
    opening_hours = models.CharField(max_length=120, default='Open daily for focused study')
    weekly_off = models.CharField(max_length=80, blank=True)
    google_maps_url = models.URLField(blank=True)
    map_embed_url = models.URLField(blank=True)
    rating_label = models.CharField(max_length=40, blank=True)
    review_count_label = models.CharField(max_length=40, blank=True)
    hero_image_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=20, default='#075f46')
    accent_color = models.CharField(max_length=20, default='#f7c948')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'library profile'
        verbose_name_plural = 'library profile'

    def __str__(self):
        return self.name


class Facility(models.Model):
    name = models.CharField(max_length=90)
    description = models.TextField(blank=True)
    icon_label = models.CharField(max_length=8, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'facilities'

    def __str__(self):
        return self.name


class StudyPlan(models.Model):
    name = models.CharField(max_length=90)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    duration = models.CharField(max_length=80, default='Monthly')
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'price', 'name']

    def __str__(self):
        return self.name


class StudySeat(models.Model):
    seat_number = models.CharField(max_length=20, unique=True)
    section = models.CharField(max_length=80, default='Reading Hall')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['section', 'seat_number']

    def __str__(self):
        return f'{self.section} - {self.seat_number}'

    @property
    def is_available(self):
        return self.is_active and not self.bookings.filter(status__in=SeatBooking.OCCUPYING_STATUSES).exists()


class SeatBooking(models.Model):
    PENDING = 'pending'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'
    PAID = 'paid'
    PARTIAL = 'partial'
    UNPAID = 'unpaid'

    STATUS_CHOICES = [
        (PENDING, 'Pending approval'),
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (REJECTED, 'Rejected'),
    ]
    OCCUPYING_STATUSES = [PENDING, ACTIVE]
    PAYMENT_STATUS_CHOICES = [
        (PAID, 'Paid'),
        (PARTIAL, 'Partial'),
        (UNPAID, 'Unpaid'),
    ]

    admission_number = models.CharField(max_length=24, unique=True, blank=True, null=True)
    seat = models.ForeignKey(StudySeat, on_delete=models.PROTECT, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seat_bookings')
    plan = models.ForeignKey(StudyPlan, on_delete=models.PROTECT, related_name='seat_bookings', null=True, blank=True)
    student_name = models.CharField(max_length=120, blank=True)
    student_photo = models.FileField(upload_to='student_photos/', blank=True)
    student_phone = models.CharField(max_length=20, blank=True)
    student_email = models.EmailField(blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    admission_note = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    reminder_enabled = models.BooleanField(default=True)
    reminder_days_before = models.PositiveIntegerField(default=3)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True)
    payment_reference = models.CharField(max_length=120, blank=True)
    payment_proof = models.FileField(upload_to='payment_proofs/', blank=True)
    payment_submitted_at = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=12,
        choices=PAYMENT_STATUS_CHOICES,
        default=UNPAID,
        blank=True,
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=ACTIVE)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='approved_seat_bookings',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.display_student_name} - {self.seat}'

    def save(self, *args, **kwargs):
        if self.plan and not self.monthly_fee:
            self.monthly_fee = self.plan.price
        if self.payment_proof and not self.payment_submitted_at:
            self.payment_submitted_at = timezone.now()
        super().save(*args, **kwargs)
        if not self.admission_number:
            self.admission_number = f'ADM{self.pk:05d}'
            super().save(update_fields=['admission_number'])

    @property
    def display_student_name(self):
        return self.student_name or self.user.get_full_name() or self.user.username

    @property
    def contact_phone(self):
        return self.student_phone or self.guardian_phone

    @property
    def balance_amount(self):
        return max(self.monthly_fee - self.amount_paid, Decimal('0.00'))

    @property
    def days_remaining(self):
        return (self.end_date - timezone.localdate()).days

    @property
    def is_expired(self):
        return self.status == self.ACTIVE and self.days_remaining < 0

    @property
    def is_month_end_near(self):
        return (
            self.status == self.ACTIVE
            and self.reminder_enabled
            and self.days_remaining <= self.reminder_days_before
        )

    @property
    def alert_label(self):
        if self.status == self.PENDING:
            return 'Pending approval'
        if self.status == self.REJECTED:
            return 'Rejected'
        if self.status != self.ACTIVE:
            return self.get_status_display()
        if self.is_expired:
            return 'Expired'
        if self.is_month_end_near:
            return 'Monthly alert due'
        return 'Active'

    def mark_reminder_sent(self):
        self.reminder_sent_at = timezone.now()
        self.save(update_fields=['reminder_sent_at'])

    def extend_month(self, days=30):
        self.end_date = self.end_date + timezone.timedelta(days=days)
        self.reminder_sent_at = None
        self.save(update_fields=['end_date', 'reminder_sent_at'])

    def approve(self, user):
        self.status = self.ACTIVE
        self.approved_by = user
        self.approved_at = timezone.now()
        if self.amount_paid >= self.monthly_fee and self.monthly_fee:
            self.payment_status = self.PAID
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'payment_status'])

    def reject(self):
        self.status = self.REJECTED
        self.save(update_fields=['status'])
