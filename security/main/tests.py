from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse  # Добавленный импорт
from django.urls import reverse
from users.models import User  # Подставьте правильный путь к вашей модели пользователя
from .models import Service, ServiceRequest, Area, Tariff  # Подставьте правильный путь к вашей модели Service
from .forms import ServiceRequestForm  # Подставьте правильный путь к вашей форме ServiceRequestForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase
from .forms import EmailForm

class RegisterUserTestCase(TestCase):

    def test_register_user(self):
        # Подготовка данных для отправки формы
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }

        # Отправка POST-запроса на страницу регистрации с данными пользователя
        response = self.client.post(reverse('users:register'), data)

        # Проверка статус-кода ответа
        self.assertEqual(response.status_code, 302)  # Ожидаем перенаправление после успешной регистрации

        # Проверка, что пользователь был создан в базе данных
        self.assertTrue(get_user_model().objects.filter(username='testuser').exists())

        # Проверка, что пользователь авторизован после регистрации
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Проверка сообщения об успешной регистрации
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Регистрация прошла успешно')

    def setUp(self):
        # Очистка базы данных перед каждым тестом
        get_user_model().objects.all().delete()

        # Создание пользователя с заранее существующим email
        get_user_model().objects.create_user(username='existinguser', email='existing@example.com',
                                             password='existingpassword')

    def test_register_user_existing_email(self):
        # Получаем начальное количество пользователей в базе данных
        initial_user_count = get_user_model().objects.count()

        # Подготовка данных для отправки формы
        data = {
            'username': 'testuser',
            'email': 'existing@example.com',  # Используем заранее существующий email
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpassword',
            'password2': 'testpassword',
        }

        # Отправка POST-запроса на страницу регистрации с данными пользователя
        response = self.client.post(reverse('users:register'), data)

        # Проверка, что количество пользователей не изменилось
        self.assertEqual(get_user_model().objects.count(), initial_user_count)

        # Проверка статус-кода ответа
        self.assertEqual(response.status_code, 200)  # Ожидаем 200, так как регистрация не удалась

        # Проверка, что сообщение об ошибке выводится пользователю
        if isinstance(response, TemplateResponse):
            form_errors = response.context_data.get('form').errors
            self.assertTrue('email' in form_errors)
            self.assertEqual(form_errors['email'], ['Такой E-mail уже существует!'])



class ServiceRequestFormTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создание необходимых данных для тестов
        cls.user = User.objects.create(username='testuser', first_name='John', last_name='Doe',
                                       email='test@example.com')
        cls.service = Service.objects.create(name_service='Test Service', base_price=100)
        cls.area = Area.objects.create(name_area='Test Area')
        cls.tariff = Tariff.objects.create(duration='3', price=50)        # Добавьте другие необходимые объекты, такие как Area, Tariff, Status, Brigade

    def test_service_request_form_valid(self):
        form_data = {
            'service': self.service.pk,
            'area': self.area.pk,
            'date_start': '2024-05-07',
            'duration': self.tariff.pk,
            'comments': 'Test comments',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@example.com',
            'phone_number': '123456789',
            'user': self.user.pk,
            'total_price': 150,  # Примерное значение для общей стоимости
        }
        form = ServiceRequestForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_service_request_form_invalid(self):
        form_data = {
            'service': self.service.pk,
            'area': self.area.pk,
            'date_start': '2024-05-07',
            'duration': self.tariff.pk,
            'comments': 'Test comments',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid_email',  # Неверный формат email
            'phone_number': '123456789',
            'user': self.user.pk,
            'total_price': 150,  # Примерное значение для общей стоимости
        }
        form = ServiceRequestForm(data=form_data)
        self.assertFalse(form.is_valid())





class EmailFormTestCase(TestCase):

    def test_email_form_valid(self):
        # Создаем валидные данные для формы
        form_data = {
            'subject': 'Тестовая квитанция',
            'message': 'Тестовое сообщение',
            'attach': SimpleUploadedFile('test_file.pdf', b'PDF content'),
            'email': 'test@example.com',
        }
        form = EmailForm(data=form_data, files={'attach': form_data['attach']})
        self.assertTrue(form.is_valid())

    def test_email_form_invalid(self):
        # Создаем невалидные данные для формы (слишком большой файл вложения)
        invalid_form_data = {
            'subject': 'Тестовая квитанция',
            'message': 'Тестовое сообщение',
            'attach': SimpleUploadedFile('test_file.pdf', b'PDF content' * 1024 * 1024 * 6),  # 6 MB file
            'email': 'test@example.com',
        }
        form = EmailForm(data=invalid_form_data, files={'attach': invalid_form_data['attach']})
        self.assertFalse(form.is_valid())
        self.assertIn('attach', form.errors)