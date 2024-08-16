import calendar
import html
import logging
from io import BytesIO
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import get_user_model
from reportlab.lib.pagesizes import letter
from .forms import ServiceRequestForm, ContactForm, ReportForm, ScheduleForm, BrigadeSelectionForm, ScheduleEntryForm
from django.http import JsonResponse
from .models import Service, Tariff, ScheduleEntry, MemberBrigade, ScheduleMember
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .models import ServiceRequest, Brigade
from .forms import ReportForm, ScheduleForm, BrigadeSelectionForm
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import CreateView
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from .models import Report, Schedule
import json
from .models import Receipt
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render
from .forms import ServiceRequestForm
import logging
from django.core.mail import EmailMessage
from django.db.models.functions import ExtractMonth
from itertools import chain
from datetime import datetime, timedelta, timezone
from django.shortcuts import get_object_or_404, render, redirect
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os


def about(request):
    service_requests = ServiceRequest.objects.annotate(month=ExtractMonth('date_start')).values('month').annotate(
        count=Count('id'))

    month_names = [calendar.month_name[i] for i in range(1, 13)]

    data_dict = {month_name: 0 for month_name in month_names}

    for service_request in service_requests:
        month_number = service_request['month']
        month_name = calendar.month_name[month_number]
        data_dict[month_name] = service_request['count']

    data_list = [{'month': month_name, 'count': count} for month_name, count in data_dict.items()]

    data_json = json.dumps(data_list)

    return render(request, 'about.html', {'data_list': data_list})


def statistics(request):
    service_requests = (
        ServiceRequest.objects
        .values('service__name_service')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    data_list = [{'service': service_request['service__name_service'], 'count': service_request['count']} for
                 service_request in service_requests]

    data_json = json.dumps(data_list)

    return render(request, 'statistics.html', {'data_json': data_json})


def login(request):
    return render(request, 'users/login.html')


def about_projects(request):
    return render(request, 'about_projects.html')


def register(request):
    return render(request, 'users/register.html')


def get_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, 'users/profile.html', {'report': report})


