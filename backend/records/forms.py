from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import DNSRecord
from dns_core.packet import TYPE_CODE

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )

class DNSQueryForm(forms.Form):
    domain = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'example.com',
            'required': True
        }),
        help_text='Enter domain name (e.g., example.com)'
    )
    record_type = forms.ChoiceField(
        choices=[(k, k) for k in sorted(TYPE_CODE.keys()) if k != 'ANY'],
        initial='A',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

class DNSRecordForm(forms.ModelForm):
    # Explicitly define record_type as ChoiceField to ensure choices are set
    record_type = forms.ChoiceField(
        choices=[(k, k) for k in sorted(TYPE_CODE.keys()) if k != 'ANY'],
        initial='A',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = DNSRecord
        fields = ['domain', 'record_type', 'value', 'ttl', 'priority']
        widgets = {
            'domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'example.com.',
                'required': True
            }),
            'value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '192.168.1.1 or mail.example.com.',
                'required': True
            }),
            'ttl': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 60,
                'value': 3600
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'required': False
            }),
        }
        help_texts = {
            'domain': 'Domain name must end with a dot (.)',
            'priority': 'Required for MX records',
        }
        
    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        if domain and not domain.endswith('.'):
            domain += '.'
        return domain

class UserCreateForm(UserCreationForm):
    """Form for admin to create normal users"""
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'required': False
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
        # Remove help text for cleaner form
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

