from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ContactForm, MemberAccountForm, SeatAdmissionForm, SeatGenerationForm
from .models import (
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


def _seat_booking_days(plan):
    if not plan:
        return 30

    duration = (plan.duration or '').lower()
    if 'day' in duration or 'daily' in duration:
        return 1
    if 'week' in duration:
        return 7
    if 'quarter' in duration:
        return 90
    if 'year' in duration or 'annual' in duration:
        return 365
    return 30


def _library_profile():
    profile, _ = LibraryProfile.objects.get_or_create(
        name='Hiti Library and Study Center',
        defaults={
            'owner_name': 'Sumit Kumar Patel',
            'phone': '08429395336',
            'whatsapp': '08429395336',
            'support_phone': '08429395336',
            'helpline_phone': '08429395336',
        },
    )
    return profile


def _available_seat_count():
    total_seats = StudySeat.objects.filter(is_active=True).count()
    booked_seats = SeatBooking.objects.filter(status__in=SeatBooking.OCCUPYING_STATUSES).count()
    return max(total_seats - booked_seats, 0)


def _seat_section_stats():
    stats = []
    sections = StudySeat.objects.values_list('section', flat=True).distinct().order_by('section')
    for section in sections:
        seats = StudySeat.objects.filter(section=section, is_active=True)
        active_booking_count = SeatBooking.objects.filter(
            seat__section=section,
            status__in=SeatBooking.OCCUPYING_STATUSES,
        ).count()
        stats.append({
            'section': section,
            'total': seats.count(),
            'booked': active_booking_count,
            'available': max(seats.count() - active_booking_count, 0),
        })
    return stats


def _facility_action(facility):
    name = facility.name.lower()
    if any(word in name for word in ['book', 'issue', 'return']):
        return {'label': 'Browse Books', 'url': reverse('books')}
    if any(word in name for word in ['fine', 'due']):
        return {'label': 'Open My Library', 'url': reverse('my_library')}
    if any(word in name for word in ['help', 'desk']):
        return {'label': 'Contact Help Desk', 'url': reverse('contact')}
    return {'label': 'Book Study Seat', 'url': f"{reverse('study_center')}#seats"}


def _facility_cards(facilities):
    return [
        {'facility': facility, 'action': _facility_action(facility)}
        for facility in facilities
    ]


def _selected_plan(plan_id):
    if plan_id:
        return StudyPlan.objects.filter(pk=plan_id, is_active=True).first()
    return StudyPlan.objects.filter(is_active=True, is_featured=True).first() or StudyPlan.objects.filter(is_active=True).first()


def _create_seat_booking(user, seat, plan, form=None):
    booking = form.save(commit=False) if form else SeatBooking()
    booking.user = user
    booking.seat = seat
    booking.plan = plan
    booking.status = SeatBooking.ACTIVE if user.is_staff else SeatBooking.PENDING
    booking.start_date = timezone.localdate()
    booking.end_date = timezone.localdate() + timedelta(days=_seat_booking_days(plan))

    if not booking.student_name:
        booking.student_name = user.get_full_name() or user.username
    if not booking.student_email:
        booking.student_email = user.email
    if booking.monthly_fee and booking.amount_paid >= booking.monthly_fee:
        booking.payment_status = SeatBooking.PAID
    elif booking.amount_paid:
        booking.payment_status = SeatBooking.PARTIAL
    else:
        booking.payment_status = SeatBooking.UNPAID

    booking.save()
    return booking


@user_passes_test(lambda user: user.is_staff, login_url='login')
def owner_dashboard(request):
    active_bookings = SeatBooking.objects.filter(status=SeatBooking.ACTIVE).select_related('seat', 'plan', 'user')
    pending_bookings = SeatBooking.objects.filter(status=SeatBooking.PENDING)
    due_bookings = [booking for booking in active_bookings if booking.is_month_end_near]
    overdue_loans = [loan for loan in Loan.objects.filter(status=Loan.BORROWED).select_related('book', 'user') if loan.is_overdue]
    context = {
        'total_books': Book.objects.count(),
        'active_books': Book.objects.filter(is_active=True).count(),
        'available_books': Book.objects.filter(is_active=True, available_copies__gt=0).count(),
        'active_admissions': active_bookings.count(),
        'pending_admissions': pending_bookings.count(),
        'seat_alerts_due': len(due_bookings),
        'available_seats': _available_seat_count(),
        'new_contacts': ContactMessage.objects.filter(status=ContactMessage.NEW).count(),
        'overdue_loans': len(overdue_loans),
        'active_notices': LibraryNotice.objects.filter(is_active=True).count(),
        'quick_links': [
            ('Website profile / colors', '/admin/main/libraryprofile/'),
            ('Owner support / QR payment', '/admin/main/libraryprofile/'),
            ('Books and copies', '/admin/main/book/'),
            ('Categories', '/admin/main/category/'),
            ('Authors', '/admin/main/author/'),
            ('Study seats', '/admin/main/studyseat/'),
            ('Auto create seats', reverse('seat_setup')),
            ('Student admissions', '/admin/main/seatbooking/'),
            ('Study plans / prices', '/admin/main/studyplan/'),
            ('Facilities', '/admin/main/facility/'),
            ('Notices', '/admin/main/librarynotice/'),
            ('Contact messages', '/admin/main/contactmessage/'),
            ('Users and staff', '/admin/auth/user/'),
        ],
        'due_bookings': due_bookings[:5],
        'recent_contacts': ContactMessage.objects.order_by('-created_at')[:5],
    }
    return render(request, 'main/owner_dashboard.html', context)


def support(request):
    profile = _library_profile()
    return render(request, 'main/support.html', {'profile': profile})


def home(request):
    profile = _library_profile()
    context = {
        'profile': profile,
        'facility_cards': _facility_cards(Facility.objects.filter(is_active=True)[:8]),
        'plans': StudyPlan.objects.filter(is_active=True)[:3],
        'notices': LibraryNotice.objects.filter(is_active=True)[:3],
        'total_books': Book.objects.filter(is_active=True).count(),
        'available_books': Book.objects.filter(is_active=True, available_copies__gt=0).count(),
        'available_seats': _available_seat_count(),
    }
    return render(request, 'main/home.html', context)


def about(request):
    return render(request, 'main/about.html')


def services(request):
    context = {
        'total_books': Book.objects.filter(is_active=True).count(),
        'available_books': Book.objects.filter(is_active=True, available_copies__gt=0).count(),
        'available_seats': _available_seat_count(),
        'facilities_count': Facility.objects.filter(is_active=True).count(),
        'plans': StudyPlan.objects.filter(is_active=True)[:3],
    }
    return render(request, 'main/services.html', context)


def facilities(request):
    active_facilities = Facility.objects.filter(is_active=True)
    context = {
        'profile': _library_profile(),
        'facility_cards': _facility_cards(active_facilities),
        'available_seats': _available_seat_count(),
        'plans': StudyPlan.objects.filter(is_active=True),
    }
    return render(request, 'main/facilities.html', context)


def facility_detail(request, facility_id):
    facility = get_object_or_404(Facility, pk=facility_id, is_active=True)
    context = {
        'facility': facility,
        'action': _facility_action(facility),
        'related_cards': _facility_cards(
            Facility.objects.filter(is_active=True).exclude(pk=facility.pk)[:3]
        ),
        'profile': _library_profile(),
        'available_seats': _available_seat_count(),
    }
    return render(request, 'main/facility_detail.html', context)


def contact(request):
    form = ContactForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Message received. We will contact you soon.')
        return redirect('contact')

    return render(request, 'main/contact.html', {'form': form, 'profile': _library_profile()})


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        username = identifier

        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            username = user.username if user else identifier

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')

        messages.error(request, 'Login details match nahi ho rahe. Please try again.')

    return render(request, 'main/login.html', {'next': next_url})


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        username = email or name

        if not name or not email or not password:
            messages.error(request, 'Name, email, and password required hain.')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Is email se account already bana hua hai.')
        elif User.objects.filter(username__iexact=email).exists():
            messages.error(request, 'Is email se account already bana hua hai.')
        elif len(password) < 8:
            messages.error(request, 'Password at least 8 characters ka hona chahiye.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
            MemberProfile.objects.create(user=user)
            auth_login(request, user)
            messages.success(request, 'Account ready hai. Welcome to Hiti Library and Study Center.')
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')

    return render(request, 'main/signup.html', {'next': next_url})


def logout(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You are logged out.')
    return redirect('home')


@login_required(login_url='login')
def dashboard(request):
    MemberProfile.objects.get_or_create(user=request.user)
    active_loans = Loan.objects.filter(user=request.user, status=Loan.BORROWED)
    overdue_count = sum(1 for loan in active_loans if loan.is_overdue)
    current_seat = (
        SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES)
        .select_related('seat', 'plan')
        .first()
    )
    active_seat_bookings = SeatBooking.objects.filter(status=SeatBooking.ACTIVE).select_related('seat', 'plan', 'user')
    context = {
        'total_books': Book.objects.filter(is_active=True).count(),
        'available_books': Book.objects.filter(is_active=True, available_copies__gt=0).count(),
        'active_loans': active_loans.count(),
        'overdue_count': overdue_count,
        'reservations_count': Reservation.objects.filter(user=request.user, status=Reservation.ACTIVE).count(),
        'seat_bookings_count': SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES).count(),
        'current_seat': current_seat,
        'seat_alerts_due_count': sum(1 for booking in active_seat_bookings if booking.is_month_end_near) if request.user.is_staff else 0,
        'notices': LibraryNotice.objects.filter(is_active=True)[:3],
        'recent_books': Book.objects.filter(is_active=True)[:4],
    }
    return render(request, 'main/dashboard.html', context)


def book_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    availability = request.GET.get('availability', '').strip()
    books = Book.objects.filter(is_active=True).select_related('author', 'category')

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(isbn__icontains=query)
            | Q(author__name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(publisher__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'borrowed':
        books = books.filter(available_copies=0)

    context = {
        'books': books,
        'categories': Category.objects.all(),
        'query': query,
        'selected_category': category_id,
        'availability': availability,
    }
    return render(request, 'main/books.html', context)


def book_detail(request, book_id):
    book = get_object_or_404(Book.objects.select_related('author', 'category'), pk=book_id, is_active=True)
    active_loan = None
    active_reservation = None
    if request.user.is_authenticated:
        active_loan = Loan.objects.filter(user=request.user, book=book, status=Loan.BORROWED).first()
        active_reservation = Reservation.objects.filter(user=request.user, book=book, status=Reservation.ACTIVE).first()
    context = {
        'book': book,
        'active_loan': active_loan,
        'active_reservation': active_reservation,
    }
    return render(request, 'main/book_detail.html', context)


@login_required(login_url='login')
def borrow_book(request, book_id):
    if request.method != 'POST':
        return redirect('book_detail', book_id=book_id)

    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=book_id, is_active=True)

        if Loan.objects.filter(user=request.user, book=book, status=Loan.BORROWED).exists():
            messages.error(request, 'Ye book already aapke paas issued hai.')
            return redirect('book_detail', book_id=book.id)

        if book.available_copies <= 0:
            Reservation.objects.get_or_create(user=request.user, book=book, status=Reservation.ACTIVE)
            messages.info(request, 'Book abhi available nahi hai. Reservation add kar di gayi.')
            return redirect('book_detail', book_id=book.id)

        book.available_copies -= 1
        book.save(update_fields=['available_copies', 'updated_at'])
        Reservation.objects.filter(user=request.user, book=book, status=Reservation.ACTIVE).update(status=Reservation.FULFILLED)
        Loan.objects.create(
            user=request.user,
            book=book,
            due_at=timezone.now() + timedelta(days=14),
        )

    messages.success(request, 'Book issue ho gayi. Return date 14 din baad hai.')
    return redirect('my_library')


@login_required(login_url='login')
def return_book(request, loan_id):
    if request.method != 'POST':
        return redirect('my_library')

    with transaction.atomic():
        loan = get_object_or_404(
            Loan.objects.select_for_update().select_related('book'),
            pk=loan_id,
            user=request.user,
            status=Loan.BORROWED,
        )
        loan.fine_amount = loan.calculate_fine()
        loan.status = Loan.RETURNED
        loan.returned_at = timezone.now()
        loan.save(update_fields=['fine_amount', 'status', 'returned_at'])

        book = loan.book
        book.available_copies = min(book.available_copies + 1, book.total_copies)
        book.save(update_fields=['available_copies', 'updated_at'])

    if loan.fine_amount:
        messages.warning(request, f'Book return ho gayi. Fine amount: Rs {loan.fine_amount}.')
    else:
        messages.success(request, 'Book return ho gayi. Koi fine nahi hai.')
    return redirect('my_library')


@login_required(login_url='login')
def reserve_book(request, book_id):
    if request.method != 'POST':
        return redirect('book_detail', book_id=book_id)

    book = get_object_or_404(Book, pk=book_id, is_active=True)
    if Loan.objects.filter(user=request.user, book=book, status=Loan.BORROWED).exists():
        messages.info(request, 'Ye book already aapke paas issued hai.')
        return redirect('book_detail', book_id=book.id)
    if book.is_available:
        messages.info(request, 'Book available hai. Aap direct borrow kar sakte hain.')
        return redirect('book_detail', book_id=book.id)

    reservation, created = Reservation.objects.get_or_create(user=request.user, book=book, status=Reservation.ACTIVE)
    if created:
        messages.success(request, 'Reservation add ho gayi.')
    else:
        messages.info(request, 'Ye reservation already active hai.')
    return redirect('book_detail', book_id=book.id)


@login_required(login_url='login')
def cancel_reservation(request, reservation_id):
    if request.method == 'POST':
        Reservation.objects.filter(pk=reservation_id, user=request.user, status=Reservation.ACTIVE).update(status=Reservation.CANCELLED)
        messages.success(request, 'Reservation cancel ho gayi.')
    return redirect('my_library')


@login_required(login_url='login')
def my_library(request):
    MemberProfile.objects.get_or_create(user=request.user)
    context = {
        'active_loans': Loan.objects.filter(user=request.user, status=Loan.BORROWED).select_related('book', 'book__author'),
        'loan_history': Loan.objects.filter(user=request.user).exclude(status=Loan.BORROWED).select_related('book', 'book__author')[:10],
        'reservations': Reservation.objects.filter(user=request.user, status=Reservation.ACTIVE).select_related('book', 'book__author'),
        'seat_bookings': SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES).select_related('seat', 'plan'),
    }
    return render(request, 'main/my_library.html', context)


@login_required(login_url='login')
def profile(request):
    profile_obj, _ = MemberProfile.objects.get_or_create(user=request.user)
    initial = {
        'full_name': request.user.get_full_name() or request.user.first_name or request.user.username,
        'email': request.user.email,
        'phone': profile_obj.phone,
        'address': profile_obj.address,
    }
    form = MemberAccountForm(
        request.POST or None,
        initial=initial,
        user=request.user,
        profile=profile_obj,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile update ho gayi.')
        return redirect('profile')

    return render(request, 'main/profile.html', {'form': form, 'profile': profile_obj})


def study_center(request):
    active_booked_seats = SeatBooking.objects.filter(status__in=SeatBooking.OCCUPYING_STATUSES).values_list('seat_id', flat=True)
    context = {
        'profile': _library_profile(),
        'facility_cards': _facility_cards(Facility.objects.filter(is_active=True)),
        'plans': StudyPlan.objects.filter(is_active=True),
        'seats': StudySeat.objects.filter(is_active=True),
        'section_stats': _seat_section_stats(),
        'active_booked_seats': set(active_booked_seats),
        'user_booking': (
            SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES)
            .select_related('seat', 'plan')
            .first()
            if request.user.is_authenticated
            else None
        ),
    }
    return render(request, 'main/study_center.html', context)


@user_passes_test(lambda user: user.is_staff, login_url='login')
def seat_setup(request):
    form = SeatGenerationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        created, skipped = form.save()
        messages.success(
            request,
            f'{len(created)} new seats create ho gaye. {len(skipped)} existing seats skip hue.',
        )
        return redirect('seat_setup')

    context = {
        'form': form,
        'section_stats': _seat_section_stats(),
        'total_seats': StudySeat.objects.filter(is_active=True).count(),
        'available_seats': _available_seat_count(),
        'active_bookings': SeatBooking.objects.filter(status=SeatBooking.ACTIVE).count(),
    }
    return render(request, 'main/seat_setup.html', context)


@login_required(login_url='login')
def seat_admission(request, seat_id):
    if SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES).exists():
        messages.error(request, 'Aapki ek study seat booking already active hai.')
        return redirect('study_center')

    seat = get_object_or_404(StudySeat, pk=seat_id, is_active=True)
    if SeatBooking.objects.filter(seat=seat, status__in=SeatBooking.OCCUPYING_STATUSES).exists():
        messages.error(request, 'Ye seat abhi available nahi hai. Dusri seat choose karein.')
        return redirect('study_center')

    profile_obj, _ = MemberProfile.objects.get_or_create(user=request.user)
    initial = {}
    plan_id = request.GET.get('plan_id', '').strip()
    if plan_id:
        plan = StudyPlan.objects.filter(pk=plan_id, is_active=True).first()
        if plan:
            initial['plan'] = plan

    form = SeatAdmissionForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        profile=profile_obj,
        initial=initial,
    )

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            seat = get_object_or_404(StudySeat.objects.select_for_update(), pk=seat_id, is_active=True)
            if SeatBooking.objects.filter(seat=seat, status__in=SeatBooking.OCCUPYING_STATUSES).exists():
                messages.error(request, 'Ye seat abhi available nahi hai. Dusri seat choose karein.')
                return redirect('study_center')
            plan = form.cleaned_data.get('plan') or _selected_plan(None)
            _create_seat_booking(request.user, seat, plan, form=form)

        if request.user.is_staff:
            messages.success(request, 'Student admission active ho gaya.')
        else:
            messages.success(request, 'Admission request submit ho gayi. Payment/admin approval ke baad seat active hogi.')
        return redirect('study_center')

    return render(request, 'main/seat_admission.html', {'form': form, 'seat': seat, 'profile': _library_profile()})


