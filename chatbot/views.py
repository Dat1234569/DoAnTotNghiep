import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from app.decorators import role_required
from app.models import Patient, Department, Doctor, Appointment

from .models import ChatLog
from .utils import (
    rule_based_reply,
    gemini_reply,
    detect_natural_symptoms,
)


# =========================================================
# SAVE CHAT LOG
# =========================================================

def _save_log(session_id, user, sender, message):
    ChatLog.objects.create(
        session_id=session_id,
        user=user if user.is_authenticated else None,
        sender=sender,
        message=message,
    )


# =========================================================
# XÁC ĐỊNH CHUYÊN KHOA
# =========================================================

def _detect_specialties(message):
    """
    Xác định chuyên khoa dựa trên câu người dùng.

    Ví dụ:
        "Tôi đau họng và nuốt nước bọt hơi đau"
        => ["Họng"]

        "Tai tôi ù và nghe không rõ"
        => ["Tai"]

        "Mũi bị nghẹt và chảy nước"
        => ["Mũi"]
    """

    symptoms = detect_natural_symptoms(message)

    specialty_map = {
        # =========================
        # TAI
        # =========================
        "ù tai": "Tai",
        "giảm thính lực": "Tai",
        "đau tai": "Tai",
        "ngứa tai": "Tai",
        "đầy tai": "Tai",
        "chảy dịch tai": "Tai",
        "chảy mủ tai": "Tai",
        "chóng mặt": "Tai",

        # =========================
        # MŨI
        # =========================
        "nghẹt mũi": "Mũi",
        "chảy nước mũi": "Mũi",
        "hắt hơi": "Mũi",
        "ngứa mũi": "Mũi",
        "chảy máu cam": "Mũi",
        "mất khứu giác": "Mũi",
        "đau vùng trán": "Mũi",
        "đau gò má": "Mũi",
        "đau nhức mặt": "Mũi",

        # =========================
        # HỌNG
        # =========================
        "đau họng": "Họng",
        "rát họng": "Họng",
        "đau khi nuốt": "Họng",
        "khó nuốt": "Họng",
        "nuốt vướng": "Họng",
        "khàn tiếng": "Họng",
        "mất tiếng": "Họng",
        "ho": "Họng",
        "ho khan": "Họng",
        "ho có đờm": "Họng",
        "hôi miệng": "Họng",
        "nổi hạch cổ": "Họng",
        "khô họng": "Họng",
    }

    specialties = []

    for symptom in symptoms:

        specialty = specialty_map.get(symptom)

        if specialty and specialty not in specialties:
            specialties.append(specialty)

    return specialties


# =========================================================
# CHAT MESSAGE
# =========================================================

@login_required
@role_required("patient")
@require_POST
def chat_message(request):

    # -----------------------------------------
    # Đọc JSON
    # -----------------------------------------

    try:

        data = json.loads(
            request.body.decode("utf-8")
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "error": "Dữ liệu không hợp lệ"
            },
            status=400,
        )

    # -----------------------------------------
    # Lấy message
    # -----------------------------------------

    message = (
        data.get("message") or ""
    ).strip()

    history = data.get("history") or []

    if not message:

        return JsonResponse(
            {
                "error": "Thiếu nội dung tin nhắn"
            },
            status=400,
        )

    # -----------------------------------------
    # Session
    # -----------------------------------------

    session_id = f"user-{request.user.id}"

    # Lưu câu hỏi người dùng
    _save_log(
        session_id,
        request.user,
        "user",
        message,
    )

    # =====================================================
    # XÁC ĐỊNH CHUYÊN KHOA TỪ CÂU NGƯỜI DÙNG
    # =====================================================

    detected_specialties = _detect_specialties(message)

    # =====================================================
    # GỌI GEMINI
    # =====================================================

    ai_text = gemini_reply(
        message,
        history,
    )

    # =====================================================
    # NẾU GEMINI HOẠT ĐỘNG
    # =====================================================

    if ai_text:

        # ---------------------------------------------
        # Nếu phát hiện chuyên khoa từ câu người dùng
        # ---------------------------------------------

        suggestions = detected_specialties

        # ---------------------------------------------
        # Nếu Gemini trả lời có nhắc chuyên khoa
        # nhưng detector chưa bắt được
        # ---------------------------------------------

        ai_lower = ai_text.lower()

        if not suggestions:

            if "nhóm khám: tai" in ai_lower:
                suggestions = ["Tai"]

            elif "nhóm khám: mũi" in ai_lower:
                suggestions = ["Mũi"]

            elif "nhóm khám: họng" in ai_lower:
                suggestions = ["Họng"]

            elif "chuyên khoa: tai" in ai_lower:
                suggestions = ["Tai"]

            elif "chuyên khoa: mũi" in ai_lower:
                suggestions = ["Mũi"]

            elif "chuyên khoa: họng" in ai_lower:
                suggestions = ["Họng"]

        # ---------------------------------------------
        # Có thể đặt lịch nếu xác định được chuyên khoa
        # ---------------------------------------------

        can_book = bool(suggestions)

        result = {
            "reply": ai_text,
            "suggestions": suggestions,
            "canBook": can_book,
            "mode": "ai",
        }

    # =====================================================
    # NẾU GEMINI KHÔNG HOẠT ĐỘNG
    # =====================================================

    else:

        rb = rule_based_reply(message)

        result = {
            "reply": rb["reply"],
            "suggestions": rb["suggestions"],
            "canBook": rb["can_book"],
            "mode": "rule-based",
        }

    # =====================================================
    # LƯU CÂU TRẢ LỜI BOT
    # =====================================================

    _save_log(
        session_id,
        request.user,
        "bot",
        result["reply"],
    )

    # =====================================================
    # TRẢ JSON CHO FRONTEND
    # =====================================================

    return JsonResponse(result)


