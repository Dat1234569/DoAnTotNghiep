import json
import unicodedata
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import role_required, ROLE_HOME
from .utils import get_role
from .forms import (
    PatientRegisterForm, StaffAccountForm, DoctorAccountForm, DepartmentForm,
    DoctorEditForm, PatientForm, PatientSelfForm, AppointmentForm, ExamForm,
    PrescriptionForm, InvoiceForm, MedicineForm, ServiceForm
)
from .models import Profile, Department, Doctor, Patient, Appointment, Prescription, Invoice, Medicine, Service


# ---------------- TRANG GIỚI THIỆU (CÔNG KHAI) ----------------

def home(request):
    """Trang chủ công khai. Người đã đăng nhập vẫn có thể quay lại trang chủ."""
    departments = Department.objects.prefetch_related("doctors").order_by("name")
    services = Service.objects.select_related("department").order_by("name")[:8]
    doctors = Doctor.objects.select_related("department").order_by("full_name")[:6]
    return render(request, "app/home.html", {
        "departments": departments,
        "services": services,
        "doctors": doctors,
    })


def about(request):
    return render(request, "app/about.html", {"heading": "Giới thiệu phòng khám An Tâm", "intro": "Tìm hiểu về định hướng, dịch vụ và trải nghiệm mà An Tâm xây dựng cho người bệnh."})


def public_services(request):
    services = Service.objects.select_related("department").order_by("department__name", "name")
    departments = Department.objects.order_by("name")
    return render(request, "app/public_services.html", {"services": services, "departments": departments, "heading": "Dịch vụ Tai Mũi Họng", "intro": "Khám, tư vấn và điều trị với quy trình thuận tiện cho người bệnh."})


def public_doctors(request):
    doctors = Doctor.objects.select_related("department").order_by("full_name")
    return render(request, "app/public_doctors.html", {"doctors": doctors, "heading": "Đội ngũ bác sĩ", "intro": "Tìm hiểu bác sĩ và lịch khám được quản lý trong hệ thống An Tâm."})



def _normalize_search_text(value):
    value = (value or "").strip().lower().replace("đ", "d")
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return " ".join(value.split())



def public_search(request):
    """Tìm kiếm bác sĩ, dịch vụ và chuyên khoa trên website công khai."""
    query = request.GET.get("q", "").strip()[:120]

    doctors = []
    services = []
    departments = []

    if query:
        normalized_query = _normalize_search_text(query)
        words = normalized_query.split()

        # Nhận diện từ khóa chỉ danh mục
        doctor_keywords = {
            "bac si", "bacsi", "doi ngu bac si",
            "cac bac si", "danh sach bac si",
        }
        service_keywords = {
            "dich vu", "dichvu", "cac dich vu",
            "danh sach dich vu",
        }
        department_keywords = {
            "chuyen khoa", "chuyenkhoa", "khoa",
            "cac chuyen khoa", "danh sach chuyen khoa",
        }

        is_doctor_category = normalized_query in doctor_keywords
        is_service_category = normalized_query in service_keywords
        is_department_category = normalized_query in department_keywords

        # Tìm bác sĩ
        doctor_queryset = (
            Doctor.objects
            .select_related("department")
            .order_by("full_name")
        )

        if is_doctor_category:
            doctors = list(doctor_queryset)
        else:
            for doctor in doctor_queryset:
                department_name = (
                    doctor.department.name
                    if doctor.department_id else ""
                )

                searchable_text = _normalize_search_text(
                    f"{doctor.full_name} {department_name} "
                    f"{doctor.work_days} {doctor.work_hours}"
                )

                # Cho phép tìm theo tên, khoa, ngày hoặc giờ làm việc
                if words and all(word in searchable_text for word in words):
                    doctors.append(doctor)

        # Tìm dịch vụ
        service_queryset = (
            Service.objects
            .select_related("department")
            .order_by("name")
        )

        if is_service_category:
            services = list(service_queryset)
        else:
            for service in service_queryset:
                department_name = (
                    service.department.name
                    if service.department_id else ""
                )

                searchable_text = _normalize_search_text(
                    f"{service.name} {service.description or ''} "
                    f"{department_name}"
                )

                if words and all(word in searchable_text for word in words):
                    services.append(service)

        # Tìm chuyên khoa
        department_queryset = Department.objects.order_by("name")

        if is_department_category:
            departments = list(department_queryset)
        else:
            for department in department_queryset:
                searchable_text = _normalize_search_text(
                    f"{department.name} {department.description or ''}"
                )

                if words and all(word in searchable_text for word in words):
                    departments.append(department)

    return render(
        request,
        "app/search_results.html",
        {
            "query": query,
            "doctors": doctors,
            "services": services,
            "departments": departments,
            "has_query": bool(query),
        },
    )