@login_required(login_url='login')
def seat_booking_detail(request, booking_id):
    booking = get_object_or_404(
        SeatBooking.objects.select_related('user', 'seat', 'plan'),
        pk=booking_id,
    )
    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, 'Is admission record ko dekhne ki permission nahi hai.')
        return redirect('dashboard')

    return render(request, 'main/seat_booking_detail.html', {'booking': booking})


@login_required(login_url='login')
def book_study_seat(request, seat_id):
    if request.method != 'POST':
        return redirect('study_center')

    if SeatBooking.objects.filter(user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES).exists():
        messages.error(request, 'Aapki ek study seat booking already active hai.')
        return redirect('study_center')

    with transaction.atomic():
        seat = get_object_or_404(StudySeat.objects.select_for_update(), pk=seat_id, is_active=True)
        if SeatBooking.objects.filter(seat=seat, status__in=SeatBooking.OCCUPYING_STATUSES).exists():
            messages.error(request, 'Ye seat abhi available nahi hai. Dusri seat choose karein.')
            return redirect('study_center')

        plan_id = request.POST.get('plan_id', '').strip()
        plan = _selected_plan(plan_id)
        if plan_id and not plan:
            messages.error(request, 'Selected study plan available nahi hai.')
            return redirect('study_center')

        if 'student_name' in request.POST:
            profile_obj, _ = MemberProfile.objects.get_or_create(user=request.user)
            form = SeatAdmissionForm(request.POST, request.FILES, user=request.user, profile=profile_obj)
            if not form.is_valid():
                messages.error(request, 'Admission details check karein aur dobara submit karein.')
                return redirect('seat_admission', seat_id=seat.id)
            plan = form.cleaned_data.get('plan') or plan
            _create_seat_booking(request.user, seat, plan, form=form)
        else:
            _create_seat_booking(request.user, seat, plan)

    messages.success(request, 'Study seat admission request save ho gaya.')
    return redirect('study_center')