# =========================================================
# BOOK APPOINTMENT
# =========================================================

@login_required
@role_required("patient")
@require_POST
def chat_book(request):

    # -----------------------------------------
    # Đọc JSON
    # -----------------------------------------

    try:

        data = json.loads(
            request.body.decode("utf-8")
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "error": "Dữ liệu không hợp lệ"
            },
            status=400,
        )

    # -----------------------------------------
    # Lấy dữ liệu
    # -----------------------------------------

    specialty = (
        data.get("specialty") or ""
    ).strip()

    appt_date = data.get(
        "appt_date"
    )

    appt_time = data.get(
        "appt_time"
    )

    symptom_note = (
        data.get("symptom_note") or ""
    ).strip()

    # -----------------------------------------
    # Kiểm tra ngày giờ
    # -----------------------------------------

    if not appt_date or not appt_time:

        return JsonResponse(
            {
                "error": "Thiếu ngày/giờ khám"
            },
            status=400,
        )

    # -----------------------------------------
    # Lấy bệnh nhân
    # -----------------------------------------

    patient = getattr(
        request.user,
        "patient_profile",
        None,
    )

    if patient is None:

        return JsonResponse(
            {
                "error": "Không tìm thấy hồ sơ bệnh nhân"
            },
            status=400,
        )

    # =====================================================
    # TÌM KHOA
    # =====================================================

    department = None

    if specialty:

        department = (
            Department.objects
            .filter(name__iexact=specialty)
            .first()
        )

    # =====================================================
    # NẾU KHÔNG TÌM THẤY KHOA
    # =====================================================

    if specialty and department is None:

        return JsonResponse(
            {
                "error": (
                    f"Không tìm thấy chuyên khoa "
                    f"'{specialty}' trong hệ thống."
                )
            },
            status=400,
        )

    # =====================================================
    # TÌM BÁC SĨ
    # =====================================================

    doctor = None

    if department:

        doctor = (
            Doctor.objects
            .filter(
                department=department
            )
            .order_by("?")
            .first()
        )

    # =====================================================
    # TẠO LỊCH KHÁM
    # =====================================================

    appt = Appointment.objects.create(
        patient=patient,

        doctor=doctor,

        department=department,

        appt_date=appt_date,

        appt_time=appt_time,

        symptom_note=symptom_note,

        source="Chatbot AI",

        status="Chờ xác nhận",
    )

    # =====================================================
    # LƯU LOG
    # =====================================================

    doctor_text = ""

    if doctor:
        doctor_text = (
            f" Bác sĩ phụ trách: {doctor.full_name}."
        )

    success_message = (
        f"Đã đặt lịch khám thành công vào "
        f"{appt_date} lúc {appt_time}."
        f"{doctor_text}"
    )

    _save_log(
        f"user-{request.user.id}",
        request.user,
        "bot",
        success_message,
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return JsonResponse(
        {
            "ok": True,

            "appointment_id": appt.id,

            "doctor_name": (
                doctor.full_name
                if doctor
                else None
            ),

            "department": (
                department.name
                if department
                else None
            ),

            "message": success_message,
        }
    )