def index(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ContactForm()

    services = Service.objects.all()
    data = {
        'services': services,
        'form': form,
    }
    return render(request, 'index.html', context=data)


def profile(request):
    service_requests = ServiceRequest.objects.filter(user=request.user)
    form = ServiceRequestForm()
    return render(request, 'users/profile.html', {'form': form, 'service_requests': service_requests})


def main_page(request, id_service):
    service = get_object_or_404(Service, id_service=id_service)
    duration_tariff = service.tariffs.first()
    duration_tariff_price = duration_tariff.price if duration_tariff else None
    return render(request, 'main_page.html', {'service': service, 'duration_tariff_price': duration_tariff_price})


def book_service(request, id_service):
    service = get_object_or_404(Service, id_service=id_service)
    messages.success(request, 'Услуга успешно забронирована')
    return render(request, 'book_service.html', {'service': service})


def get_service_requests_stats():
    total_requests = ServiceRequest.objects.count()
    total_amount = ServiceRequest.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0

    return {'total_requests': total_requests, 'total_amount': total_amount}


def view_service_request(request, request_id):
    service_request = ServiceRequest.objects.get(pk=request_id)
    context = {'service_request': service_request}
    return render(request, 'service_page.html', context)


logger = logging.getLogger(__name__)


def service_request_handler(request, id_service=None):
    template_name = 'service_page.html' if id_service else 'submit_service_request.html'
    service = None

    if id_service:
        service = get_object_or_404(Service, id_service=id_service)

    form_class = ServiceRequestForm
    initial_data = {'id_service': id_service} if id_service else {}

    stats_context = get_service_requests_stats()

    if request.method == 'POST':
        form = form_class(request.POST, user=request.user, initial=initial_data)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.user = request.user
            service_request.confirmed = True

            total_price = 0

            if id_service:
                duration_tariff = form.cleaned_data['duration']
                has_alarm_system = form.cleaned_data['alarm_system']
                total_price = calculate_price(id_service, duration_tariff, has_alarm_system)
                form.instance.total_price = Decimal(total_price)

                if has_alarm_system:
                    pass

            # Назначить бригаду
            service_request.assign_brigade()

            try:
                service_request.save()
                messages.success(request, 'Заявка на услугу успешно отправлена')
                emails = form.cleaned_data['email']
                if not isinstance(emails, list):
                    emails = [emails]

                receipt = generate_receipt(service_request)
                receipt_id = receipt.id
                print("Receipt ID:", receipt_id)
                try:
                    for email in emails:
                        send_email_with_attachment(receipt_id, email)
                except Exception as e:
                    print(f"Ошибка при отправке письма с квитанцией: {e}")
                    messages.error(request, 'Ошибка при отправке квитанции по электронной почте')

                return redirect('submit_service_request')
            except Exception as e:
                print(f"Ошибка при сохранении заявки на услугу: {e}")
                messages.error(request, 'Ошибка при сохранении заявки на услугу')
        else:
            print("Форма недействительна")
            print(form.errors)
            print(request.POST)
    else:
        form = form_class(user=request.user, initial=initial_data)

    total_requests = ServiceRequest.objects.count()
    total_amount = ServiceRequest.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    context = {'form': form, 'total_requests': total_requests, 'total_amount': total_amount, **stats_context}

    if service:
        context.update({'service': service, 'base_price': service.base_price})

    print(f"Отображение шаблона: {template_name}")
    return render(request, template_name, context)

def create_service_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save()  # Сохраняем данные заявки на услугу

            # Генерируем квитанцию и PDF
            receipt = generate_receipt(service_request)
            pdf_data = generate_pdf_from_receipt(receipt)

            # Отправляем письмо с вложением
            email_subject = 'Заявка на услугу'
            email_body = 'Ваша заявка на услугу успешно создана.'
            try:
                email = EmailMessage(
                    email_subject,
                    email_body,
                    settings.EMAIL_HOST_USER,  # Отправитель
                    [service_request.email],  # Получатель
                )
                email.attach('payment_receipt.pdf', pdf_data, 'application/pdf')
                email.send()

                return HttpResponse('Заявка на услугу успешно отправлена.')
            except Exception as e:
                logger.error("Failed to send email: %s", e)
                return HttpResponse("Failed to send email: " + str(e), status=500)
    else:
        form = ServiceRequestForm()
    return render(request, 'submit_service_request.html', {'form': form})


def generate_receipt(service_request):
    # Создаем объект квитанции
    print("Generating receipt...")
    print("Service request total price:", service_request.total_price)
    receipt = Receipt.objects.create(
        date_receipt=datetime.now(),
        total_amount=service_request.total_price,
        services=service_request.service,
    )
    print("Receipt generated successfully")
    return receipt


def generate_pdf_from_receipt(receipt):
    # Создаем объект canvas для генерации PDF
    pdf_buffer = BytesIO()
    pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Путь к шрифту в папке static/main/fonts
    font_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'main', 'fonts', 'DejaVuSans.ttf')

    # Проверка пути к шрифту и его существования
    if not os.path.exists(font_path):
        print(f"Font file not found at: {font_path}")
        raise FileNotFoundError(f"Font file not found at: {font_path}")

    # Регистрация шрифта, поддерживающего кириллицу
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    # Установка шрифта
    pdf_canvas.setFont('DejaVuSans', 12)

    # Вставляем информацию о квитанции в PDF
    pdf_canvas.drawString(100, 750, f"Дата: {receipt.date_receipt}")
    pdf_canvas.drawString(100, 730, f"Сумма: {receipt.total_amount}")
    pdf_canvas.drawString(100, 710, f"Услуга: {receipt.services}")

    # Завершаем создание PDF
    pdf_canvas.showPage()
    pdf_canvas.save()

    # Возвращаем содержимое PDF
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


# Пример использования
class MockReceipt:
    def __init__(self):
        self.date_receipt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total_amount = 8845.00
        self.services = "Услуга 1"


receipt = MockReceipt()
pdf_data = generate_pdf_from_receipt(receipt)

# Сохранение PDF для проверки
with open("receipt.pdf", "wb") as f:
    f.write(pdf_data)


