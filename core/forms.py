from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Order
from allauth.account.forms import SignupForm
import re
from django.core.exceptions import ValidationError


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'phone']


class RescheduleForm(forms.ModelForm):
    DELIVERY_TIMESLOTS = [
        ('8 AM - 12 PM', 'Morning (8 AM - 12 PM)'),
        ('12 PM - 4 PM', 'Afternoon (12 PM - 4 PM)'),
        ('4 PM - 8 PM', 'Evening (4 PM - 8 PM)'),
    ]

    delivery_timeslot = forms.ChoiceField(
        choices=DELIVERY_TIMESLOTS,
        required=True,
        label="Preferred Time Slot",  
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Order
        fields = ['delivery_date', 'delivery_timeslot']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'delivery_date': 'Preferred Delivery Date',
        }


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change labels
        self.fields['email'].label = "Email Address"
        self.fields['username'].label = "Username"
        self.fields['password1'].label = "Password"
        self.fields['password2'].label = "Confirm Password"

        # Change placeholders
        self.fields['email'].widget.attrs.update({
            'placeholder': ''
        })
        self.fields['username'].widget.attrs.update({
            'placeholder': ''
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Atleast 6 characters long'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': ''
        })

        # Add styling if needed
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'city', 'postal_code', 'phone']
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Your Address', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'City', 'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal Code', 'class': 'form-control','maxlength': '6'}),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter 10-digit phone number',
                'class': 'form-control',
                'maxlength': '10',
                'pattern': r'\d{10}',
                'title': 'Enter exactly 10 digits'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields required
        self.fields['address'].required = True
        self.fields['city'].required = True
        self.fields['postal_code'].required = True
        # phone is not mandatory
        self.fields['phone'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not re.fullmatch(r'\d{10}', phone):
                raise ValidationError("Phone number must be exactly 10 digits (digits only).")
        return phone

