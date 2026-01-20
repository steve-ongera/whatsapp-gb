from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Group, Status

class UserRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=20, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Phone Number')

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description', 'icon')

class StatusCreationForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ('status_type', 'content', 'media_file', 'background_color')