def send_email_with_attachment(receipt_id, recipient_email):
    try:
        receipt = Receipt.objects.get(pk=receipt_id)
        pdf_data = generate_pdf_from_receipt(receipt)

        email_subject = 'Платежная квитанция'
        email_body = 'В приложении находится платежная квитанция за вашу последнюю транзакцию.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [recipient_email]

        email = EmailMessage(email_subject, email_body, email_from, recipient_list)
        email.attach('payment_receipt.pdf', pdf_data, 'application/pdf')  # Прикрепляем данные PDF
        email.send()  # Отправляем письмо

        print("Письмо успешно отправлено")
        return HttpResponse("Письмо успешно отправлено")
    except Exception as e:
        print("Не удалось отправить письмо:", e)
        return HttpResponse("Не удалось отправить письмо: " + str(e), status=500)


def calculate_price(id_service, duration_tariff, has_alarm_system):
    try:
        service = Service.objects.get(id_service=id_service)
    except Service.DoesNotExist:
        return 0
    base_price = service.base_price
    alarm_system_discount = service.alarm_system_discount

    additional_price = duration_tariff.price if duration_tariff else 0

    if has_alarm_system:
        additional_price -= alarm_system_discount

    total_price = base_price + additional_price

    return total_price


def schedule(request):
    brigades = Brigade.objects.all()

    selected_brigade_id = request.GET.get('brigade')
    selected_month = request.GET.get('selected_month')

    schedule_entries_queryset = Schedule.objects.all()

    if selected_brigade_id is not None:
        schedule_entries_queryset = schedule_entries_queryset.filter(brigade_id=selected_brigade_id)
    if selected_month is not None and selected_month != '':
        schedule_entries_queryset = schedule_entries_queryset.filter(start__month=selected_month)

    schedule_entries = list(schedule_entries_queryset)
    report_form = None
    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST, user=request.user)
        schedule_entry_form = ScheduleEntryForm(request.POST)  # Используйте новую форму ScheduleEntryForm

        if schedule_entry_form.is_valid():
            schedule_instance = schedule_entry_form.save(commit=False)
            user_brigade = Brigade.objects.filter(memberbrigade__user=request.user).first()
            if user_brigade:
                schedule_instance.brigade = user_brigade
                schedule_instance.save()
                return redirect('schedule')

    else:
        schedule_form = ScheduleForm(user=request.user)
        schedule_entry_form = ScheduleEntryForm()  # Используйте новую форму ScheduleEntryForm

        report_form = ReportForm()

    # Генерируем список дней недели на текущей неделе
    today = datetime.now().date()
    weekdays = [today + timedelta(days=i) for i in range(7)]

    brigade_selection_form = BrigadeSelectionForm()
    user_brigades = Brigade.objects.filter(chief=request.user)
    service_requests = ServiceRequest.objects.filter(assigned_team__in=user_brigades)
    unique_dates = Schedule.objects.values_list('start', flat=True).distinct()
    available_dates = [date.strftime('%Y-%m-%d') for date in unique_dates]
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    return render(request, 'schedule.html', {
        'schedule_form': schedule_form,
        'schedule_entry_form': schedule_entry_form,  # Добавьте новую форму в контекст
        'report_form': report_form,
        'user_brigades': user_brigades,
        'service_requests': service_requests,
        'available_dates': available_dates,
        'schedule_entries': schedule_entries,
        'brigade_selection_form': brigade_selection_form,
        'brigades': brigades,
        'weekdays': weekdays,  # Добавляем переменную weekdays в контекст
    })


from .models import Event


def add_event(request):
    title = request.POST.get('title')
    start = request.POST.get('start')
    # Другие необходимые поля

    # Создаем новое событие в базе данных
    event = Event.objects.create(title=title, start=start)
    # Дополнительные действия, если необходимо
    return JsonResponse({'id': event.id, 'title': event.title, 'start': event.start})


def save_event(request):
    event_id = request.POST.get('id')
    title = request.POST.get('title')

    # Находим событие по его ID и обновляем его название
    event = Event.objects.get(id=event_id)
    event.title = title
    event.save()

    # Дополнительные действия, если необходимо
    return JsonResponse({'id': event.id, 'title': event.title, 'start': event.start})


