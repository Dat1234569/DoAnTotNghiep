from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Quản trị viên"),
        ("reception", "Lễ tân"),
        ("doctor", "Bác sĩ"),
        ("patient", "Bệnh nhân"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doctor_profile")
    full_name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="doctors")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    work_days = models.CharField(max_length=50, blank=True, help_text="vd: T2,T3,T4")
    work_hours = models.CharField(max_length=50, blank=True, help_text="vd: 08:00 - 17:00")
    avatar_color = models.CharField(max_length=10, default="#2451B0")

    def __str__(self):
        return self.full_name


class Patient(models.Model):
    GENDER_CHOICES = [("Nam", "Nam"), ("Nữ", "Nữ"), ("Khác", "Khác")]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="patient_profile")
    full_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    allergies = models.TextField(blank=True, help_text="Dị ứng (nếu có)")
    medical_history = models.TextField(blank=True, help_text="Tiền sử bệnh / hồ sơ bệnh án")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("Chờ xác nhận", "Chờ xác nhận"),
        ("Đã xác nhận", "Đã xác nhận"),
        ("Đang khám", "Đang khám"),
        ("Đã khám", "Đã khám"),
        ("Đã hủy", "Đã hủy"),
        ("Không đến", "Không đến"),
    ]
    SOURCE_CHOICES = [("Lễ tân", "Lễ tân"), ("Chatbot AI", "Chatbot AI"), ("Bệnh nhân", "Bệnh nhân")]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    appt_date = models.DateField()
    appt_time = models.TimeField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Chờ xác nhận")
    symptom_note = models.TextField(blank=True)
    exam_result = models.TextField(blank=True, help_text="Kết quả khám lâm sàng")
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    doctor_note = models.TextField(blank=True, help_text="Lời dặn của bác sĩ")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="Lễ tân")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-appt_date", "appt_time"]

    def __str__(self):
        return f"{self.patient.full_name} - {self.appt_date} {self.appt_time}"


class Medicine(models.Model):
    name = models.CharField(max_length=150, verbose_name="Tên thuốc")
    category = models.CharField(max_length=100, blank=True, verbose_name="Loại thuốc")
    quantity = models.IntegerField(default=0, verbose_name="Số lượng tồn kho")
    unit = models.CharField(max_length=30, blank=True, verbose_name="Đơn vị", help_text="vd: viên, chai, gói")
    price = models.IntegerField(default=0, verbose_name="Giá (VNĐ/đơn vị)")
    manufacturer = models.CharField(max_length=150, blank=True, verbose_name="Nhà sản xuất")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Hạn sử dụng")

    def __str__(self):
        return self.name


class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="prescriptions")
    diagnosis = models.CharField(max_length=255, blank=True)
    medicines = models.TextField(blank=True, help_text="JSON: [{medicine_id, name, dose, quantity}]")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Service(models.Model):
    name = models.CharField(max_length=150, verbose_name="Tên dịch vụ")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="services")
    price = models.IntegerField(default=0, verbose_name="Giá (VNĐ)")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} — {self.price} đ"


class Invoice(models.Model):
    STATUS_CHOICES = [("Chưa thanh toán", "Chưa thanh toán"), ("Đã thanh toán", "Đã thanh toán")]
    PAYMENT_METHOD_CHOICES = [("cash", "Tiền mặt"), ("qr", "Chuyển khoản QR")]
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="invoices")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField(default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default="cash")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Chưa thanh toán")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
