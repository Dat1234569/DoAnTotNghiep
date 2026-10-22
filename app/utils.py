def get_role(user):
    """Trả về vai trò của user. Superuser (tạo bằng createsuperuser) luôn được coi là admin."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    profile = getattr(user, "profile", None)
    return profile.role if profile else None