def reviews(request):
    return render(request, "app/reviews.html", {"heading": "Đánh giá khách hàng", "intro": "Những cảm nhận trên giao diện mẫu; về sau có thể kết nối với đánh giá thực tế từ bệnh nhân."})


def news(request):
    return render(request, "app/news.html", {"heading": "Tin tức & kiến thức", "intro": "Các nội dung tham khảo về chăm sóc sức khỏe Tai Mũi Họng."})


def contact(request):
    return render(request, "app/contact.html", {"heading": "Liên hệ phòng khám", "intro": "Thông tin liên hệ và đường dẫn đặt lịch trực tuyến của An Tâm."})


def public_booking(request):
    """Nút Đặt lịch trên website công khai: bệnh nhân đi thẳng vào khu vực đặt lịch."""
    if not request.user.is_authenticated:
        messages.info(request, "Vui lòng đăng nhập tài khoản bệnh nhân để đặt lịch khám.")
        return redirect("login")
    if get_role(request.user) == "patient":
        return redirect("patient_home")
    messages.info(request, "Chức năng đặt lịch trực tuyến dành cho tài khoản bệnh nhân.")
    return redirect("home")


# ---------------- AUTH ----------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(get_role(request.user), "login"))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu.")
        else:
            login(request, user)
            return redirect(ROLE_HOME.get(get_role(user), "dashboard"))
    return render(request, "app/login.html")


def register_view(request):
    if request.method == "POST":
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(username=d["username"], password=d["password"], first_name=d["full_name"])
            Profile.objects.create(user=user, role="patient", phone=d.get("phone", ""))
            Patient.objects.create(
                user=user, full_name=d["full_name"], dob=d.get("dob"), gender=d.get("gender", ""),
                phone=d.get("phone", ""), address=d.get("address", ""), email=d.get("email", "")
            )
            login(request, user)
            return redirect("patient_home")
    else:
        form = PatientRegisterForm()
    return render(request, "app/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")


# ---------------- DASHBOARD ----------------

@login_required
def dashboard(request):
    role = get_role(request.user)
    if role == "patient":
        return redirect("patient_home")
    if role not in ("admin", "reception", "doctor"):
        return redirect("login")

    today = date.today()
    appts = Appointment.objects.all()
    if role == "doctor":
        doctor = getattr(request.user, "doctor_profile", None)
        appts = appts.filter(doctor=doctor) if doctor else appts.none()

    context = {
        "total_patients": Patient.objects.count(),
        "total_doctors": Doctor.objects.count(),
        "today_appts": appts.filter(appt_date=today).count(),
        "pending_appts": appts.filter(status="Chờ xác nhận").count(),
        "revenue_month": Invoice.objects.filter(
            status="Đã thanh toán", created_at__year=today.year, created_at__month=today.month
        ).aggregate(s=Sum("amount"))["s"] or 0,
        "chatbot_bookings": appts.filter(source="Chatbot AI").count(),
        "upcoming": appts.filter(appt_date__gte=today).order_by("appt_date", "appt_time")[:6],
        "by_specialty": appts.values("department__name").annotate(c=Count("id")).order_by("-c"),
    }
    return render(request, "app/dashboard.html", context)


