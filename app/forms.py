from django import forms
from django.contrib.auth.models import User
from .models import Department, Doctor, Patient, Appointment, Prescription, Invoice, Medicine, Service


class PatientRegisterForm(forms.Form):
    full_name = forms.CharField(label="Họ và tên", max_length=100)
    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput, min_length=6)
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False)
    dob = forms.DateField(
        label="Ngày sinh",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "lang": "vi"}),
    )
    gender = forms.ChoiceField(label="Giới tính", choices=Patient.GENDER_CHOICES, required=False)
    email = forms.EmailField(label="Email", required=False)
    address = forms.CharField(label="Địa chỉ", max_length=255, required=False)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập đã tồn tại.")
        return username


class StaffAccountForm(forms.Form):
    ROLE_CHOICES = [("reception", "Lễ tân"), ("admin", "Quản trị viên")]
    full_name = forms.CharField(label="Họ và tên", max_length=100)
    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput, min_length=6)
    role = forms.ChoiceField(label="Vai trò", choices=ROLE_CHOICES)
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False)
    email = forms.EmailField(label="Email", required=False)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập đã tồn tại.")
        return username


class DoctorAccountForm(forms.Form):
    full_name = forms.CharField(label="Họ và tên", max_length=100)
    department = forms.ModelChoiceField(label="Khoa khám", queryset=Department.objects.all())
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False)
    email = forms.EmailField(label="Email", required=False)
    work_days = forms.CharField(label="Ngày làm việc", max_length=50, required=False, help_text="vd: T2,T3,T4")
    work_hours = forms.CharField(label="Giờ làm việc", max_length=50, required=False, help_text="vd: 08:00 - 17:00")
    username = forms.CharField(label="Tên đăng nhập", max_length=150, required=False)
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput, required=False)

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập đã tồn tại.")
        return username


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class DoctorEditForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["full_name", "department", "phone", "email", "work_days", "work_hours"]


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["full_name", "dob", "gender", "phone", "address", "email", "allergies", "medical_history"]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "medical_history": forms.Textarea(attrs={"rows": 3}),
        }


class PatientSelfForm(forms.ModelForm):
    """Bệnh nhân dùng form này để tự cập nhật hồ sơ của mình."""
    class Meta:
        model = Patient
        fields = ["full_name", "dob", "gender", "phone", "address", "email", "allergies", "medical_history"]
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "allergies": forms.TextInput(),
            "medical_history": forms.Textarea(attrs={"rows": 3}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "department", "appt_date", "appt_time", "symptom_note", "status"]
        widgets = {
            "appt_date": forms.DateInput(attrs={"type": "date"}),
            "appt_time": forms.TimeInput(attrs={"type": "time"}),
            "symptom_note": forms.Textarea(attrs={"rows": 2}),
        }


class ExamForm(forms.ModelForm):
    """Bác sĩ dùng form này để nhập kết quả khám bệnh."""
    class Meta:
        model = Appointment
        fields = ["diagnosis", "treatment", "status"]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 2}),
            "treatment": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [
            ("Đã xác nhận", "Đã xác nhận"), ("Hoàn thành", "Hoàn thành"), ("Đã hủy", "Đã hủy")
        ]


class PrescriptionForm(forms.Form):
    appointment = forms.ModelChoiceField(label="Chọn lượt khám", queryset=Appointment.objects.all())
    diagnosis = forms.CharField(label="Chẩn đoán", max_length=255, required=False)
    note = forms.CharField(label="Ghi chú", widget=forms.Textarea(attrs={"rows": 2}), required=False)


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "category", "quantity", "unit", "price", "manufacturer", "expiry_date"]
        widgets = {"expiry_date": forms.DateInput(attrs={"type": "date"})}


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "department", "price", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["appointment", "service", "amount", "status"]
