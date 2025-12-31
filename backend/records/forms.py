from django import forms
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

