from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.forms import fields
from accounts.models import CustomUser
from core.models import GroupChatThread


class AccountAuthenticationForm(forms.ModelForm):
    # password = forms.CharField(label = 'Password',widget=forms.PasswordInput)
    class Meta:
        model = CustomUser
        fields = ('email','password')
    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email = email, password = password):
                raise forms.ValidationError(f"Invalid login credentials")

class UserRegistrationForm(UserCreationForm):
    # first_name = forms.CharField()
    # last_name = forms.CharField()
    email = forms.EmailField(max_length=255, help_text="Required. Enter a valid email address. ")
    
    class Meta:
        model = CustomUser
        fields = ('first_name','last_name','email','username','password1','password2',)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            user_instance = CustomUser.objects.exclude(pk = self.instance.pk).get(email = email)
        except CustomUser.DoesNotExist:
            return email
        raise forms.ValidationError(f'Email {email} is already taken.')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user_instance = CustomUser.objects.exclude(pk = self.instance.pk).get(username = username)
        except CustomUser.DoesNotExist:
            return username
        raise forms.ValidationError(f'Username {username} is already taken.')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name','last_name','email','username','profile_image','hide_email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            user_instance = CustomUser.objects.exclude(pk = self.instance.pk).get(email = email)
        except CustomUser.DoesNotExist:
            return email
        raise forms.ValidationError(f'Email {email} is already taken.')
    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user_instance = CustomUser.objects.exclude(pk = self.instance.pk).get(username = username)
        except CustomUser.DoesNotExist:
            return username
        raise forms.ValidationError(f'Username {username} is already taken.')

    def save(self,commit=True):
        user_account = super(ProfileUpdateForm, self).save(commit=False)
        user_account.first_name = self.cleaned_data['first_name']
        user_account.last_name = self.cleaned_data['last_name']
        user_account.username = self.cleaned_data['username']
        user_account.email = self.cleaned_data['email']
        user_account.profile_image = self.cleaned_data['profile_image']
        user_account.hide_email = self.cleaned_data['hide_email']
        if commit:
            user_account.save()
        return user_account


class GroupChatCreationForm(forms.ModelForm):
    class Meta:
        model = GroupChatThread
        fields = ('group_name','image','group_description')
    # def clean_group_name(self):
    #     group_name = self.cleaned_data['group_name'].lower()
    #     try:
    #         group_instance = GroupChatThread.objects.exclude(pk = self.instance.pk).get(grouup  = group_name)
    #     except GroupChatThread.DoesNotExist:
    #         return group_name
    #     raise forms.ValidationError(f'Group name {group_name} is already taken.')