from django import forms
from django.contrib.auth.forms import UserCreationForm
from PIL import Image

from .models import User


class RegisterForm(UserCreationForm):
    """Форма регистрации пользователя.

    Поля:
    - email (обязательно)
    - password1 (пароль)
    - password2 (подтверждение пароля)
    """

    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
        }),
    )

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        """Стилизация полей пароля под Bootstrap."""
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль',
        })
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    def clean_email(self):
        """Проверяем, что email ещё не занят."""
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def save(self, commit=True):
        """Сохраняем пользователя. Username генерируется из email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.username = self.cleaned_data['email'].split('@')[0][:150]

        base_username = user.username
        counter = 1
        while User.objects.filter(username=user.username).exists():
            counter += 1
            user.username = f'{base_username}{counter}'

        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Форма входа по email и паролю."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль',
        }),
    )


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'avatar', 'phone_number', 'country')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
            'avatar': 'Аватар',
            'phone_number': 'Номер телефона',
            'country': 'Страна',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Россия'}),
        }

    def clean_avatar(self):
        """Проверяем формат и размер аватара (JPEG/PNG, до 5 МБ)."""
        avatar = self.cleaned_data.get('avatar')

        # Если поле пустое — пропускаем
        if not avatar:
            return avatar

        # Если это уже существующий файл из БД — пропускаем
        if not hasattr(avatar, 'content_type'):
            return avatar

        # Проверка размера
        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                f'Размер аватара не должен превышать 5 МБ. '
                f'Ваш файл: {avatar.size / (1024 * 1024):.1f} МБ.'
            )

        # Проверка формата через Pillow
        try:
            img = Image.open(avatar)
            img_format = img.format
        except Exception:
            raise forms.ValidationError('Не удалось прочитать изображение.')

        if img_format not in ['JPEG', 'PNG']:
            raise forms.ValidationError(
                f'Недопустимый формат: {img_format}. Разрешены только JPEG и PNG.'
            )

        # Возвращаем указатель в начало
        avatar.seek(0)
        return avatar

    def clean_email(self):
        """Проверяем, что email не занят другим пользователем."""
        email = self.cleaned_data.get('email', '').lower()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Этот email уже занят другим пользователем.')
        return email
