from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Các trang công khai của website
    path("gioi-thieu/", views.about, name="about"),
    path("dich-vu/", views.public_services, name="public_services"),
    path("bac-si/", views.public_doctors, name="public_doctors"),
    path("danh-gia/", views.reviews, name="reviews"),
    path("tin-tuc/", views.news, name="news"),
    path("lien-he/", views.contact, name="contact"),
    path("dat-lich/", views.public_booking, name="public_booking"),
    path("tim-kiem/", views.public_search, name="public_search"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("patient/", views.patient_home, name="patient_home"),
    path("patient/profile/save/", views.patient_profile_save, name="patient_profile_save"),
    path("patient/book/", views.patient_book_appointment, name="patient_book_appointment"),

    path("departments/", views.department_list, name="department_list"),
    path("departments/save/", views.department_save, name="department_save"),
    path("departments/<int:pk>/save/", views.department_save, name="department_save_edit"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),

    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/create/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),

    path("patients/", views.patient_list, name="patient_list"),
    path("patients/create/", views.patient_create, name="patient_create"),
    path("patients/<int:pk>/edit/", views.patient_edit, name="patient_edit"),
    path("patients/<int:pk>/delete/", views.patient_delete, name="patient_delete"),

    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/create/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/exam/", views.appointment_exam, name="appointment_exam"),
    path("appointments/<int:pk>/delete/", views.appointment_delete, name="appointment_delete"),

    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/create/", views.prescription_create, name="prescription_create"),
    path("prescriptions/<int:pk>/delete/", views.prescription_delete, name="prescription_delete"),

    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/create/", views.medicine_create, name="medicine_create"),
    path("medicines/<int:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("medicines/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),

    path("services/", views.service_list, name="service_list"),
    path("services/create/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),

    path("reports/", views.reports, name="reports"),

    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:pk>/paid/", views.invoice_mark_paid, name="invoice_mark_paid"),
    path("invoices/<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),

    path("staff/", views.staff_list, name="staff_list"),
    path("staff/create/", views.staff_create, name="staff_create"),
    path("staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),
]