# ---------------- KHOA KHÁM (Departments) ----------------

@login_required
@role_required("admin")
def department_list(request):
    departments = Department.objects.all().order_by("name")
    return render(request, "app/departments.html", {"departments": departments})


@login_required
@role_required("admin")
def department_save(request, pk=None):
    instance = get_object_or_404(Department, pk=pk) if pk else None
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã lưu khoa khám.")
    return redirect("department_list")


@login_required
@role_required("admin")
def department_delete(request, pk):
    get_object_or_404(Department, pk=pk).delete()
    messages.success(request, "Đã xóa khoa khám.")
    return redirect("department_list")


# ---------------- BÁC SĨ (Doctors) ----------------

@login_required
@role_required("admin", "reception", "doctor")
def doctor_list(request):
    doctors = Doctor.objects.select_related("department").order_by("full_name")
    form = DoctorAccountForm()
    departments = Department.objects.all().order_by("name")
    return render(request, "app/doctors.html", {"doctors": doctors, "form": form, "departments": departments})


@login_required
@role_required("admin")
def doctor_create(request):
    if request.method == "POST":
        form = DoctorAccountForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = None
            if d.get("username") and d.get("password"):
                user = User.objects.create_user(username=d["username"], password=d["password"], first_name=d["full_name"])
                Profile.objects.create(user=user, role="doctor", phone=d.get("phone", ""))
            Doctor.objects.create(
                user=user, full_name=d["full_name"], department=d["department"], phone=d.get("phone", ""),
                email=d.get("email", ""), work_days=d.get("work_days", ""), work_hours=d.get("work_hours", "")
            )
            messages.success(request, "Đã thêm bác sĩ.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    return redirect("doctor_list")


@login_required
@role_required("admin")
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        form = DoctorEditForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin bác sĩ.")
    return redirect("doctor_list")


@login_required
@role_required("admin")
def doctor_delete(request, pk):
    get_object_or_404(Doctor, pk=pk).delete()
    messages.success(request, "Đã xóa bác sĩ.")
    return redirect("doctor_list")


# ---------------- BỆNH NHÂN (Patients) ----------------

@login_required
@role_required("admin", "reception", "doctor")
def patient_list(request):
    q = request.GET.get("q", "").strip()
    patients = Patient.objects.all().order_by("-id")
    if q:
        patients = patients.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))
    return render(request, "app/patients.html", {"patients": patients, "q": q})


@login_required
@role_required("admin", "reception")
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm bệnh nhân.")
    return redirect("patient_list")


@login_required
@role_required("admin", "reception", "doctor")
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ bệnh nhân.")
    return redirect("patient_list")


@login_required
@role_required("admin")
def patient_delete(request, pk):
    get_object_or_404(Patient, pk=pk).delete()
    messages.success(request, "Đã xóa hồ sơ bệnh nhân.")
    return redirect("patient_list")


# ---------------- LỊCH KHÁM (Appointments) ----------------

@login_required
@role_required("admin", "reception", "doctor")
def appointment_list(request):
    role = get_role(request.user)
    status = request.GET.get("status", "")
    appts = Appointment.objects.select_related("patient", "doctor", "department").all()

    if role == "doctor":
        doctor = getattr(request.user, "doctor_profile", None)
        appts = appts.filter(doctor=doctor) if doctor else appts.none()
    if status:
        appts = appts.filter(status=status)

    context = {"appointments": appts, "status": status, "role": role}
    if role in ("admin", "reception"):
        context["form"] = AppointmentForm()
        context["all_departments"] = Department.objects.all().order_by("name")
        context["all_doctors"] = Doctor.objects.select_related("department").order_by("full_name")
    return render(request, "app/appointments.html", context)


