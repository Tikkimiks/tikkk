import os
import django
import json
from decimal import Decimal

# Укажите путь к вашему файлу settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'security.settings')
django.setup()

from main.models import ServiceCategory, Status, Tariff, Service, Area

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def backup_data():
    data = {
        'ServiceCategory': list(ServiceCategory.objects.all().values()),
        'Status': list(Status.objects.all().values()),
        'Tariff': list(Tariff.objects.all().values()),
        'Service': list(Service.objects.all().values()),
        'Area': list(Area.objects.all().values()),
    }
    with open('backup.json', 'w') as f:
        json.dump(data, f, default=decimal_default)

if __name__ == "__main__":
    backup_data()
