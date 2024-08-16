from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import send_mail

from security import settings


class ServiceCategory(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название категории')
    description = models.TextField(verbose_name='Описание', blank=True, null=True)

    def __str__(self):
        return self.name


class Brigade(models.Model):
    id_brigade = models.AutoField(primary_key=True)
    name_brigade = models.CharField(max_length=200, verbose_name='Название бригады')
    number = models.IntegerField(verbose_name='Номер', unique=True)  # Добавляем поле для номера бригады
    categories = models.ManyToManyField(ServiceCategory, related_name='brigades', verbose_name='Категории')

    chief = models.ForeignKey(
        get_user_model(), related_name='leader_of_brigades', on_delete=models.SET_NULL, null=True,
        blank=True, verbose_name='Главный бригадир',
    )

    @property
    def member_count(self):
        return self.memberbrigade_set.count()

    def __str__(self):
        return self.name_brigade  # или любое другое поле, которое вы хотите видеть при отображении объекта


class Status(models.Model):
    id_status = models.AutoField(primary_key=True)
    name_status = models.CharField(max_length=200, verbose_name='Имя')

    def __str__(self):
        return self.name_status  # или любое другое поле, которое вы хотите видеть при отображении объекта


class Tariff(models.Model):
    duration = models.IntegerField(verbose_name='Продолжительность (в месяцах)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return f'{self.duration} месяцев - {self.price}'


class Service(models.Model):
    id_service = models.AutoField(primary_key=True)
    name_service = models.CharField(max_length=200, verbose_name='Имя')
    description = models.TextField(verbose_name='Описание')

    tariffs = models.ManyToManyField(Tariff, related_name='services', verbose_name='Тарифы')

    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=1500)
    alarm_system_discount = models.DecimalField(max_digits=10, decimal_places=2, default=20)

    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name='Категория')

    def __str__(self):
        return self.name_service


class Area(models.Model):
    id_area = models.AutoField(primary_key=True)
    name_area = models.CharField(max_length=200, verbose_name='Имя')

    def __str__(self):
        return self.name_area  # или любое другое поле, которое вы хотите видеть при отображении объекта


class Contract(models.Model):
    id_contract = models.AutoField(primary_key=True)
    name_contract = models.TextField(max_length=200, verbose_name='Имя')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    brigade = models.ForeignKey(Brigade, null=True, on_delete=models.CASCADE, verbose_name='Бригада')
    service = models.ForeignKey(Service, null=True, on_delete=models.CASCADE, verbose_name='Услуга')
    area = models.ForeignKey(Area, null=True, on_delete=models.CASCADE, verbose_name='Участок')

    def __str__(self):
        return self.name_contract  # или любое другое поле, которое вы хотите видеть при отображении объекта




class Assignment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateField()


class MemberBrigade(models.Model):
    id_member_brigade = models.AutoField(primary_key=True)
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, verbose_name='Бригада')
    number = models.IntegerField(verbose_name='Номер')
    experience = models.IntegerField(default=1, verbose_name='Опыт')

    def __str__(self):
        return f"{self.brigade.name_brigade} - Member {self.number}"

    @property
    def current_experience(self):
        # Опыт увеличивается на основе количества дней, когда человека добавляли в расписание
        # Получаем все даты, когда участник был добавлен в расписание
        dates_added = ScheduleMember.objects.filter(user=self.user).values_list('date', flat=True)
        # Считаем уникальные даты, чтобы избежать учета одной и той же даты несколько раз
        unique_dates_added = set(dates_added)
        return len(unique_dates_added)

    def increase_experience(self):
        # Повышение опыта на основе количества дней, когда человека добавляли в расписание
        current_experience = self.current_experience

        # Устанавливаем шаг увеличения опыта в зависимости от текущего уровня опыта
        if self.experience < 5:
            # Для уровней от 1 до 5, шаг составляет 15 дней
            step = 15
        else:
            # После 5 уровня опыта шаг уменьшается до 10 дней
            step = 10

        # Вычисляем новый уровень опыта
        new_experience = current_experience // step + 1

        # Обновляем опыт участника, если он достиг нового уровня опыта
        if new_experience > self.experience:
            self.experience = new_experience
            self.save()


