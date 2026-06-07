from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Author, Book, Category, ContactMessage, Facility, Loan, MemberProfile, Reservation, SeatBooking, StudyPlan, StudySeat


class PublicPageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hiti Library and Study Center')

    def test_public_pages_load(self):
        pages = [
            (reverse('login'), 'Log in to Hiti Library and Study Center'),
            (reverse('signup'), 'Create your account'),
            (reverse('study_center'), 'Study seats and facilities'),
            (reverse('facilities'), 'Study center facilities'),
            (reverse('support'), 'Sumit Kumar Patel'),
            (reverse('about'), 'Built for complete library operations'),
            (reverse('services'), 'Everything needed for library management'),
            (reverse('contact'), 'Ask librarian'),
        ]

        for url, text in pages:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)

    def test_facility_detail_page_has_working_action(self):
        facility = Facility.objects.create(
            name='Demo Study Facility',
            description='Working facility detail page.',
            icon_label='DF',
            is_active=True,
        )

        response = self.client.get(reverse('facility_detail', args=[facility.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo Study Facility')
        self.assertContains(response, 'Book Study Seat')


class ContactMessageDatabaseTests(TestCase):
    def test_contact_form_saves_message(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Please contact me.',
        })

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(ContactMessage.objects.get().email, 'test@example.com')
        self.assertEqual(ContactMessage.objects.get().status, ContactMessage.NEW)


class AuthFlowTests(TestCase):
    def test_signup_creates_user_profile_and_opens_dashboard(self):
        response = self.client.post(reverse('signup'), {
            'name': 'Aman User',
            'email': 'aman@example.com',
            'password': 'strongpass123',
        })

        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(email='aman@example.com')
        self.assertTrue(MemberProfile.objects.filter(user=user).exists())

    def test_login_accepts_email(self):
        User.objects.create_user(
            username='neha@example.com',
            email='neha@example.com',
            password='strongpass123',
        )

        response = self.client.post(reverse('login'), {
            'identifier': 'neha@example.com',
            'password': 'strongpass123',
        })

        self.assertRedirects(response, reverse('dashboard'))


class OwnerAdminFlowTests(TestCase):
    def test_owner_dashboard_requires_staff(self):
        member = User.objects.create_user(
            username='member-owner@example.com',
            email='member-owner@example.com',
            password='strongpass123',
        )
        self.client.login(username='member-owner@example.com', password='strongpass123')

        response = self.client.get(reverse('owner_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_staff_can_open_owner_dashboard(self):
        staff = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='strongpass123',
            is_staff=True,
        )
        self.client.login(username='owner@example.com', password='strongpass123')

        response = self.client.get(reverse('owner_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Website control center')
        self.assertContains(response, 'Books and copies')

    def test_staff_can_auto_create_seats(self):
        staff = User.objects.create_user(
            username='seat-owner@example.com',
            email='seat-owner@example.com',
            password='strongpass123',
            is_staff=True,
        )
        self.client.login(username='seat-owner@example.com', password='strongpass123')

        response = self.client.post(reverse('seat_setup'), {
            'section': 'New Hall',
            'prefix': 'N',
            'start_number': 1,
            'count': 3,
        })

        self.assertRedirects(response, reverse('seat_setup'))
        self.assertTrue(StudySeat.objects.filter(seat_number='N01', section='New Hall').exists())
        self.assertTrue(StudySeat.objects.filter(seat_number='N03', section='New Hall').exists())


class LibraryFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='member@example.com',
            email='member@example.com',
            password='strongpass123',
        )
        MemberProfile.objects.create(user=self.user)
        self.category = Category.objects.create(name='Test Programming')
        self.author = Author.objects.create(name='Test Author')
        self.book = Book.objects.create(
            title='Django Library Guide',
            isbn='9780000000001',
            author=self.author,
            category=self.category,
            total_copies=2,
            available_copies=2,
            shelf_location='PRO-1',
        )
        self.seat = StudySeat.objects.create(seat_number='T01', section='Test Hall')
        self.client.login(username='member@example.com', password='strongpass123')

    def test_book_catalog_loads_for_member(self):
        response = self.client.get(reverse('books'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Library Guide')

    def test_public_catalog_and_detail_are_visible(self):
        self.client.logout()

        response = self.client.get(reverse('books'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Library Guide')

        response = self.client.get(reverse('book_detail', args=[self.book.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log in to Borrow')

    def test_member_can_borrow_and_return_book(self):
        response = self.client.post(reverse('borrow_book', args=[self.book.id]))

        self.assertRedirects(response, reverse('my_library'))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)
        loan = Loan.objects.get(user=self.user, book=self.book, status=Loan.BORROWED)

        response = self.client.post(reverse('return_book', args=[loan.id]))

        self.assertRedirects(response, reverse('my_library'))
        self.book.refresh_from_db()
        loan.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        self.assertEqual(loan.status, Loan.RETURNED)

    def test_unavailable_book_creates_reservation(self):
        self.book.available_copies = 0
        self.book.save(update_fields=['available_copies'])

        response = self.client.post(reverse('borrow_book', args=[self.book.id]))

        self.assertRedirects(response, reverse('book_detail', args=[self.book.id]))
        self.assertTrue(Reservation.objects.filter(user=self.user, book=self.book, status=Reservation.ACTIVE).exists())

    def test_member_can_book_study_seat(self):
        response = self.client.post(reverse('book_study_seat', args=[self.seat.id]))

        self.assertRedirects(response, reverse('study_center'))
        self.assertTrue(SeatBooking.objects.filter(user=self.user, seat=self.seat, status=SeatBooking.PENDING).exists())

    def test_member_can_book_study_seat_with_selected_plan(self):
        weekly_plan = StudyPlan.objects.create(
            name='Weekly Test Seat',
            duration='Weekly',
            price=100,
            is_active=True,
        )

        response = self.client.post(reverse('book_study_seat', args=[self.seat.id]), {'plan_id': weekly_plan.id})

        self.assertRedirects(response, reverse('study_center'))
        booking = SeatBooking.objects.get(user=self.user, seat=self.seat, status=SeatBooking.PENDING)
        self.assertEqual(booking.plan, weekly_plan)
        self.assertEqual(booking.end_date, timezone.localdate() + timedelta(days=7))

    def test_member_can_submit_seat_admission_details(self):
        monthly_plan = StudyPlan.objects.create(
            name='Monthly Test Seat',
            duration='Monthly',
            price=500,
            is_active=True,
        )

        response = self.client.post(reverse('seat_admission', args=[self.seat.id]), {
            'student_name': 'Ravi Student',
            'student_photo': SimpleUploadedFile('student.txt', b'photo-data', content_type='text/plain'),
            'student_phone': '9000000001',
            'student_email': 'ravi@example.com',
            'guardian_name': 'Parent User',
            'guardian_phone': '9000000002',
            'address': 'Near library road',
            'plan': monthly_plan.id,
            'monthly_fee': '500.00',
            'amount_paid': '250.00',
            'payment_status': SeatBooking.PARTIAL,
            'reminder_enabled': 'on',
            'reminder_days_before': 5,
            'admission_note': 'Paid cash',
        })

        self.assertRedirects(response, reverse('study_center'))
        booking = SeatBooking.objects.get(user=self.user, seat=self.seat, status=SeatBooking.PENDING)
        self.assertEqual(booking.student_name, 'Ravi Student')
        self.assertEqual(booking.guardian_phone, '9000000002')
        self.assertEqual(booking.plan, monthly_plan)
        self.assertEqual(booking.amount_paid, 250)
        self.assertEqual(booking.payment_status, SeatBooking.PARTIAL)
        self.assertTrue(booking.student_photo)
        self.assertTrue(booking.admission_number.startswith('ADM'))
        self.assertEqual(booking.status, SeatBooking.PENDING)
        self.assertTrue(booking.reminder_enabled)
        self.assertEqual(booking.reminder_days_before, 5)

        response = self.client.get(reverse('seat_booking_detail', args=[booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ravi Student')
        self.assertContains(response, 'Balance')

    def test_profile_updates_account_and_member_details(self):
        response = self.client.post(reverse('profile'), {
            'full_name': 'Updated Member',
            'email': 'updated@example.com',
            'phone': '9876543210',
            'address': 'Reading Hall Road',
        })

        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.user.member_profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Member')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.member_profile.phone, '9876543210')

    def test_staff_can_manage_seat_alert_and_extension(self):
        staff = User.objects.create_user(
            username='staff@example.com',
            email='staff@example.com',
            password='strongpass123',
            is_staff=True,
        )
        booking = SeatBooking.objects.create(
            user=self.user,
            seat=self.seat,
            student_name='Due Student',
            student_phone='9000000003',
            status=SeatBooking.ACTIVE,
            end_date=timezone.localdate() + timedelta(days=1),
            reminder_days_before=3,
        )
        original_end_date = booking.end_date
        self.client.logout()
        self.client.login(username='staff@example.com', password='strongpass123')

        response = self.client.get(f"{reverse('seat_admissions')}?status=due")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Due Student')

        response = self.client.post(reverse('mark_seat_alert_sent', args=[booking.id]))
        self.assertRedirects(response, reverse('seat_admissions'))
        booking.refresh_from_db()
        self.assertIsNotNone(booking.reminder_sent_at)

        response = self.client.post(reverse('extend_seat_booking', args=[booking.id]), {'days': 30})
        self.assertRedirects(response, reverse('seat_admissions'))
        booking.refresh_from_db()
        self.assertEqual(booking.end_date, original_end_date + timedelta(days=30))

    def test_staff_can_approve_pending_paid_admission(self):
        staff = User.objects.create_user(
            username='approve@example.com',
            email='approve@example.com',
            password='strongpass123',
            is_staff=True,
        )
        booking = SeatBooking.objects.create(
            user=self.user,
            seat=self.seat,
            student_name='Paid Student',
            status=SeatBooking.PENDING,
            monthly_fee=500,
            amount_paid=500,
            payment_reference='UPI123',
            end_date=timezone.localdate() + timedelta(days=30),
        )
        self.client.logout()
        self.client.login(username='approve@example.com', password='strongpass123')

        response = self.client.post(reverse('approve_seat_booking', args=[booking.id]))

        self.assertRedirects(response, reverse('seat_admissions'))
        booking.refresh_from_db()
        self.assertEqual(booking.status, SeatBooking.ACTIVE)
        self.assertEqual(booking.payment_status, SeatBooking.PAID)
        self.assertEqual(booking.approved_by, staff)