def schedule_view(request):
    # Получаем все уникальные месяцы из полей start и end
    start_months = Schedule.objects.annotate(month=ExtractMonth('start')).values_list('month', flat=True)
    end_months = Schedule.objects.annotate(month=ExtractMonth('end')).values_list('month', flat=True)
    all_months = chain(start_months, end_months)
    unique_months = set(all_months)

    # Создаем список названий месяцев, включая пустой вариант
    month_names = ['Выберите месяц'] + [datetime.strptime(str(month), '%m').strftime('%B') for month in unique_months]

    # Передаем список названий месяцев в контекст шаблона
    context = {'month_names': month_names}

    return render(request, 'schedule.html', context)


def get_filtered_data(request):
    brigade_id = request.GET.get('brigade')

    # Фильтрация данных на основе переданного параметра brigade_id
    if brigade_id:
        schedule_entries = Schedule.objects.filter(brigade_id=brigade_id)
    else:
        schedule_entries = Schedule.objects.all()

    # Преобразование данных в формат JSON
    data = list(schedule_entries.values('assigned_member__username', 'work_days'))

    return JsonResponse(data, safe=False)


def get_top_workers():
    # Получение данных о топ-работниках
    work_days_data = Schedule.objects.values('assigned_member__username').annotate(total_work_days=Count('work_days'))
    top_workers = sorted(work_days_data, key=lambda x: x['total_work_days'], reverse=True)[:5]
    return top_workers


def get_price(request):
    id_service = request.GET.get('id_service')
    duration_id = request.GET.get('duration')
    has_alarm_system = request.GET.get('has_alarm_system') == 'True'

    duration_tariff = Tariff.objects.filter(id=duration_id).first()

    total_price = calculate_price(id_service, duration_tariff, has_alarm_system)

    return JsonResponse({'total_price': str(total_price)})


def service_page(request, id_service):
    service = get_object_or_404(Service, id_service=id_service)
    default_duration_id = 1
    form = ServiceRequestForm(initial={'service': service.id_service, 'duration': default_duration_id})
    return render(request, 'service_page.html', {'service': service, 'form': form})


class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'brigade.html'

@login_required
def brigade_page(request):
    current_date = timezone.now().date()
    user = request.user
    brigades = user.leader_of_brigades.all()
    is_chief = brigades.exists()

    if not is_chief:
        try:
            member_brigade = MemberBrigade.objects.get(user=user)
            brigade = member_brigade.brigade
            service_requests = ServiceRequest.objects.filter(assigned_team=brigade)
        except MemberBrigade.DoesNotExist:
            return HttpResponseForbidden("Вы не состоите в бригаде и не являетесь главным бригадиром.")
    else:
        brigade = brigades.first()
        service_requests = ServiceRequest.objects.filter(assigned_team=brigade)

    members_info = []
    if brigade:
        members = MemberBrigade.objects.filter(brigade=brigade).select_related('user')
        for member in members:
            is_occupied = ServiceRequest.objects.filter(
                assigned_team=brigade,
                members__user=member.user,
                schedule__date=current_date
            ).exists()
            members_info.append({
                'username': member.user.username,
                'brigade': member.brigade,
                'id': member.user.id,
                'is_occupied': is_occupied
            })

    context = {
        'current_date': current_date,
        'service_requests': service_requests,
        'members': members_info,
        'is_chief': is_chief,
    }

    return render(request, 'display_schedule.html', context)



def get_service_requests(request):
    if request.method == 'GET':
        brigade_id = request.GET.get('brigade_id')

        if brigade_id:
            try:
                brigade_id = int(brigade_id)
            except ValueError:
                return JsonResponse({'error': 'Идентификатор бригады должен быть целым числом.'}, status=400)

            # Извлекаем данные из базы данных, включая имя услуги
            service_requests = ServiceRequest.objects.filter(brigade_id=brigade_id).values(
                'id',
                'service__name_service'  # Обращаемся к полю name_service в связанной модели Service
            )

            # Преобразуем данные в формат JSON, декодируя Unicode escape-последовательности
            decoded_service_requests = [
                {'id': req['id'], 'service__name_service': html.unescape(req['service__name_service'])} for req in
                service_requests]

            data = {
                'service_requests': decoded_service_requests
            }
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Необходимо предоставить идентификатор бригады.'}, status=400)

    return JsonResponse({'error': 'Метод запроса не поддерживается.'}, status=405)