@login_required
@role_required("admin", "reception")
def appointment_create(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.source = "Lễ tân"
            appt.save()
            messages.success(request, "Đã tạo lịch khám.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    return redirect("appointment_list")


@login_required
@role_required("admin", "reception")
def appointment_edit(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật lịch khám.")
    return redirect("appointment_list")


@login_required
@role_required("doctor")
def appointment_exam(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    doctor = getattr(request.user, "doctor_profile", None)
    if doctor is None or appt.doctor_id != doctor.id:
        messages.error(request, "Bạn không có quyền với lịch khám này.")
        return redirect("appointment_list")
    if request.method == "POST":
        form = ExamForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã lưu kết quả khám bệnh.")
    return redirect("appointment_list")


@login_required
@role_required("admin")
def appointment_delete(request, pk):
    get_object_or_404(Appointment, pk=pk).delete()
    messages.success(request, "Đã xóa lịch khám.")
    return redirect("appointment_list")


# ---------------- DỊCH VỤ & BẢNG GIÁ (Service) ----------------

@login_required
@role_required("admin", "reception")
def service_list(request):
    services = Service.objects.select_related("department").order_by("name")
    departments_all = Department.objects.all().order_by("name")
    return render(request, "app/services.html", {"services": services, "departments_all": departments_all})


@login_required
@role_required("admin")
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm dịch vụ.")
    return redirect("service_list")


@login_required
@role_required("admin")
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật dịch vụ.")
    return redirect("service_list")


@login_required
@role_required("admin")
def service_delete(request, pk):
    get_object_or_404(Service, pk=pk).delete()
    messages.success(request, "Đã xóa dịch vụ.")
    return redirect("service_list")


# ---------------- BÁO CÁO THỐNG KÊ (Reports) ----------------

@login_required
@role_required("admin")
def reports(request):
    today = date.today()
    months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    month_labels = [f"{m:02d}/{y}" for y, m in months]
    visits_by_month = []
    revenue_by_month = []
    for y, m in months:
        visits_by_month.append(Appointment.objects.filter(appt_date__year=y, appt_date__month=m).count())
        rev = Invoice.objects.filter(status="Đã thanh toán", created_at__year=y, created_at__month=m).aggregate(s=Sum("amount"))["s"] or 0
        revenue_by_month.append(rev)

    total_patients = Patient.objects.count()
    new_patients_this_month = Patient.objects.filter(created_at__year=today.year, created_at__month=today.month).count()

    symptom_stats = list(
        Appointment.objects.exclude(department__isnull=True)
        .values("department__name").annotate(c=Count("id")).order_by("-c")
    )

    context = {
        "month_labels": json.dumps(month_labels),
        "visits_by_month": json.dumps(visits_by_month),
        "revenue_by_month": json.dumps(revenue_by_month),
        "total_patients": total_patients,
        "new_patients_this_month": new_patients_this_month,
        "symptom_labels": json.dumps([s["department__name"] for s in symptom_stats]),
        "symptom_data": json.dumps([s["c"] for s in symptom_stats]),
    }
    return render(request, "app/reports.html", context)


# ---------------- KHO THUỐC (Medicine) ----------------

@login_required
@role_required("admin", "doctor")
def medicine_list(request):
    medicines = Medicine.objects.all().order_by("name")
    return render(request, "app/medicines.html", {"medicines": medicines})


@login_required
@role_required("admin")
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm thuốc vào kho.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    return redirect("medicine_list")


@login_required
@role_required("admin")
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin thuốc.")
    return redirect("medicine_list")


@login_required
@role_required("admin")
def medicine_delete(request, pk):
    get_object_or_404(Medicine, pk=pk).delete()
    messages.success(request, "Đã xóa thuốc khỏi kho.")
    return redirect("medicine_list")


# ---------------- ĐƠN THUỐC (Prescriptions) ----------------

@login_required
@role_required("admin", "reception", "doctor")
def prescription_list(request):
    role = get_role(request.user)

    rx = (
        Prescription.objects
        .select_related(
            "appointment",
            "appointment__patient",
            "appointment__doctor"
        )
        .order_by("-id")
    )

    if role == "doctor":
        doctor = getattr(request.user, "doctor_profile", None)
        rx = (
            rx.filter(appointment__doctor=doctor)
            if doctor else rx.none()
        )

    appts = (
        Appointment.objects
        .select_related("patient")
        .order_by("-appt_date", "-appt_time")
    )

    if role == "doctor":
        doctor = getattr(request.user, "doctor_profile", None)
        appts = (
            appts.filter(doctor=doctor)
            if doctor else appts.none()
        )

    parsed = []

    for r in rx:
        try:
            meds = json.loads(r.medicines or "[]")
        except (json.JSONDecodeError, TypeError):
            meds = []

        parsed.append({
            "obj": r,
            "med_count": len(meds),
        })

    # Chuyển QuerySet thành list để json_script trong HTML có thể xử lý
    medicines = list(
        Medicine.objects
        .all()
        .order_by("name")
        .values(
            "id",
            "name",
            "quantity",
            "unit",
        )
    )

    return render(
        request,
        "app/prescriptions.html",
        {
            "rx_list": parsed,
            "appointments": appts,
            "role": role,
            "medicines": medicines,
        }
    )


@login_required
@role_required("admin", "doctor")
def prescription_create(request):
    if request.method == "POST":
        appointment_id = request.POST.get("appointment")
        diagnosis = request.POST.get("diagnosis", "")
        note = request.POST.get("note", "")
        medicine_ids = request.POST.getlist("med_id")
        quantities = request.POST.getlist("med_qty")

        appt = get_object_or_404(Appointment, pk=appointment_id)
        medicines = []
        for i, med_id in enumerate(medicine_ids):
            if not med_id:
                continue
            qty = int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else 1
            med = Medicine.objects.filter(id=med_id).first()
            if not med:
                continue
            medicines.append({"medicine_id": med.id, "name": med.name, "dose": f"{qty} {med.unit or 'đơn vị'}", "quantity": qty})
            # Trừ tồn kho (không cho âm)
            med.quantity = max(0, med.quantity - qty)
            med.save()

        Prescription.objects.create(appointment=appt, diagnosis=diagnosis, medicines=json.dumps(medicines, ensure_ascii=False), note=note)
        appt.status = "Hoàn thành"
        appt.save()
        messages.success(request, "Đã tạo đơn thuốc và cập nhật kho thuốc.")
    return redirect("prescription_list")


@login_required
@role_required("admin")
def prescription_delete(request, pk):
    get_object_or_404(Prescription, pk=pk).delete()
    messages.success(request, "Đã xóa đơn thuốc.")
    return redirect("prescription_list")


# ---------------- HÓA ĐƠN (Invoices) ----------------

@login_required
@role_required("admin", "reception")
def invoice_list(request):
    invoices = Invoice.objects.select_related("appointment", "appointment__patient", "appointment__doctor").order_by("-id")
    appointments = Appointment.objects.select_related("patient").order_by("-appt_date")
    services = Service.objects.all().order_by("name")
    return render(request, "app/invoices.html", {"invoices": invoices, "appointments": appointments, "services": services, "form": InvoiceForm()})


@login_required
@role_required("admin", "reception")
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            method = request.POST.get("payment_method", "cash")
            invoice.payment_method = method if method in ("cash", "qr") else "cash"
            if invoice.payment_method == "qr":
                invoice.status = "Chưa thanh toán"
            invoice.save()
            messages.success(request, "Đã tạo hóa đơn. Hãy xác nhận thanh toán sau khi nhận tiền.")
        else:
            messages.error(request, "Không thể tạo hóa đơn. Vui lòng kiểm tra dữ liệu.")
    return redirect("invoice_list")


@login_required
@role_required("admin", "reception")
def invoice_mark_paid(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        inv.status = "Đã thanh toán"
        inv.save(update_fields=["status"])
        messages.success(request, "Đã xác nhận hóa đơn đã thanh toán.")
    return redirect("invoice_list")


@login_required
@role_required("admin")
def invoice_delete(request, pk):
    get_object_or_404(Invoice, pk=pk).delete()
    messages.success(request, "Đã xóa hóa đơn.")
    return redirect("invoice_list")


# ---------------- TÀI KHOẢN NHÂN VIÊN (Staff) ----------------

@login_required
@role_required("admin")
def staff_list(request):
    staff_profiles = Profile.objects.filter(role__in=["admin", "reception"]).select_related("user")
    return render(request, "app/staff.html", {"staff_profiles": staff_profiles, "form": StaffAccountForm()})


@login_required
@role_required("admin")
def staff_create(request):
    if request.method == "POST":
        form = StaffAccountForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(username=d["username"], password=d["password"], first_name=d["full_name"])
            if d["role"] == "admin":
                user.is_staff = True
                user.save()
            Profile.objects.create(user=user, role=d["role"], phone=d.get("phone", ""))
            messages.success(request, "Đã tạo tài khoản.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    return redirect("staff_list")


@login_required
@role_required("admin")
def staff_delete(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    profile.user.delete()
    messages.success(request, "Đã xóa tài khoản.")
    return redirect("staff_list")


# ---------------- TRANG BỆNH NHÂN ----------------

@login_required
@role_required("patient")
def patient_home(request):
    patient = getattr(request.user, "patient_profile", None)
    appts = Appointment.objects.filter(patient=patient).select_related("doctor", "department").order_by("-appt_date", "-appt_time") if patient else []
    rx = Prescription.objects.filter(appointment__patient=patient).select_related("appointment", "appointment__doctor").order_by("-id") if patient else []
    invoices = Invoice.objects.filter(appointment__patient=patient).select_related("appointment").order_by("-id") if patient else []
    departments = Department.objects.all().order_by("name")

    rx_parsed = []
    for r in rx:
        try:
            meds = json.loads(r.medicines or "[]")
        except (json.JSONDecodeError, TypeError):
            meds = []
        rx_parsed.append({"obj": r, "meds": meds})

    return render(request, "app/patient_home.html", {
        "patient": patient, "appointments": appts, "rx_list": rx_parsed,
        "invoices": invoices, "departments": departments,
    })


@login_required
@role_required("patient")
def patient_profile_save(request):
    patient = getattr(request.user, "patient_profile", None)
    if request.method == "POST" and patient:
        form = PatientSelfForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật hồ sơ cá nhân.")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin.")
    return redirect("patient_home")


@login_required
@role_required("patient")
def patient_book_appointment(request):
    patient = getattr(request.user, "patient_profile", None)
    if request.method == "POST" and patient:
        department_id = request.POST.get("department")
        appt_date = request.POST.get("appt_date")
        appt_time = request.POST.get("appt_time")
        symptom_note = request.POST.get("symptom_note", "")

        if not appt_date or not appt_time:
            messages.error(request, "Vui lòng chọn ngày và giờ khám.")
            return redirect("patient_home")

        department = Department.objects.filter(id=department_id).first() if department_id else None
        doctor = Doctor.objects.filter(department=department).order_by("?").first() if department else None

        Appointment.objects.create(
            patient=patient, doctor=doctor, department=department, appt_date=appt_date, appt_time=appt_time,
            symptom_note=symptom_note, source="Lễ tân", status="Chờ xác nhận",
        )
        messages.success(request, "Đã đặt lịch khám thành công. Vui lòng chờ xác nhận.")
    return redirect("patient_home")
