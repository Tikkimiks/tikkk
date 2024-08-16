from django.contrib.auth.models import AbstractUser, User
from django.core.mail import send_mail, EmailMessage
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя пользователя в Telegram')
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID чата в Telegram')

    def __str__(self):
        return self.username
    def is_chief_brigadier(self):
        return self.leader_of_brigades.exists()