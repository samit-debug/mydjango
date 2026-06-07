from django import forms
from django.contrib.auth.models import User

from .models import ContactMessage, MemberProfile, SeatBooking, StudyPlan, StudySeat


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'message')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }


class MemberProfileForm(forms.ModelForm):
    class Meta:
        model = MemberProfile
        fields = ('phone', 'address')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
        }


class MemberAccountForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, *args, user=None, profile=None, **kwargs):
        self.user = user
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        existing_user = User.objects.filter(email__iexact=email)
        if self.user:
            existing_user = existing_user.exclude(pk=self.user.pk)
        if existing_user.exists():
            raise forms.ValidationError('Is email se account already bana hua hai.')
        return email

    def save(self):
        full_name = self.cleaned_data['full_name'].strip()
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone'].strip()
        address = self.cleaned_data['address'].strip()

        self.user.first_name = full_name
        self.user.email = email
        if not User.objects.filter(username__iexact=email).exclude(pk=self.user.pk).exists():
            self.user.username = email
        self.user.save(update_fields=['first_name', 'email', 'username'])

        self.profile.phone = phone
        self.profile.address = address
        self.profile.save(update_fields=['phone', 'address'])
        return self.profile


class SeatAdmissionForm(forms.ModelForm):
    plan = forms.ModelChoiceField(
        queryset=StudyPlan.objects.filter(is_active=True),
        empty_label=None,
        required=False,
    )

    class Meta:
        model = SeatBooking
        fields = (
            'student_name',
            'student_photo',
            'student_phone',
            'student_email',
            'guardian_name',
            'guardian_phone',
            'address',
            'plan',
            'monthly_fee',
            'amount_paid',
            'payment_reference',
            'payment_proof',
            'payment_status',
            'reminder_enabled',
            'reminder_days_before',
            'admission_note',
        )
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'admission_note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = StudyPlan.objects.filter(is_active=True)
        self.fields['student_name'].label = 'Student name'
        self.fields['student_photo'].label = 'Student photo'
        self.fields['student_phone'].label = 'Student phone'
        self.fields['student_email'].label = 'Student email'
        self.fields['guardian_name'].label = 'Guardian name'
        self.fields['guardian_phone'].label = 'Guardian phone'
        self.fields['monthly_fee'].label = 'Monthly fee'
        self.fields['amount_paid'].label = 'Amount paid'
        self.fields['payment_reference'].label = 'Payment reference / UPI transaction ID'
        self.fields['payment_proof'].label = 'Payment screenshot / proof'
        self.fields['payment_status'].label = 'Payment status'
        self.fields['reminder_enabled'].label = 'Monthly alert enabled'
        self.fields['reminder_days_before'].label = 'Alert days before month end'
        self.fields['admission_note'].label = 'Admission note'

        if not self.is_bound and user:
            self.initial.setdefault('student_name', user.get_full_name() or user.username)
            self.initial.setdefault('student_email', user.email)
            if profile:
                self.initial.setdefault('student_phone', profile.phone)
                self.initial.setdefault('address', profile.address)

    def clean_reminder_days_before(self):
        days = self.cleaned_data['reminder_days_before']
        if days > 15:
            raise forms.ValidationError('Alert 15 din se zyada pehle nahi hona chahiye.')
        return days


class SeatGenerationForm(forms.Form):
    section = forms.CharField(max_length=80, initial='Reading Hall')
    prefix = forms.CharField(max_length=8, initial='S')
    start_number = forms.IntegerField(min_value=1, initial=1)
    count = forms.IntegerField(min_value=1, max_value=300, initial=10)

    def clean_prefix(self):
        return self.cleaned_data['prefix'].strip().upper()

    def save(self):
        section = self.cleaned_data['section'].strip()
        prefix = self.cleaned_data['prefix']
        start_number = self.cleaned_data['start_number']
        count = self.cleaned_data['count']
        created = []
        skipped = []

        width = max(2, len(str(start_number + count - 1)))
        for number in range(start_number, start_number + count):
            seat_number = f'{prefix}{str(number).zfill(width)}'
            seat, was_created = StudySeat.objects.get_or_create(
                seat_number=seat_number,
                defaults={'section': section},
            )
            if was_created:
                created.append(seat)
            else:
                skipped.append(seat)

        return created, skipped
