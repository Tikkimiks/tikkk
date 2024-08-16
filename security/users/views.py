import uuid

from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import authenticate, login, logout, get_user_model

from main.models import ServiceRequest, Report, NotificationSubscription, MemberBrigade
from django.contrib import messages
# from main import bot


from . import forms
from .forms import LoginUserForm, RegisterUserForm, ProfileUserForm, UserPasswordChangeForm, ResetPasswordForm, \
    SetPasswordForm, EmailSetPasswordForm
from main.models import *
from django.views.generic import UpdateView
from .forms import ProfileUserForm


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(self.request, user)
                messages.success(self.request, 'Успешный вход')  # добавляем уведомление об успешном входе
                return HttpResponseRedirect(self.get_success_url())
        return super().form_invalid(form)


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': "Регистрация"}
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()  # Сохраняем пользователя
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')  # Аутентифицируем пользователя
        messages.success(self.request, 'Регистрация прошла успешно')  # Добавляем уведомление об успешной регистрации
        return response


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm

    template_name = 'users/profile.html'
    extra_context = {
        'title': "Профиль пользователя",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         'Профиль успешно обновлен')  # добавляем уведомление об успешном обновлении профиля
        return response

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получим все заявки пользователя вместе с ценой, используя аннотации
        service_requests = ServiceRequest.objects.filter(user=self.request.user).annotate(
            base_price=F('service__base_price')
        )

        # Фильтруем отчеты пользователя по заявке на услугу пользователя
        reports = Report.objects.filter(service_request__user=self.request.user)

        # Получим членство пользователя в бригаде
        member_brigade = MemberBrigade.objects.filter(user=self.request.user).first()

        context['service_requests'] = service_requests
        context['reports'] = reports
        context['member_brigade'] = member_brigade

        return context

class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:password_change_done")
    template_name = "users/password_change_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Пароль успешно изменен')  # добавляем уведомление об успешной смене пароля
        return response


class ResetPassword(PasswordResetView):
    form_class = ResetPasswordForm
    success_url = reverse_lazy("users:password_reset_done")
    template_name = "users/password_reset_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         'Ссылка для сброса пароля отправлена на вашу почту')  # добавляем уведомление о запросе сброса пароля
        return response


def get_request(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    # Assume report_data is a dictionary containing the report data
    report_data = {
        'service': service_request.service,
        'total_price': service_request.total_price,
        # Other report data
    }
    return JsonResponse(report_data)


def get_report(request, report_id):
    # Получим отчет по его ID или вернем 404, если отчет не найден
    report = get_object_or_404(Report, id=report_id)

    # Теперь вы можете передать данные отчета в шаблон или просто вернуть JSON-ответ
    response_data = {
        'date': report.date.strftime('%Y-%m-%d'),
        'description': report.description,
        # Другие поля отчета, которые вы хотите включить в ответ
    }

    return JsonResponse(response_data)


class SetPassword(PasswordResetConfirmView):
    form_class = EmailSetPasswordForm
    success_url = reverse_lazy("users:password_reset_complete")
    template_name = "users/password_reset_confirm.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request,
                         'Пароль успешно изменен')  # добавляем уведомление об успешной установке нового пароля
        return response
