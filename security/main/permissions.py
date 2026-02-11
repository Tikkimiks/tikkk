from .models import MemberBrigade


def is_employee(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or MemberBrigade.objects.filter(user=user).exists()