def get_members_for_brigade(request, brigade_id):
    members = User.objects.filter(memberbrigade__brigade_id=brigade_id).values('id', 'username')
    return JsonResponse(list(members), safe=False)


def get_schedule(request):
    brigades = Brigade.objects.all()

    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST, user=request.user)
        report_form = ReportForm(request.POST)

        if schedule_form.is_valid():
            schedule_instance = schedule_form.save(commit=False)
            user_brigade = Brigade.objects.filter(memberbrigade__user=request.user).first()
            if user_brigade:
                schedule_instance.brigade = user_brigade
                schedule_instance.save()
                return redirect('schedule')

        elif report_form.is_valid():
            report = report_form.save(commit=False)
            report.user = request.user
            report.save()
            return redirect('schedule')
    else:
        schedule_form = ScheduleForm(user=request.user)
        report_form = ReportForm()

    brigade_selection_form = BrigadeSelectionForm()
    context = {'schedule_form': schedule_form, 'report_form': report_form,
               'brigade_selection_form': brigade_selection_form}
    return render(request, 'schedule.html', context)


def recommend_brigades(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            required_category = service_request.service.category
            matching_brigades = Brigade.objects.filter(categories=required_category).distinct()

            return render(request, 'recommend_brigades.html', {
                'form': form,
                'matching_brigades': matching_brigades,
                'service_request': service_request
            })
    else:
        form = ServiceRequestForm()

    return render(request, 'recommend_brigades.html', {'form': form})


def assign_brigade(request, request_id, brigade_id):
    service_request = get_object_or_404(ServiceRequest, pk=request_id)
    brigade = get_object_or_404(Brigade, pk=brigade_id)
    service_request.assigned_team = brigade
    service_request.save()

    return redirect('service_request_detail', pk=request_id)


def payment(request):
    context = {}  # Можно добавить контекстные данные, если необходимо
    return render(request, 'payment.html', context)


def view_service_request(request, request_id):
    service_request = ServiceRequest.objects.get(pk=request_id)
    context = {'service_request': service_request}
    return render(request, 'service_page.html', context)


from django.utils import timezone


@login_required
def display_schedule(request):
    current_date = timezone.now().date()
    user = request.user

    # Получаем бригады, где пользователь является лидером или участником
    brigades_as_chief = user.leader_of_brigades.all()
    is_chief = brigades_as_chief.exists()

    if is_chief:
        # Если пользователь - лидер бригады, получаем все заявки, назначенные его бригаде
        service_requests = ServiceRequest.objects.filter(assigned_team__in=brigades_as_chief)
        members = MemberBrigade.objects.filter(brigade__in=brigades_as_chief).select_related('user')
    else:
        try:
            member_brigade = MemberBrigade.objects.get(user=user)
            service_requests = ServiceRequest.objects.filter(assigned_team=member_brigade.brigade)
            members = MemberBrigade.objects.filter(brigade=member_brigade.brigade).select_related('user')
        except MemberBrigade.DoesNotExist:
            # Если пользователь не состоит в бригаде, показываем только его собственные заявки
            service_requests = ServiceRequest.objects.filter(user=user)
            members = MemberBrigade.objects.none()

    context = {
        'current_date': current_date,
        'members': members,
        'title': 'Расписание',
        'is_chief': is_chief,
        'service_requests': service_requests
    }
    return render(request, 'display_schedule.html', context)

def get_available_dates(request):
    id_brigade = request.GET.get('brigade')
    if id_brigade:
        brigade = get_object_or_404(Brigade, pk=id_brigade)
        available_dates = list(Schedule.objects.filter(brigade=brigade).values_list('start', flat=True).distinct())
        return JsonResponse({'available_dates': available_dates})
    return JsonResponse({'error': 'Brigade ID is required'}, status=400)


User = get_user_model()

def get_brigade_members(request):
    current_user = request.user
    date = request.GET.get('date')
    request_id = request.GET.get('request_id')
    
    if not date or not request_id:
        return JsonResponse({'error': 'Date and request ID are required'}, status=400)

    try:
        brigade = current_user.leader_of_brigades.get()
    except MemberBrigade.DoesNotExist:
        return JsonResponse({'error': 'User is not a chief of any brigade'}, status=403)

    members = MemberBrigade.objects.filter(brigade=brigade).select_related('user')
    data = []

    for member in members:
        is_member_added = ScheduleMember.objects.filter(user=member.user, date=date, service_request_id=request_id).exists()
        is_occupied = ServiceRequest.objects.filter(members__user=member.user, schedule__date=date).exists()
        data.append({
            'id': member.user.id,
            'username': member.user.username,
            'brigade': {
                'id': brigade.id,
                'name_brigade': brigade.name_brigade
            },
            'is_member_added': is_member_added,
            'is_occupied': is_occupied
        })

    return JsonResponse({'members': data})

@csrf_exempt
@require_POST
def add_member_to_date(request):
    data = json.loads(request.body)
    member_id = data.get('member_id')
    date = data.get('date')
    brigade_id = data.get('brigade_id')
    request_id = data.get('request_id')

    if not member_id or not date or not brigade_id or not request_id:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    ScheduleMember.objects.create(user_id=member_id, date=date, brigade_id=brigade_id, service_request_id=request_id)
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
def remove_member_from_date(request):
    data = json.loads(request.body)
    member_id = data.get('member_id')
    date = data.get('date')
    brigade_id = data.get('brigade_id')
    request_id = data.get('request_id')

    if not member_id or not date or not brigade_id or not request_id:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    ScheduleMember.objects.filter(user_id=member_id, date=date, brigade_id=brigade_id, service_request_id=request_id).delete()

    return JsonResponse({'success': True})

def check_member_added(request):
    member_id = request.GET.get('member_id')
    date = request.GET.get('date')

    is_added = ScheduleMember.objects.filter(user_id=member_id, date=date).exists()
    member_brigade = MemberBrigade.objects.get(...)  # Получаем экземпляр MemberBrigade
    member_brigade.increase_experience()  # Вызываем метод для увеличения опыта
    return JsonResponse({'is_added': is_added})


@login_required
def get_schedule_members(request):
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')
    request_id = request.GET.get('request_id')

    if not start_date_str or not end_date_str or not request_id:
        return JsonResponse({'error': 'Start date, end date, and request ID are required'}, status=400)

    try:
        start_date = timezone.datetime.fromisoformat(start_date_str).date()
        end_date = timezone.datetime.fromisoformat(end_date_str).date()
        request = get_object_or_404(ServiceRequest, pk=request_id)

        brigade = request.assigned_team
        schedule_members = ScheduleMember.objects.filter(
            brigade=brigade,
            date__range=(start_date, end_date),
            service_request=request
        ).select_related('user', 'brigade')

        events = [{
            'title': member.user.username,
            'start': member.date.isoformat(),
            'end': member.date.isoformat(),
            'address': request.get_address()  # Добавляем адрес в событие расписания
        } for member in schedule_members]

        return JsonResponse(events, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_brigade_members(request):
    current_user = request.user
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'Date is required'}, status=400)

    try:
        brigade = current_user.leader_of_brigades.get()
    except MemberBrigade.DoesNotExist:
        return JsonResponse({'error': 'User is not a chief of any brigade'}, status=403)

    members = MemberBrigade.objects.filter(brigade=brigade).select_related('user')
    data = []

    for member in members:
        is_member_added = ScheduleMember.objects.filter(user=member.user, date=date).exists()
        data.append({
            'id': member.user.id,
            'username': member.user.username,
            'brigade': {
                'id': brigade.id_brigade,
                'name_brigade': brigade.name_brigade
            },
            'is_member_added': is_member_added
        })

    print(data)  # Отладочное сообщение
    return JsonResponse({'members': data})


def check_member_status(request):
    member_id = request.GET.get('member_id')
    date = request.GET.get('date')

    if not member_id or not date:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    is_member_added = ScheduleMember.objects.filter(user_id=member_id, date=date).exists()
    return JsonResponse({'is_member_added': is_member_added})
