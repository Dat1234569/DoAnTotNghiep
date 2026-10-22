from django.contrib import admin
from .models import Profile, Department, Doctor, Patient, Appointment, Prescription, Invoice, Medicine, Service

admin.site.register(Profile)
admin.site.register(Department)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Prescription)
admin.site.register(Invoice)
admin.site.register(Medicine)
admin.site.register(Service)
