from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Programme
from face_auth.image_capture import image_from_data_url

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
    profile_photo = forms.ImageField(
        required=False,
        label='Face authentication photo',
        help_text='Optional: upload a clear, front-facing photo to set up face authentication during signup.',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    enable_face_auth = forms.BooleanField(
        required=False,
        label='Enable face authentication after signup',
        help_text='You must upload a valid face photo before enabling face authentication.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    captured_face_image = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'student_id', 
                  'programme', 'current_year', 'role', 'profile_photo',
                  'captured_face_image', 'enable_face_auth', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        profile_photo = cleaned_data.get('profile_photo')
        captured_face_image = cleaned_data.get('captured_face_image')
        enable_face_auth = cleaned_data.get('enable_face_auth')
        face_photo = profile_photo or image_from_data_url(captured_face_image, 'signup-face')

        if enable_face_auth and not face_photo:
            self.add_error('profile_photo', 'Upload or snap a face photo before enabling face authentication.')
            return cleaned_data

        self.face_encoding = None
        self.face_photo = None
        if face_photo:
            try:
                from face_auth.face_comparator import face_comparator
            except ModuleNotFoundError as exc:
                self.add_error(
                    'profile_photo',
                    f'Face authentication cannot be set up because a dependency is missing: {exc.name}.'
                )
                return cleaned_data

            encoding, success, message = face_comparator.extract_face_encoding(face_photo)
            face_photo.seek(0)
            if not success:
                self.add_error('profile_photo', f'Could not use this photo for face authentication: {message}')
            else:
                self.face_encoding = encoding
                self.face_photo = face_photo

        return cleaned_data

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
