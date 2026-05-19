from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Feedback


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=20,
        min_length=3,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Иван',
            'pattern': '[A-ZА-ЯЁ][a-zа-яё]{2,19}',
            'title': 'Имя должно начинаться с заглавной буквы (3-20 символов)',
        })
    )
    last_name = forms.CharField(
        max_length=26,
        min_length=3,
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'placeholder': 'Иванов',
            'pattern': '[A-ZА-ЯЁ][a-zа-яё]{2,25}',
            'title': 'Фамилия должна начинаться с заглавной буквы (3-26 символов)',
        })
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'ivan@example.com'})
    )
    favourite_cat = forms.CharField(
        max_length=50,
        required=False,
        label='Любимый вид кошек',
        widget=forms.TextInput(attrs={'placeholder': 'Бенгальская'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'favourite_cat', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Имя пользователя'
        self.fields['username'].label = 'Логин'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пример: qwerty123'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        for field in self.fields.values():
            field.widget.attrs.setdefault('required', True)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Имя пользователя'
        self.fields['username'].label = 'Логин'
        self.fields['password'].widget.attrs['placeholder'] = 'Пример: qwerty123'
        self.fields['password'].label = 'Пароль'


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Иван Иванов',
                'required': True,
                'minlength': '2',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'example@mail.com',
                'required': True,
            }),
            'subject': forms.TextInput(attrs={
                'placeholder': 'Вопрос о породах кошек',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Напишите ваше сообщение...',
                'required': True,
                'maxlength': '1000',
                'rows': 5,
            }),
        }
