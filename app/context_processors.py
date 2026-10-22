from .utils import get_role


def user_role(request):
    role = get_role(request.user) if request.user.is_authenticated else None
    return {"current_role": role}
