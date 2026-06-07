from django.contrib import admin
from django.utils import timezone

from .models import (
    Author,
    Book,
    Category,
    ContactMessage,
    Facility,
    LibraryNotice,
    LibraryProfile,
    Loan,
    MemberProfile,
    Reservation,
    SeatBooking,
    StudyPlan,
    StudySeat,
)

admin.site.site_header = 'Hiti Library Owner Admin'
admin.site.site_title = 'Hiti Library Admin'
admin.site.index_title = 'Website and Library Data Management'


class ActiveStatusAdminMixin:
    actions = ('mark_active', 'mark_inactive')

    @admin.action(description='Mark selected records active')
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Mark selected records inactive')
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'created_at', 'resolved_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('status', 'created_at', 'resolved_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    actions = ('mark_new', 'mark_contacted', 'mark_resolved')
    fieldsets = (
        ('Message', {'fields': ('name', 'email', 'message', 'status')}),
        ('Owner follow-up', {'fields': ('staff_note', 'resolved_at')}),
        ('Audit', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.action(description='Mark selected messages new')
    def mark_new(self, request, queryset):
        queryset.update(status=ContactMessage.NEW, resolved_at=None)

    @admin.action(description='Mark selected messages contacted')
    def mark_contacted(self, request, queryset):
        queryset.update(status=ContactMessage.CONTACTED)

    @admin.action(description='Mark selected messages resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status=ContactMessage.RESOLVED, resolved_at=timezone.now())


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'bio')


@admin.register(Book)
class BookAdmin(ActiveStatusAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'isbn', 'copy_status', 'shelf_location', 'is_active')
    list_filter = ('category', 'author', 'language', 'is_active')
    search_fields = ('title', 'isbn', 'author__name', 'category__name', 'publisher')
    list_editable = ('is_active',)
    autocomplete_fields = ('author', 'category')
    list_per_page = 25
    fieldsets = (
        ('Book details', {'fields': ('title', 'isbn', 'author', 'category', 'description')}),
        ('Publishing', {'fields': ('publisher', 'publication_year', 'language', 'cover_url')}),
        ('Inventory', {'fields': ('total_copies', 'available_copies', 'shelf_location', 'is_active')}),
    )

    @admin.display(description='Copies')
    def copy_status(self, obj):
        return f'{obj.available_copies}/{obj.total_copies}'


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('membership_id', 'user', 'phone', 'joined_at')
    search_fields = ('membership_id', 'user__username', 'user__email', 'user__first_name', 'phone')
    readonly_fields = ('membership_id', 'joined_at')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'issued_at', 'due_at', 'returned_at', 'status', 'fine_amount')
    list_filter = ('status', 'issued_at', 'due_at')
    search_fields = ('book__title', 'book__isbn', 'user__username', 'user__email')
    autocomplete_fields = ('book', 'user')
    readonly_fields = ('issued_at',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('book__title', 'book__isbn', 'user__username', 'user__email')
    autocomplete_fields = ('book', 'user')


@admin.register(LibraryNotice)
class LibraryNoticeAdmin(ActiveStatusAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'body')
    list_editable = ('is_active',)


@admin.register(LibraryProfile)
class LibraryProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'opening_hours', 'updated_at')
    fieldsets = (
        ('Basic details', {'fields': ('name', 'tagline', 'description', 'address', 'phone', 'whatsapp', 'email')}),
        ('Owner and support', {'fields': ('owner_name', 'owner_photo', 'support_phone', 'helpline_phone', 'support_note')}),
        ('Payments', {'fields': ('upi_id', 'payment_qr', 'payment_note')}),
        ('Timing and maps', {'fields': ('opening_hours', 'weekly_off', 'google_maps_url', 'map_embed_url')}),
        ('Branding', {'fields': ('rating_label', 'review_count_label', 'hero_image_url', 'primary_color', 'accent_color')}),
    )

    def has_add_permission(self, request):
        if LibraryProfile.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Facility)
