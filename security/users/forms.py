from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm, PasswordResetForm, \
    SetPasswordForm
from django.contrib.auth.models import User


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label="", widget=forms.TextInput(
        attrs={'class': 'form-input w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Логин'}, ))
    password = forms.CharField(label="", widget=forms.PasswordInput(
        attrs={'class': 'form-input text-sm text-gray-600 px-4 py-3 rounded-lg w-full bg-gray-200 focus:bg-gray-100 border border-gray-200 focus:outline-none focus:border-purple-400', 'placeholder': 'Пароль'}))

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']

        # def clean(self):
        #     cleaned_data = super().clean()
        #     username = cleaned_data.get('username')
        #     password = cleaned_data.get('password')
        #
        #     if username and password:
        #         user = self.authenticate(username=username, password=password)
        #
        #         if user is None:
        #             raise forms.ValidationError("Неправильный логин или пароль.")
        #
        #         if not user.is_active:
        #             if hasattr(user, 'reason_for_blocking') and user.reason_for_blocking:
        #                 raise forms.ValidationError(f"Ваш аккаунт заблокирован. Причина: {user.reason_for_blocking}")
        #             else:
        #                 raise forms.ValidationError(
        #                     "Ваш аккаунт заблокирован. Обратитесь к администратору для получения дополнительной информации.")
        #
        #     return cleaned_data

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Логин'}))
    password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Пароль'}))
    password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Повторите пароль'}))

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        labels = {
            'email': '',
            'first_name': "",
            'last_name': "",
        }
        widgets = {
            'email': forms.TextInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Фамилия'}),
        }
    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Такой E-mail уже существует!")
        return email


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(disabled=True, label='', widget=forms.TextInput(attrs={'class': 'bg-gray-900 grid m-1 border border-gray-800 shadow-lg  rounded-2xl p-2 text-center text-white'}))
    email = forms.CharField(disabled=True, label='', widget=forms.TextInput(attrs={'class': 'bg-gray-900 grid m-1 mb-3 border border-gray-800 shadow-lg  rounded-2xl p-2 text-center text-white'}))

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'first_name': '',
            'last_name': '',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'bg-gray-700 grid m-1 border border-gray-800 shadow-lg  rounded-2xl p-2 text-center text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'bg-gray-700 grid m-1 border border-gray-800 shadow-lg  rounded-2xl p-2 text-center text-white'}),
        }

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Старый пароль", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Старый пароль'}))
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Новый пароль'}))
    new_password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Подтвердите пароль'}))


class ResetPasswordForm(PasswordResetForm):
    email = forms.EmailField(label='', widget=forms.TextInput(attrs={'class': 'bg-gray-900 grid m-1 border border-gray-800 shadow-lg  rounded-2xl p-2 text-center text-white'}))


class EmailSetPasswordForm(SetPasswordForm):
   new_password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Старый пароль'}))
   new_password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'w-full text-sm  px-4 py-3 bg-gray-200 focus:bg-gray-100 border  border-gray-200 rounded-lg focus:outline-none focus:border-purple-400', 'placeholder': 'Старый пароль'}),)