from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, View

from .forms import RegisterForm, LoginForm, ProfileForm
from .models import User


class RegisterView(CreateView):
    """Регистрация пользователя."""

    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('catalog:home')

    def form_valid(self, form):
        """Сохраняем пользователя, логиним его и отправляем приветственное письмо."""
        response = super().form_valid(form)

        # Логиним нового пользователя
        login(self.request, self.object)

        # Приветственное письмо (в dev-режиме печатается в консоль)
        send_mail(
            subject='Добро пожаловать в АгроХаб!',
            message=(
                f'Здравствуйте!\n\n'
                f'Спасибо за регистрацию в АгроХаб.\n'
                f'Ваш аккаунт: {self.object.email}\n\n'
                f'Теперь вы можете добавлять товары, '
                f'писать статьи в блог и управлять своим профилем.\n\n'
                f'Хорошего дня!\n'
                f'— Команда АгроХаб'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.object.email],
            fail_silently=True,
        )

        messages.success(self.request, f'Добро пожаловать, {self.object.email}!')
        return response


class LoginView(View):
    """Вход по email и паролю."""

    template_name = 'users/login.html'

    def get(self, request):
        """GET — показать форму."""
        if request.user.is_authenticated:
            return redirect('catalog:home')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """POST — проверить данные и залогинить."""
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {user.email}!')
                return redirect('catalog:home')
            else:
                form.add_error(None, 'Неверный email или пароль.')

        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Выход из аккаунта."""

    def get(self, request):
        logout(request)
        messages.success(request, 'Вы вышли из аккаунта.')
        return redirect('catalog:home')

    def post(self, request):
        logout(request)
        messages.success(request, 'Вы вышли из аккаунта.')
        return redirect('catalog:home')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля текущего пользователя."""

    model = User
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        """Возвращаем текущего пользователя."""
        return self.request.user

    def form_valid(self, form):
        """Сообщение об успешном сохранении."""
        messages.success(self.request, 'Профиль обновлён!')
        return super().form_valid(form)
