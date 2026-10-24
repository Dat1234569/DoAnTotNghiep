from django.contrib.auth.models import User
from django.db import models


class SymptomKB(models.Model):
    URGENCY_CHOICES = [("Thấp", "Thấp"), ("Trung bình", "Trung bình"), ("Cao", "Cao")]
    keyword = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100, help_text="Phải trùng tên khoa khám (Department.name)")
    advice = models.TextField()
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default="Thấp")

    def __str__(self):
        return f"{self.keyword} → {self.specialty}"


class ChatLog(models.Model):
    session_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sender = models.CharField(max_length=10)  # user | bot
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