class FacilityAdmin(ActiveStatusAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'icon_label', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(StudyPlan)
class StudyPlanAdmin(ActiveStatusAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'is_featured', 'sort_order', 'is_active')
    list_editable = ('price', 'is_featured', 'sort_order', 'is_active')
    list_filter = ('is_active', 'is_featured', 'duration')
    search_fields = ('name', 'description')


@admin.register(StudySeat)
class StudySeatAdmin(ActiveStatusAdminMixin, admin.ModelAdmin):
    list_display = ('seat_number', 'section', 'current_student', 'availability', 'is_active')
    list_filter = ('section', 'is_active')
    search_fields = ('seat_number', 'section')
    list_editable = ('is_active',)

    @admin.display(description='Current student')
    def current_student(self, obj):
        booking = obj.bookings.filter(status__in=SeatBooking.OCCUPYING_STATUSES).select_related('user').first()
        return booking.display_student_name if booking else '-'

    @admin.display(description='Availability')
    def availability(self, obj):
        return 'Available' if obj.is_available else 'Booked'


@admin.register(SeatBooking)
class SeatBookingAdmin(admin.ModelAdmin):
    list_display = (
        'admission_number',
        'student',
        'seat',
        'plan',
        'payment_status',
        'balance',
        'student_phone',
        'guardian_phone',
        'start_date',
        'end_date',
        'days_left',
        'alert',
        'status',
    )
    date_hierarchy = 'end_date'
    list_per_page = 25
    list_filter = ('status', 'payment_status', 'reminder_enabled', 'start_date', 'end_date', 'plan', 'seat__section')
    search_fields = (
        'admission_number',
        'student_name',
        'student_phone',
        'student_email',
        'guardian_name',
        'guardian_phone',
        'seat__seat_number',
        'user__username',
        'user__email',
        'plan__name',
    )
    readonly_fields = ('admission_number', 'created_at', 'reminder_sent_at', 'payment_submitted_at', 'approved_at')
    actions = ('approve_selected', 'reject_selected', 'mark_monthly_alert_sent', 'extend_month_30_days', 'mark_completed')
    fieldsets = (
        ('Student details', {
            'fields': (
                'user',
                'admission_number',
                'student_name',
                'student_photo',
                'student_phone',
                'student_email',
                'guardian_name',
                'guardian_phone',
                'address',
                'admission_note',
            )
        }),
        ('Seat and plan', {'fields': ('seat', 'plan', 'start_date', 'end_date', 'status')}),
        ('Payment', {'fields': ('monthly_fee', 'amount_paid', 'payment_status', 'payment_reference', 'payment_proof', 'payment_submitted_at')}),
        ('Approval', {'fields': ('approved_by', 'approved_at')}),
        ('Monthly alert', {'fields': ('reminder_enabled', 'reminder_days_before', 'reminder_sent_at')}),
        ('Audit', {'fields': ('created_at',)}),
    )

    @admin.display(description='Student')
    def student(self, obj):
        return obj.display_student_name

    @admin.display(description='Days left')
    def days_left(self, obj):
        return obj.days_remaining

    @admin.display(description='Alert')
    def alert(self, obj):
        return obj.alert_label

    @admin.display(description='Balance')
    def balance(self, obj):
        return obj.balance_amount

    @admin.action(description='Mark monthly alert sent')
    def mark_monthly_alert_sent(self, request, queryset):
        queryset.update(reminder_sent_at=timezone.now())

    @admin.action(description='Approve selected pending admissions')
    def approve_selected(self, request, queryset):
        for booking in queryset.filter(status=SeatBooking.PENDING):
            booking.approve(request.user)

    @admin.action(description='Reject selected pending admissions')
    def reject_selected(self, request, queryset):
        queryset.filter(status=SeatBooking.PENDING).update(status=SeatBooking.REJECTED)

    @admin.action(description='Extend selected admissions by 30 days')
    def extend_month_30_days(self, request, queryset):
        for booking in queryset:
            booking.extend_month(days=30)

    @admin.action(description='Mark selected admissions completed')
    def mark_completed(self, request, queryset):
        queryset.update(status=SeatBooking.COMPLETED)
