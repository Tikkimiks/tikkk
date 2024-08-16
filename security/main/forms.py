from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_integer
from django.forms import Textarea
from datetime import date
from security import settings
from users.models import User
from .models import Service, Area, ServiceRequest, Contact, Tariff, Report, Schedule, Brigade, MemberBrigade, \
    ScheduleEntry
from django.utils import timezone
from datetime import date
from datetime import timedelta


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = [
            'service', 'area', 'date_start', 'duration', 'comments',
            'first_name', 'last_name', 'email', 'phone_number', 'user', 'total_price', 'address'
        ]

    services = Service.objects.all()
    areas = Area.objects.all()

    service = forms.ModelChoiceField(
        queryset=services,
        label='Выберите услугу',
        widget=forms.Select(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'})
    )

    area = forms.ModelChoiceField(
        queryset=areas,
        label='Выберите участок',
        widget=forms.Select(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'})
    )

    date_start = forms.DateField(
        label='Дата начала',
        widget=forms.DateInput(attrs={'type': 'date',
                                      'class': 'w-2/4 appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'})
    )

    duration = forms.ModelChoiceField(
        queryset=Tariff.objects.all(),  # Используем теперь тарифы
        label='Продолжительность',
        required=False,
        widget=forms.Select(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-white'})
    )

    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
        label='Дополнительные комментарии',
        required=False
    )

    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
    )

    last_name = forms.CharField(
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
    )

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
    )
    address = forms.CharField(
        label='Адрес',
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white',
            'placeholder': 'Введите адрес',
        }),
        required=False
    )
    phone_number = forms.CharField(
        label='Номер телефона',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white',
            'id': 'phone_number_input'}),
    )

    alarm_system = forms.BooleanField(
        label='Установлена сигнализация',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'm-2',
        })
    )

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )

    total_price = forms.DecimalField(
        label='Общая стоимость',
        required=False,
        widget=forms.TextInput(attrs={'readonly': True,
                                      'class': 'bg-gray-800  block w-full m-1 shadow-lg rounded-2xl p-2 text-center text-white'}),
    )

    hidden_price = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False,
    )

    alarm_system_discount = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        service_id = kwargs.pop('service_id', None)
        user = kwargs.pop('user', None)
        super(ServiceRequestForm, self).__init__(*args, **kwargs)
        self.service_id = service_id

        if self.service_id is not None:
            try:
                self.service_instance = Service.objects.get(id_service=self.service_id)
            except Service.DoesNotExist:
                self.service_instance = None
                self.add_error(None, f"Услуга с id {self.service_id} не найдена")

        if user:
            self.fields['user'].initial = user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

        if 'service_id' in self.initial:
            service_id = self.initial['service_id']
            service = Service.objects.get(id_service=service_id)
            self.fields['hidden_price'].initial = service.base_price
            # self.fields['duration_multiplier'].initial = service.duration_price_multiplier
            self.fields['alarm_system_discount'].initial = service.alarm_system_discount

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')
        duration_tariff = cleaned_data.get('duration')
        has_alarm_system = cleaned_data.get('alarm_system')

        # Получаем значения из модели Service
        base_price = service.base_price if service else 0
        alarm_system_discount = service.alarm_system_discount if service else 0

        # Логика расчета цены
        additional_price = 0

        if duration_tariff:
            # Используем цену тарифа вместо умножения на duration_multiplier
            additional_price += duration_tariff.price

        if has_alarm_system:
            additional_price -= alarm_system_discount

        total_price = base_price + additional_price

        # Записываем общую цену в cleaned_data
        cleaned_data['total_price'] = total_price

        return cleaned_data


class ContactForm(forms.Form):
    class Meta:
        model = Contact
        fields = ['first_name', 'email', 'message']

    first_name = forms.CharField(
        max_length=255,
        label='Ваше имя',
        widget=forms.TextInput(
            attrs={
                "class": "w-full bg-gray-800 rounded border border-gray-700 focus:border-purple-500 focus:ring-2 focus:ring-purple-900 text-base outline-none text-gray-100 py-1 px-3 leading-8 transition-colors duration-200 ease-in-out",
                "placeholder": "Введите имя",
            }
        )
    )
    email = forms.EmailField(
        label='Ваша почта',
        widget=forms.EmailInput(
            attrs={
                "class": "w-full bg-gray-800 rounded border border-gray-700 focus:border-purple-500 focus:ring-2 focus:ring-purple-900 text-base outline-none text-gray-100 py-1 px-3 leading-8 transition-colors duration-200 ease-in-out",
                "placeholder": "Введите почту",
            }
        )
    )
    message = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(
            attrs={
                "class": "w-full bg-gray-800 rounded border border-gray-700 focus:border-purple-500 focus:ring-2 focus:ring-purple-900 h-32 text-base outline-none text-gray-100 py-1 px-3 resize-none leading-6 transition-colors duration-200 ease-in-out",
                "placeholder": "Комментарий",
            }
        )
    )

    def save(self):
        first_name = self.cleaned_data['first_name']
        email = self.cleaned_data['email']
        message = self.cleaned_data['message']
        Contact.objects.create(first_name=first_name, email=email, message=message)

        # Отправляем на почту
        send_mail(
            'Новая обратная связь',
            f'Имя: {first_name}\nEmail: {email}\nСообщение: {message}',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )


class ServiceRequestAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ServiceRequestAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            required_category = self.instance.service.category
            matching_brigades = Brigade.objects.filter(categories=required_category).distinct()
            self.fields['assigned_team'].queryset = matching_brigades
            self.fields['assigned_team'].label_from_instance = lambda obj: f"{obj} (Наиболее подходящая)"
        else:
            self.fields['assigned_team'].queryset = Brigade.objects.none()
            self.fields['assigned_team'].help_text = "Нет доступных бригад для этой услуги."
        self.fields['assigned_team'].help_text = "Наиболее подходящие бригады для этой услуги."

    def clean(self):
        cleaned_data = super().clean()
        assigned_team = cleaned_data.get('assigned_team')
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')

        # Проверка: Если назначена бригада, статус должен быть "Принято"
        if assigned_team and status.name_status != 'Принято':
            self.add_error('status', "Вы не поменяли статус на 'Принято'.")

        # Проверка: Если статус "Принято", должна быть выбрана бригада
        if status.name_status == 'Принято' and not assigned_team:
            self.add_error('assigned_team', "Вы не выбрали бригаду.")

        # Проверка: Если статус "Отказано", должна быть указана причина отказа и не должна быть назначена бригада
        if status.name_status == 'Отказано':
            if not rejection_reason:
                self.add_error('rejection_reason', "Вы не указали причину отказа.")
            if assigned_team:
                self.add_error('assigned_team', "При отказе не должна быть назначена бригада.")

        # Проверка: Если указана причина отказа, статус не может быть другим, кроме "Отказано"
        if rejection_reason and status.name_status != 'Отказано':
            self.add_error('rejection_reason', "Причина отказа может быть указана только при статусе 'Отказано'.")

        return cleaned_data


class BrigadeSelectionForm(forms.Form):
    brigade = forms.ModelChoiceField(queryset=Brigade.objects.all(), empty_label=None, widget=forms.Select(attrs={
        'class': 'bg-green-500 text-white px-4 py-2 rounded-full hover:bg-green-600 focus:outline-none focus:shadow-outline-green active:bg-green-800 transition duration-300'}))


class BaseReportForm(forms.Form):
    date = forms.DateField(label='Дата')
    description = forms.CharField(label='Описание', widget=forms.Textarea)
    issues = forms.CharField(label='Выявленные проблемы', widget=forms.Textarea, required=False)


class AccessControlReportForm(BaseReportForm):
    checked_documents_and_persons = forms.IntegerField(label='Количество проверенных документов и лиц')
    incidents_or_violations = forms.CharField(label='Инциденты или нарушения', widget=forms.Textarea)


class SecuritySystemMaintenanceReportForm(BaseReportForm):
    system_condition = forms.CharField(label='Состояние установленных охранных систем', widget=forms.Textarea)
    maintenance_and_repairs = forms.CharField(label='Проведенные обслуживания и ремонты', widget=forms.Textarea)


class EventSecurityReportForm(BaseReportForm):
    security_measures_description = forms.CharField(label='Описание мероприятий по обеспечению безопасности',
                                                    widget=forms.Textarea)
    incidents_or_problems = forms.CharField(label='Инциденты или проблемы', widget=forms.Textarea)


class PropertyProtectionReportForm(BaseReportForm):
    security_measures_description = forms.CharField(
        label='Описание мер по обеспечению безопасности грузов при транспортировке', widget=forms.Textarea)
    incidents_or_problems = forms.CharField(label='Инциденты или проблемы', widget=forms.Textarea)


class SiteSecurityReportForm(BaseReportForm):
    surveillance_results = forms.CharField(label='Результаты круглосуточного наблюдения за объектом',
                                           widget=forms.Textarea)
    incidents_or_attempted_access = forms.CharField(label='Инциденты или попытки несанкционированного доступа',
                                                    widget=forms.Textarea)