@login_required(login_url='login')
def cancel_study_booking(request, booking_id):
    if request.method == 'POST':
        SeatBooking.objects.filter(pk=booking_id, user=request.user, status__in=SeatBooking.OCCUPYING_STATUSES).update(status=SeatBooking.CANCELLED)
        messages.success(request, 'Study seat booking cancel ho gayi.')
    return redirect('study_center')


@user_passes_test(lambda user: user.is_staff, login_url='login')
def seat_admissions(request):
    status = request.GET.get('status', 'active')
    bookings = SeatBooking.objects.select_related('user', 'seat', 'plan')

    if status == 'due':
        bookings = [booking for booking in bookings.filter(status=SeatBooking.ACTIVE) if booking.is_month_end_near]
    elif status == 'expired':
        bookings = [booking for booking in bookings.filter(status=SeatBooking.ACTIVE) if booking.is_expired]
    elif status in {SeatBooking.PENDING, SeatBooking.ACTIVE, SeatBooking.COMPLETED, SeatBooking.CANCELLED, SeatBooking.REJECTED}:
        bookings = bookings.filter(status=status)

    active_bookings = SeatBooking.objects.filter(status=SeatBooking.ACTIVE).select_related('seat', 'plan', 'user')
    context = {
        'bookings': bookings,
        'status': status,
        'active_count': active_bookings.count(),
        'pending_count': SeatBooking.objects.filter(status=SeatBooking.PENDING).count(),
        'due_count': sum(1 for booking in active_bookings if booking.is_month_end_near),
        'expired_count': sum(1 for booking in active_bookings if booking.is_expired),
        'total_seats': StudySeat.objects.filter(is_active=True).count(),
        'available_seats': _available_seat_count(),
    }
    return render(request, 'main/seat_admissions.html', context)


