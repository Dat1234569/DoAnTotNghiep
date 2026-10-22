from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .utils import get_role

ROLE_HOME = {"admin": "dashboard", "reception": "dashboard", "doctor": "dashboard", "patient": "patient_home"}


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            role = get_role(request.user)
            if role not in roles:
                messages.error(request, "Bạn không có quyền truy cập trang này.")
                return redirect(ROLE_HOME.get(role, "login"))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
