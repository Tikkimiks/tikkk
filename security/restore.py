import os
import django
import json
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist

# Укажите путь к вашему файлу settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'security.settings')
django.setup()

from main.models import ServiceCategory, Status, Tariff, Service, Area

def restore_data():
    with open('backup.json', 'r') as f:
        data = json.load(f)

        # Восстановление категорий услуг
        for item in data.get('ServiceCategory', []):
            if 'id' in item:
                category, created = ServiceCategory.objects.update_or_create(
                    id=item['id'], defaults=item
                )

        # Восстановление статусов
        for item in data.get('Status', []):
            if 'id' in item:
                status, created = Status.objects.update_or_create(
                    id=item['id'], defaults=item
                )

        # Восстановление тарифов
        for item in data.get('Tariff', []):
            if 'id' in item:
                item['price'] = Decimal(str(item['price']))  # Преобразуем цену обратно в Decimal
                tariff, created = Tariff.objects.update_or_create(
                    id=item['id'], defaults=item
                )

        # Восстановление услуг
        for item in data.get('Service', []):
            if 'id_service' in item:
                try:
                    category_id = item.get('category', None)
                    category = ServiceCategory.objects.get(pk=category_id) if category_id else None
                except ObjectDoesNotExist:
                    category = None

                service, created = Service.objects.update_or_create(
                    id_service=item['id_service'],
                    defaults={
                        'name_service': item['name_service'],
                        'description': item['description'],
                        'base_price': Decimal(str(item['base_price'])),  # Преобразуем цену обратно в Decimal
                        'alarm_system_discount': Decimal(str(item['alarm_system_discount'])),  # Преобразуем скидку обратно в Decimal
                        'category': category
                    }
                )
                if 'tariffs' in item:
                    tariffs = item['tariffs']
                    service.tariffs.set(Tariff.objects.filter(id__in=tariffs))
                service.save()

        # Восстановление зон
        for item in data.get('Area', []):
            if 'id' in item:
                area, created = Area.objects.update_or_create(
                    id=item['id'], defaults=item
                )

if __name__ == "__main__":
    restore_data()