@user_passes_test(lambda user: user.is_staff, login_url='login')
def mark_seat_alert_sent(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(SeatBooking, pk=booking_id)
        booking.mark_reminder_sent()
        messages.success(request, f'{booking.display_student_name} ka monthly alert sent mark ho gaya.')
    return redirect('seat_admissions')


@user_passes_test(lambda user: user.is_staff, login_url='login')
def extend_seat_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(SeatBooking, pk=booking_id)
        try:
            days = int(request.POST.get('days', 30) or 30)
        except ValueError:
            days = 30
        days = max(1, min(days, 365))
        booking.extend_month(days=days)
        booking.status = SeatBooking.ACTIVE
        booking.save(update_fields=['status'])
        messages.success(request, f'{booking.display_student_name} ka admission {days} din extend ho gaya.')
    return redirect('seat_admissions')


@user_passes_test(lambda user: user.is_staff, login_url='login')
def approve_seat_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(SeatBooking, pk=booking_id, status=SeatBooking.PENDING)
        booking.approve(request.user)
        messages.success(request, f'{booking.display_student_name} ka admission approve ho gaya.')
    return redirect('seat_admissions')


@user_passes_test(lambda user: user.is_staff, login_url='login')
def reject_seat_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(SeatBooking, pk=booking_id, status=SeatBooking.PENDING)
        booking.reject()
        messages.success(request, f'{booking.display_student_name} ka admission reject ho gaya.')
    return redirect('seat_admissions')