class PersonalSecurityReportForm(BaseReportForm):
    security_measures_description = forms.CharField(label='Описание мер по обеспечению личной безопасности',
                                                    widget=forms.Textarea)
    operations_description = forms.CharField(label='Описание проведенных операций по сопровождению VIP-персон',
                                             widget=forms.Textarea)


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['service_request', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-2/4 appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
            'description': forms.Textarea(attrs={
                'class': 'appearance-none block w-full bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
            'service_request': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        # Получаем service_request_id из ключевых аргументов kwargs
        service_request_id = kwargs.pop('service_request_id', None)
        super().__init__(*args, **kwargs)
        if service_request_id:
            # Если service_request_id указан, устанавливаем его в качестве начального значения для поля service_request
            self.fields['service_request'].initial = service_request_id


def validate_not_past_date(value):
    if value < timezone.now().date():
        raise ValidationError('Выбранная дата не может быть прошлой.')


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['start', 'end', 'brigade', 'service_request', 'assigned_member', 'task_description']

    start = forms.DateField(
        label='Начало периода',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full ps-10 p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'min': str(date.today()),
        }),
        initial=date.today,
        validators=[validate_not_past_date]
    )

    end = forms.DateField(
        label='Конец периода',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full ps-10 p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'min': str(date.today()),
        }),
        initial=date.today() + timedelta(days=1),
        validators=[validate_not_past_date]
    )

    task_description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'type': 'date',
            'class': 'w-full appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white'}),
        required=False
    )

    brigade = forms.ModelChoiceField(
        label='Бригада',
        queryset=Brigade.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white',
        }),
        required=False
    )

    assigned_member = forms.ModelChoiceField(
        label='Выбрать работника',
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white brigade-members-dropdown',
        }),
    )

    service_request = forms.ModelChoiceField(
        label='Услуга',
        queryset=ServiceRequest.objects.none(),  # Начальное значение, будет обновлено при инициализации формы
        widget=forms.Select(attrs={
            'class': 'w-full appearance-none block bg-gray-700 m-1 border border-gray-800 shadow-lg rounded-2xl p-2 text-center text-white',
        }),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            user_brigade = Brigade.objects.filter(memberbrigade__user=user).first()
            if user_brigade:
                self.fields['brigade'].queryset = Brigade.objects.filter(memberbrigade__user=user)
                self.fields['assigned_member'].queryset = User.objects.filter(memberbrigade__brigade=user_brigade)
                self.fields['service_request'].queryset = ServiceRequest.objects.filter(assigned_team=user_brigade)

        # Если есть instance (редактирование объекта), заполним brigade
        instance = kwargs.get('instance')
        if instance and instance.brigade:
            self.fields['brigade'].initial = instance.brigade


class DisplayScheduleForm(forms.Form):
    brigade = forms.ModelChoiceField(queryset=Brigade.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brigade'].widget.attrs.update({'class': 'form-control'})


class MemberBrigadeForm(forms.ModelForm):
    class Meta:
        model = MemberBrigade
        fields = ['user', 'brigade', 'number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем текущего пользователя бригады, если он уже выбран в записи (редактирование)
        current_user = self.instance.user if self.instance.pk else None
        # Ограничиваем queryset пользователей только теми, которые еще не добавлены в бригады, но не исключаем текущего пользователя
        existing_users = MemberBrigade.objects.exclude(user=current_user).values_list('user_id', flat=True)
        self.fields['user'].queryset = self.fields['user'].queryset.exclude(id__in=existing_users)

    def clean_user(self):
        user = self.cleaned_data['user']
        # Проверяем, существует ли уже запись о членстве в бригаде для выбранного пользователя,
        # и исключаем текущего пользователя из проверки, если это редактирование
        if self.instance.pk and MemberBrigade.objects.filter(user=user).exclude(
                id_member_brigade=self.instance.id_member_brigade).exists():
            raise forms.ValidationError('Этот пользователь уже состоит в бригаде.')
        return user


class EmailForm(forms.Form):
    subject = forms.CharField(max_length=100, initial="Квитанция об оплате")
    message = forms.CharField(widget=forms.Textarea, initial="Добрый день! Пожалуйста, прикрепляю квитанцию об оплате.")
    attach = forms.FileField(widget=forms.FileInput, label="Квитанция")

    def __init__(self, email=None, *args, **kwargs):
        super(EmailForm, self).__init__(*args, **kwargs)
        if email:
            self.fields['email'] = forms.EmailField(initial=email)
        else:
            self.fields['email'] = forms.EmailField()

    def clean_attach(self):
        attach = self.cleaned_data['attach']
        if attach.size > 5 * 1024 * 1024:  # Проверяем размер вложения (5 МБ максимум)
            raise forms.ValidationError("Файл слишком большой. Максимальный размер 5 МБ.")
        return attach


class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
        fields = ['start', 'brigade', 'service_request', 'assigned_members', 'task_description']

    start = forms.DateTimeField(
        label='Начало периода',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-input rounded-md shadow-sm w-full bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-500',
        }),
    )
    brigade = forms.ModelChoiceField(
        queryset=Brigade.objects.all(),
        label='Бригада',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-md shadow-sm w-full bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-500',
        }),
    )
    service_request = forms.ModelChoiceField(
        queryset=ServiceRequest.objects.all(),
        label='Заявка на услугу',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-md shadow-sm w-full bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-500',
        }),
    )
    assigned_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        label='Назначенные работники',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-multiselect rounded-md shadow-sm w-full h-24 bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-500',
        }),
    )
    task_description = forms.CharField(
        label='Описание задачи',
        widget=forms.Textarea(attrs={
            'class': 'form-textarea rounded-md shadow-sm w-full bg-gray-800 text-white border border-gray-600 focus:outline-none focus:border-blue-500',
            'rows': 2,  # Уменьшаем количество строк до 2
        }),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start')
        if start:
            # Установка времени конца работы на 8 часов позже времени начала
            end = start + timedelta(hours=8)
            cleaned_data['end'] = end
        return cleaned_data