@receiver(post_save, sender=get_user_model())
def assign_brigade_number(sender, instance, created, **kwargs):
    """
    Сигнал, который присваивает номер бригады пользователю при его создании.
    """
    if created:
        # Получаем бригады пользователя через related_name
        brigades = instance.leader_of_brigades.all()

        # Проверяем, что у пользователя есть бригады и номер не назначен
        for brigade in brigades:
            if not brigade.memberbrigade_set.filter(user=instance).exists():
                # Находим максимальный номер в бригаде
                max_number = brigade.memberbrigade_set.aggregate(models.Max('number'))['number__max']
                new_number = max_number + 1 if max_number is not None else 1

                # Создаем MemberBrigade с номером для пользователя
                MemberBrigade.objects.create(user=instance, brigade=brigade, number=new_number)


class Receipt(models.Model):
    id = models.AutoField(primary_key=True)
    date_receipt = models.DateTimeField(verbose_name='Дата')
    services = models.ForeignKey(Service, null=True, on_delete=models.CASCADE, verbose_name='Услуга')
    contract = models.ForeignKey(Contract, null=True, on_delete=models.CASCADE, verbose_name='Контракт')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма оплаты')


class Contact(models.Model):
    first_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    message = models.TextField(max_length=1000)

    def __str__(self):
        # Будет отображаться следующее поле в панели администрирования
        return self.email


class ServiceRequest(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    date_start = models.DateField()
    duration = models.CharField(null=True, max_length=25, blank=True)
    comments = models.TextField(blank=True)
    first_name = models.TextField(blank=True)
    last_name = models.TextField(blank=True)
    email = models.TextField(blank=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Общая стоимость')
    status = models.ForeignKey(Status, default=2, blank=True, on_delete=models.CASCADE, verbose_name='Статус')
    assigned_team = models.ForeignKey(Brigade, null=True, blank=True, on_delete=models.CASCADE, verbose_name='Назначенная бригада')
    rejection_reason = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Адрес')

    def __str__(self):
        return f"{self.service} - {self.user}"

    def get_service_price(self):
        return self.service.price

    def save(self, *args, **kwargs):
        # Ensure rejection_reason is not None
        if self.rejection_reason is None:
            self.rejection_reason = ''

        if self.pk:
            original = ServiceRequest.objects.get(pk=self.pk)
            if original.status != self.status:
                self.send_status_change_notification()
                
        super().save(*args, **kwargs)
    def get_address(self):
            return self.address if self.address else self.area.name
    def send_status_change_notification(self):
        subject = 'Изменение статуса вашей заявки'
        message = render_to_string('status_change_notification.txt', {'request': self})
        recipient_list = [self.email]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

    def assign_brigade(self):
        required_category = self.service.category
        matching_brigades = Brigade.objects.filter(categories=required_category).distinct()
        if matching_brigades.exists():
            self.assigned_team = matching_brigades.first()
class Report(models.Model):
    date = models.DateField(verbose_name='Дата')
    number = models.BigAutoField(verbose_name='Число', unique=True, primary_key=True)
    description = models.TextField(verbose_name='Описание')
    service_request = models.ForeignKey(ServiceRequest, null=True, on_delete=models.SET_NULL,
                                        verbose_name='Заявка на услугу')

class ScheduleMember(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Пользователь')
    date = models.DateField(verbose_name='Дата')
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, verbose_name='Бригада')
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.brigade})"

class Schedule(models.Model):
    id_schedule = models.AutoField(primary_key=True)
    start = models.DateField(verbose_name='Начало периода')
    end = models.DateField(verbose_name='Конец периода')
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, verbose_name='Бригада')
    assigned_member = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name='Назначенный работник'
    )
    task_description = models.TextField(verbose_name='Описание задачи')
    work_days = models.IntegerField(verbose_name='Отработанные дни', default=0)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, verbose_name='Заявка на услугу',
                                        null=True, blank=True)

    def __str__(self):
        return f'{self.start} to {self.end} - {self.brigade.name_brigade} - {self.assigned_member.username}'


class ScheduleEntry(models.Model):
    start = models.DateTimeField(verbose_name='Время начала')
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, verbose_name='Бригада')
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, verbose_name='Заявка на услугу')
    assigned_members = models.ManyToManyField(get_user_model(), verbose_name='Назначенные работники')
    task_description = models.TextField(verbose_name='Описание задачи')

    def __str__(self):
        return f"Schedule Entry - {self.start}"


class Event(models.Model):
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()

    # Другие поля, если необходимо

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.title


class NotificationSubscription(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    telegram_chat_id = models.CharField(max_length=255, unique=True)
    subscription_token = models.CharField(max_length=255, unique=True)
