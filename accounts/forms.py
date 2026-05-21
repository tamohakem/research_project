from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Programme

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    student_id = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    programme = forms.ModelChoiceField(queryset=Programme.objects.all(), required=False, 
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    current_year = forms.IntegerField(min_value=1, max_value=6, required=False, 
                                      widget=forms.NumberInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'student_id', 
                  'programme', 'current_year', 'role', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))