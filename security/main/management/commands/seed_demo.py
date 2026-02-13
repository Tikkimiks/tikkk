from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import (
    Area,
    Brigade,
    MemberBrigade,
    Schedule,
    ScheduleMember,
    Service,
    ServiceCategory,
    ServiceRequest,
    Status,
    Tariff,
)


class Command(BaseCommand):
    help = "Seed demo data for the portfolio build. Safe to run multiple times."

    def handle(self, *args, **options):
        User = get_user_model()

        users = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "password": "Admin123!",
            },
            {
                "username": "chief",
                "email": "chief@example.com",
                "is_staff": True,
                "is_superuser": False,
                "password": "Chief123!",
            },
            {
                "username": "worker1",
                "email": "worker1@example.com",
                "is_staff": False,
                "is_superuser": False,
                "password": "Worker123!",
            },
            {
                "username": "worker2",
                "email": "worker2@example.com",
                "is_staff": False,
                "is_superuser": False,
                "password": "Worker123!",
            },
            {
                "username": "client",
                "email": "client@example.com",
                "is_staff": False,
                "is_superuser": False,
                "password": "Client123!",
            },
        ]

        created_users = {}
        for entry in users:
            username = entry["username"]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": entry["email"],
                    "is_staff": entry["is_staff"],
                    "is_superuser": entry["is_superuser"],
                },
            )
            if created:
                user.set_password(entry["password"])
                user.save()
            created_users[username] = user

        Status.objects.update_or_create(id_status=1, defaults={"name_status": "New"})
        Status.objects.update_or_create(id_status=2, defaults={"name_status": "In progress"})
        Status.objects.update_or_create(id_status=3, defaults={"name_status": "Completed"})
        status_new = Status.objects.get(id_status=1)
        status_work = Status.objects.get(id_status=2)

        cat_security, _ = ServiceCategory.objects.get_or_create(
            name="Security",
            defaults={"description": "Security services for facilities and territories."},
        )
        cat_monitoring, _ = ServiceCategory.objects.get_or_create(
            name="Monitoring",
            defaults={"description": "Alarm monitoring and response services."},
        )

        tariff_1m, _ = Tariff.objects.get_or_create(
            duration=1,
            defaults={"price": Decimal("1500.00")},
        )
        tariff_6m, _ = Tariff.objects.get_or_create(
            duration=6,
            defaults={"price": Decimal("8000.00")},
        )
        tariff_12m, _ = Tariff.objects.get_or_create(
            duration=12,
            defaults={"price": Decimal("15000.00")},
        )

        service_guard, _ = Service.objects.get_or_create(
            name_service="Object security",
            defaults={
                "description": "Comprehensive security for commercial sites.",
                "base_price": Decimal("3500.00"),
                "alarm_system_discount": Decimal("300.00"),
                "category": cat_security,
            },
        )
        service_guard.category = cat_security
        service_guard.save()
        service_guard.tariffs.set([tariff_1m, tariff_6m, tariff_12m])

        service_monitoring, _ = Service.objects.get_or_create(
            name_service="Alarm monitoring",
            defaults={
                "description": "24/7 monitoring and response.",
                "base_price": Decimal("2200.00"),
                "alarm_system_discount": Decimal("150.00"),
                "category": cat_monitoring,
            },
        )
        service_monitoring.category = cat_monitoring
        service_monitoring.save()
        service_monitoring.tariffs.set([tariff_1m, tariff_6m])

        area_center, _ = Area.objects.get_or_create(name_area="Central district")
        area_industrial, _ = Area.objects.get_or_create(name_area="Industrial zone")

        chief = created_users["chief"]
        worker1 = created_users["worker1"]
        worker2 = created_users["worker2"]
        client = created_users["client"]

        brigade_alpha, _ = Brigade.objects.get_or_create(
            number=1,
            defaults={
                "name_brigade": "Alpha",
                "chief": chief,
            },
        )
        brigade_alpha.chief = chief
        brigade_alpha.save()
        brigade_alpha.categories.set([cat_security, cat_monitoring])

        MemberBrigade.objects.get_or_create(
            user=worker1,
            brigade=brigade_alpha,
            defaults={"number": 1, "experience": 2},
        )
        MemberBrigade.objects.get_or_create(
            user=worker2,
            brigade=brigade_alpha,
            defaults={"number": 2, "experience": 1},
        )

        today = timezone.now().date()

        req_1, _ = ServiceRequest.objects.get_or_create(
            user=client,
            service=service_guard,
            area=area_center,
            date_start=today,
            defaults={
                "duration": "1 month",
                "comments": "Security coverage on business days.",
                "first_name": "Ivan",
                "last_name": "Petrov",
                "email": "client@example.com",
                "phone_number": "+79990000000",
                "total_price": service_guard.base_price,
                "status": status_work,
                "assigned_team": brigade_alpha,
                "address": "Lenina st, 10",
            },
        )
        req_1.status = status_work
        req_1.assigned_team = brigade_alpha
        req_1.save()

        req_2, _ = ServiceRequest.objects.get_or_create(
            user=client,
            service=service_monitoring,
            area=area_industrial,
            date_start=today + timedelta(days=3),
            defaults={
                "duration": "6 months",
                "comments": "Warehouse monitoring 24/7.",
                "first_name": "Ivan",
                "last_name": "Petrov",
                "email": "client@example.com",
                "phone_number": "+79990000000",
                "total_price": service_monitoring.base_price,
                "status": status_new,
                "assigned_team": brigade_alpha,
                "address": "Industrial st, 5",
            },
        )
        req_2.status = status_new
        req_2.assigned_team = brigade_alpha
        req_2.save()

        schedule, _ = Schedule.objects.get_or_create(
            start=today,
            end=today + timedelta(days=2),
            brigade=brigade_alpha,
            assigned_member=worker1,
            defaults={
                "task_description": "On-site duty for the client.",
                "work_days": 2,
                "service_request": req_1,
            },
        )
        schedule.service_request = req_1
        schedule.save()

        ScheduleMember.objects.get_or_create(
            user=worker1,
            date=today,
            brigade=brigade_alpha,
            service_request=req_1,
        )
        ScheduleMember.objects.get_or_create(
            user=worker2,
            date=today + timedelta(days=1),
            brigade=brigade_alpha,
            service_request=req_1,
        )

        self.stdout.write(self.style.SUCCESS("Demo data created/updated."))
        self.stdout.write("Users:")
        self.stdout.write("- admin / Admin123! (superuser)")
        self.stdout.write("- chief / Chief123! (brigade chief, staff)")
        self.stdout.write("- worker1 / Worker123!")
        self.stdout.write("- worker2 / Worker123!")
        self.stdout.write("- client / Client123!")
