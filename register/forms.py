from django import forms
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta: #Modify default meta data
        model = User
        fields = ["username", "email", "password1", "password2"] #fields we ask the user for upon registration. Pass1 vs 2 is to confirm password