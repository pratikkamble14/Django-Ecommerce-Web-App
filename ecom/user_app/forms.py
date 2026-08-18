from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

class UserRegistrationForm(forms.ModelForm):
    name = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ['name','username','email','password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('name', '')
        if commit:
            user.save()
        return user

