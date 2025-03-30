
from .models import BankAccount,Transaction
from django import forms
from django.core.validators import MinLengthValidator, RegexValidator
from datetime import datetime, timedelta

class StatementPeriodForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=(datetime.now() - timedelta(days=30)).date()
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=datetime.now().date()
    )
    format = forms.ChoiceField(
        choices=[('html', 'Web View'), ('pdf', 'PDF Download')],
        widget=forms.RadioSelect,
        initial='html'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date must be after start date")
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Maximum statement period is 1 year")
        
        return cleaned_data

# Option 1: Use ModelForm properly (if you want to create/update BankAccount records)
class DepositForm(forms.ModelForm):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    
    class Meta:
        model = BankAccount
        fields = []  # We only need amount, not other model fields

# Option 2: Better approach - use regular Form (recommended for deposit/withdraw)
class DepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount'
        })
    )

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount'
        })
    )

class TransferForm(forms.Form):
    recipient_account = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Recipient account number'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount'
        })
    )

class PinChangeForm(forms.Form):
    old_pin = forms.CharField(
        label="Current PIN",
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current PIN',
            'autocomplete': 'off'
        }),
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'PIN must contain only numbers')
        ]
    )
    new_pin = forms.CharField(
        label="New PIN",
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new PIN',
            'autocomplete': 'off'
        }),
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'PIN must contain only numbers')
        ]
    )
    confirm_pin = forms.CharField(
        label="Confirm New PIN",
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new PIN',
            'autocomplete': 'off'
        }),
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d+$', 'PIN must contain only numbers')
        ]
    )

    def clean(self):
        cleaned_data = super().clean()
        new_pin = cleaned_data.get('new_pin')
        confirm_pin = cleaned_data.get('confirm_pin')
        
        if new_pin and confirm_pin and new_pin != confirm_pin:
            raise forms.ValidationError("New PINs don't match")
        
        return cleaned_data