import json
import os
import re

import requests
from django.conf import settings

from .models import SymptomKB


# =========================================================
# GEMINI CONFIG
# =========================================================

GEMINI_MODEL = "gemini-flash-latest"

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
Bạn là trợ lý AI tư vấn sức khỏe sơ bộ cho
Phòng khám Chuyên khoa Tai Mũi Họng An Tâm Đà Nẵng.

PHẠM VI PHÒNG KHÁM:
- Tai
- Mũi
- Họng

Bạn KHÔNG phải bác sĩ và không được khẳng định chẩn đoán chắc chắn.
Chỉ đưa ra tư vấn sơ bộ dựa trên triệu chứng người dùng mô tả.

========================
QUY TẮC HIỂU NGÔN NGỮ
========================

Hãy hiểu câu nói tự nhiên của người dùng, không yêu cầu họ phải
dùng đúng từ khóa.

Ví dụ:

"Tôi bị đau họng"
=> hiểu là triệu chứng đau họng
=> nhóm khám: Họng

"Tôi cảm thấy đau họng và nuốt nước bọt thì hơi đau"
=> hiểu là:
- đau họng
- đau khi nuốt
=> nhóm khám: Họng

"Cổ họng tôi rát, ăn uống cũng đau"
=> hiểu là:
- rát họng
- đau khi nuốt
=> nhóm khám: Họng

"Tai tôi cứ kêu tiếng ve ve"
=> hiểu là ù tai
=> nhóm khám: Tai

"Tai tôi nghe không được rõ như trước"
=> hiểu là giảm thính lực
=> nhóm khám: Tai

"Mũi tôi nghẹt, cứ chảy nước mũi"
=> hiểu là nghẹt mũi + chảy nước mũi
=> nhóm khám: Mũi

"Tôi hắt hơi liên tục, mũi ngứa và chảy nước"
=> hiểu là các triệu chứng ở mũi
=> nhóm khám: Mũi

========================
CÁCH TRẢ LỜI
========================

- Trả lời bằng tiếng Việt.
- Ngắn gọn, dễ hiểu.
- Có thể giải thích triệu chứng có thể liên quan đến vấn đề gì,
  nhưng KHÔNG khẳng định người dùng chắc chắn mắc bệnh.
- Nếu có nhiều triệu chứng, hãy tổng hợp chúng.
- Chỉ gợi ý nhóm khám trong 3 nhóm:
  + Tai
  + Mũi
  + Họng
- Luôn nhắc đây chỉ là tư vấn sơ bộ và không thay thế bác sĩ.
- Nếu phù hợp, hỏi người dùng có muốn đặt lịch khám không.

========================
TRIỆU CHỨNG NGUY HIỂM
========================

Nếu người dùng có:
- khó thở nặng
- mất ý thức
- chảy máu nhiều
- chảy máu tai/mũi không cầm được
- đau dữ dội bất thường
- triệu chứng nghiêm trọng khác

=> khuyên người dùng đến cơ sở y tế/cấp cứu ngay.

========================
NGOÀI PHẠM VI
========================

Nếu người dùng hỏi về:
- đau bụng
- đau chân
- đau tay
- bệnh da
- bệnh tim
- bệnh dạ dày
- hoặc vấn đề không thuộc Tai Mũi Họng

=> lịch sự giải thích phòng khám chỉ chuyên Tai Mũi Họng
và khuyên tìm cơ sở y tế phù hợp.

Không được cố gán những triệu chứng ngoài Tai Mũi Họng
vào Tai, Mũi hoặc Họng.
"""


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(text):
    """
    Chuẩn hóa câu người dùng để việc tìm triệu chứng dễ hơn.
    """

    if not text:
        return ""

    text = text.lower().strip()

    # Một số cách viết thường gặp
    replacements = {
        "  ": " ",
        "nuốt nước bọt": "nuốt nước bọt",
        "nuot nuoc bot": "nuốt nước bọt",
        "đau cổ họng": "đau họng",
        "đau ở cổ họng": "đau họng",
        "cổ họng đau": "đau họng",
        "họng đau": "đau họng",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# =========================================================
# NATURAL LANGUAGE SYMPTOM DETECTION
# =========================================================

def detect_natural_symptoms(message):
    """
    Phát hiện các cách diễn đạt tự nhiên của người dùng.

    Ví dụ:
    "nuốt nước bọt nó hơi đau"
    => "đau khi nuốt"

    "tai cứ kêu ve ve"
    => "ù tai"
    """

    text = normalize_text(message)

    detected = []

    patterns = [

        # =================================================
        # TAI
        # =================================================

        (
            [
                "tiếng ve",
                "tiếng ve ve",
                "ve ve trong tai",
                "tai kêu",
                "tai cứ kêu",
                "tai có tiếng kêu",
                "tiếng kêu trong tai",
                "tiếng vo ve",
                "vo ve trong tai",
                "ù ù trong tai",
                "tai ù",
                "bị ù tai",
            ],
            "ù tai",
        ),

        (
            [
                "nghe không rõ",
                "nghe không được rõ",
                "nghe kém",
                "nghe nhỏ",
                "tai nghe kém",
                "thính lực giảm",
                "không nghe rõ",
                "nghe không tốt",
            ],
            "giảm thính lực",
        ),

        (
            [
                "đau tai",
                "tai bị đau",
                "tai đau",
                "đau trong tai",
                "đau ở tai",
            ],
            "đau tai",
        ),

        (
            [
                "ngứa tai",
                "tai bị ngứa",
                "tai rất ngứa",
                "ngứa trong tai",
            ],
            "ngứa tai",
        ),

        (
            [
                "đầy tai",
                "tai bị đầy",
                "cảm giác đầy tai",
                "bịt tai",
                "bít tai",
                "tai bị bít",
            ],
            "đầy tai",
        ),

        (
            [
                "chảy dịch tai",
                "tai chảy dịch",
                "tai có dịch",
                "chảy nước ở tai",
            ],
            "chảy dịch tai",
        ),

        (
            [
                "chảy mủ tai",
                "tai chảy mủ",
                "tai có mủ",
            ],
            "chảy mủ tai",
        ),

        (
            [
                "chóng mặt",
                "hay chóng mặt",
                "bị chóng mặt",
                "cảm giác chóng mặt",
            ],
            "chóng mặt",
        ),

        # =================================================
        # MŨI
        # =================================================

        (
            [
                "mũi bị nghẹt",
                "mũi nghẹt",
                "nghẹt mũi",
                "bị nghẹt mũi",
                "khó thở bằng mũi",
                "mũi không thông",
            ],
            "nghẹt mũi",
        ),

        (
            [
                "sổ mũi",
                "mũi bị sổ",
                "chảy nước mũi",
                "mũi chảy nước",
                "nước mũi chảy",
            ],
            "chảy nước mũi",
        ),

        (
            [
                "hắt hơi",
                "hắt xì",
                "hắt xì hơi",
                "hắt hơi liên tục",
            ],
            "hắt hơi",
        ),

        (
            [
                "ngứa mũi",
                "mũi bị ngứa",
                "mũi rất ngứa",
            ],
            "ngứa mũi",
        ),

        (
            [
                "chảy máu cam",
                "mũi chảy máu",
                "chảy máu ở mũi",
                "máu chảy từ mũi",
            ],
            "chảy máu cam",
        ),

        (
            [
                "mất khứu giác",
                "không ngửi được",
                "không ngửi thấy mùi",
                "ngửi không thấy",
            ],
            "mất khứu giác",
        ),

        (
            [
                "đau vùng trán",
                "trán đau",
                "đau ở trán",
            ],
            "đau vùng trán",
        ),

        (
            [
                "đau gò má",
                "gò má đau",
                "đau ở gò má",
            ],
            "đau gò má",
        ),

        (
            [
                "đau nhức mặt",
                "đau mặt",
                "mặt bị đau",
                "nhức mặt",
            ],
            "đau nhức mặt",
        ),

        # =================================================
        # HỌNG
        # =================================================

        (
            [
                "đau họng",
                "họng đau",
                "cổ họng đau",
                "đau cổ họng",
                "đau ở cổ họng",
                "cổ họng bị đau",
                "họng bị đau",
            ],
            "đau họng",
        ),

        (
            [
                "rát họng",
                "họng rát",
                "cổ họng rát",
                "cổ họng bị rát",
                "rát ở cổ họng",
            ],
            "rát họng",
        ),

        (
            [
                "khô họng",
                "họng khô",
                "cổ họng khô",
                "cổ họng bị khô",
            ],
            "khô họng",
        ),

        # =================================================
        # QUAN TRỌNG:
        # NUỐT NƯỚC BỌT BỊ ĐAU
        # =================================================

        (
            [
                "nuốt nước bọt đau",
                "nuốt nước bọt bị đau",
                "nuốt nước bọt thấy đau",
                "nuốt nước bọt hơi đau",
                "nuốt nước bọt đau họng",
                "nuốt nước bọt thấy rát",
                "nuốt nước bọt bị rát",
                "nuốt nước bọt hơi rát",
                "nuốt nước bọt khó chịu",
                "nuốt nước bọt thấy khó chịu",
                "nuốt nước bọt đau cổ",
                "nuốt nước bọt đau cổ họng",
                "nuốt nước bọt cũng đau",
                "nuốt nước bọt thì đau",
                "nuốt nước bọt nó đau",
                "nuốt nước bọt nó hơi đau",
            ],
            "đau khi nuốt",
        ),

        (
            [
                "nuốt đau",
                "nuốt bị đau",
                "nuốt thấy đau",
                "nuốt vào đau",
                "nuốt thức ăn đau",
                "ăn uống bị đau",
                "ăn uống thấy đau",
                "nuốt đồ ăn đau",
                "nuốt thức ăn thấy đau",
            ],
            "đau khi nuốt",
        ),

        (
            [
                "khó nuốt",
                "nuốt khó",
                "nuốt thức ăn khó",
                "nuốt đồ ăn khó",
                "cảm giác khó nuốt",
                "khó nuốt thức ăn",
            ],
            "khó nuốt",
        ),

        (
            [
                "nuốt vướng",
                "nuốt thấy vướng",
                "cảm giác vướng cổ",
                "cổ họng bị vướng",
                "vướng ở cổ họng",
                "cảm giác có gì trong cổ",
            ],
            "nuốt vướng",
        ),

        (
            [
                "khàn tiếng",
                "giọng bị khàn",
                "giọng khàn",
                "bị khàn giọng",
                "nói khàn",
                "giọng nói bị khàn",
            ],
            "khàn tiếng",
        ),

        (
            [
                "mất tiếng",
                "không nói được",
                "mất giọng",
                "không ra tiếng",
            ],
            "mất tiếng",
        ),

        (
            [
                "ho",
                "bị ho",
                "ho nhiều",
                "ho liên tục",
                "cứ ho",
            ],
            "ho",
        ),

        (
            [
                "ho khan",
                "bị ho khan",
                "ho không có đờm",
            ],
            "ho khan",
        ),

        (
            [
                "ho có đờm",
                "ho ra đờm",
                "có đờm",
                "đờm trong cổ",
            ],
            "ho có đờm",
        ),

        (
            [
                "hôi miệng",
                "miệng có mùi",
                "hơi thở có mùi",
            ],
            "hôi miệng",
        ),

        (
            [
                "nổi hạch cổ",
                "cổ nổi hạch",
                "có hạch ở cổ",
                "hạch ở cổ",
            ],
            "nổi hạch cổ",
        ),

        # =================================================
        # GENERAL
        # =================================================

        (
            [
                "sốt",
                "bị sốt",
                "đang sốt",
                "nóng sốt",
            ],
            "sốt",
        ),
    ]

    for keywords, symptom in patterns:
        if any(keyword in text for keyword in keywords):
            if symptom not in detected:
                detected.append(symptom)

    return detected


# =========================================================
# RULE-BASED CHATBOT
# =========================================================

def rule_based_reply(message):
    """
    Chatbot dự phòng khi Gemini không hoạt động.

    Kết hợp:
    1. Natural language detection
    2. SymptomKB trong database
    """

    text = normalize_text(message)

    # -----------------------------------------
    # Phát hiện cách nói tự nhiên
    # -----------------------------------------

    natural_symptoms = detect_natural_symptoms(text)

    # -----------------------------------------
    # Tìm trong database SymptomKB
    # -----------------------------------------

    kb = list(SymptomKB.objects.all())

    matched = []

    for row in kb:
        keyword = normalize_text(row.keyword)

        if keyword and keyword in text:
            matched.append(row)

    # -----------------------------------------
    # Xác định chuyên khoa từ triệu chứng tự nhiên
    # -----------------------------------------

    specialty_map = {
        # Tai
        "ù tai": "Tai",
        "giảm thính lực": "Tai",
        "đau tai": "Tai",
        "ngứa tai": "Tai",
        "đầy tai": "Tai",
        "chảy dịch tai": "Tai",
        "chảy mủ tai": "Tai",
        "chóng mặt": "Tai",

        # Mũi
        "nghẹt mũi": "Mũi",
        "chảy nước mũi": "Mũi",
        "hắt hơi": "Mũi",
        "ngứa mũi": "Mũi",
        "chảy máu cam": "Mũi",
        "mất khứu giác": "Mũi",
        "đau vùng trán": "Mũi",
        "đau gò má": "Mũi",
        "đau nhức mặt": "Mũi",

        # Họng
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

    detected_specialties = []

    for symptom in natural_symptoms:
        specialty = specialty_map.get(symptom)

        if specialty and specialty not in detected_specialties:
            detected_specialties.append(specialty)

    # -----------------------------------------
    # Lấy chuyên khoa từ database
    # -----------------------------------------

    for row in matched:
        if row.specialty not in detected_specialties:
            detected_specialties.append(row.specialty)

    # -----------------------------------------
    # Nếu không nhận ra
    # -----------------------------------------

    if not matched and not natural_symptoms:

        return {
            "reply": (
                "Cảm ơn bạn đã chia sẻ. Bạn có thể mô tả rõ hơn "
                "triệu chứng đang gặp phải ở tai, mũi hoặc họng không?\n\n"
                "Ví dụ: đau tai, ù tai, nghẹt mũi, chảy nước mũi, "
                "đau họng, nuốt đau, khàn tiếng..."
            ),
            "suggestions": [],
            "can_book": False,
        }

    # -----------------------------------------
    # Xác định mức độ khẩn cấp
    # -----------------------------------------

    urgency_rank = {
        "Cao": 3,
        "Trung bình": 2,
        "Thấp": 1,
    }

    top = None

    if matched:
        matched.sort(
            key=lambda r: urgency_rank.get(r.urgency, 0),
            reverse=True
        )
        top = matched[0]

    # -----------------------------------------
    # Tạo câu trả lời
    # -----------------------------------------

    symptom_text = ", ".join(natural_symptoms)

    if symptom_text:
        reply = (
            f"Mình hiểu bạn đang có triệu chứng: {symptom_text}."
        )
    else:
        reply = "Mình đã ghi nhận các triệu chứng bạn mô tả."

    # -----------------------------------------
    # Lấy lời khuyên từ database
    # -----------------------------------------

    if top:
        reply += f"\n\n{top.advice}"

    # -----------------------------------------
    # Chuyên khoa
    # -----------------------------------------

    if detected_specialties:

        reply += (
            "\n\n🏥 Nhóm khám phù hợp: "
            + ", ".join(detected_specialties)
            + "."
        )

    # -----------------------------------------
    # Cảnh báo
    # -----------------------------------------

    if top and top.urgency == "Cao":

        reply += (
            "\n\n⚠️ Triệu chứng này có thể cần được kiểm tra sớm. "
            "Nếu triệu chứng nặng hoặc diễn biến nhanh, "
            "bạn nên đến cơ sở y tế gần nhất."
        )

    # -----------------------------------------
    # Disclaimer
    # -----------------------------------------

    reply += (
        "\n\nLưu ý: Đây chỉ là tư vấn sơ bộ, "
        "không thay thế chẩn đoán trực tiếp của bác sĩ."
    )

    # -----------------------------------------
    # Mời đặt lịch
    # -----------------------------------------

    reply += "\n\nBạn có muốn đặt lịch khám không?"

    return {
        "reply": reply,
        "suggestions": detected_specialties,
        "can_book": bool(detected_specialties),
    }


# =========================================================
# GEMINI AI
# =========================================================

def gemini_reply(message, history):
    """
    Gọi Gemini để hiểu ngôn ngữ tự nhiên.

    Trả về:
        str
    hoặc:
        None nếu Gemini lỗi
    """

    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or getattr(settings, "GEMINI_API_KEY", "")
    )

    if not api_key:
        print(
            "[Gemini] Không tìm thấy GEMINI_API_KEY "
            "trong .env — dùng bộ luật tư vấn."
        )
        return None

    # -----------------------------------------
    # Xây dựng lịch sử hội thoại
    # -----------------------------------------

    contents = []

    for h in history or []:

        role = (
            "model"
            if h.get("role") == "assistant"
            else "user"
        )

        content = h.get("content", "")

        if content:
            contents.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": content
                        }
                    ],
                }
            )

    # Tin nhắn hiện tại
    contents.append(
        {
            "role": "user",
            "parts": [
                {
                    "text": message
                }
            ],
        }
    )

    # -----------------------------------------
    # Gọi Gemini
    # -----------------------------------------

    try:

        response = requests.post(
            GEMINI_URL,
            params={
                "key": api_key
            },
            json={
                "system_instruction": {
                    "parts": [
                        {
                            "text": SYSTEM_PROMPT
                        }
                    ]
                },

                "contents": contents,

                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 500,
                },
            },

            timeout=20,
        )

        # -------------------------------------
        # Kiểm tra HTTP
        # -------------------------------------

        if response.status_code != 200:

            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            print(
                f"[Gemini] HTTP {response.status_code}: "
                f"{str(error_data)[:1000]}"
            )

            return None

        # -------------------------------------
        # Parse JSON
        # -------------------------------------

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:

            print(
                "[Gemini] API không trả về candidates: "
                f"{str(data)[:1000]}"
            )

            return None

        # -------------------------------------
        # Lấy text
        # -------------------------------------

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        text_parts = []

        for part in parts:

            text = part.get("text", "")

            if text:
                text_parts.append(text)

        result = "\n".join(text_parts).strip()

        if not result:
            print(
                "[Gemini] Không lấy được nội dung trả lời."
            )
            return None

        return result

    # -----------------------------------------
    # Lỗi request
    # -----------------------------------------

    except requests.RequestException as e:

        print(
            f"[Gemini] Lỗi kết nối API: {e}"
        )

        return None

    # -----------------------------------------
    # Lỗi JSON
    # -----------------------------------------

    except json.JSONDecodeError as e:

        print(
            f"[Gemini] Lỗi JSON: {e}"
        )

        return None

    # -----------------------------------------
    # Lỗi khác
    # -----------------------------------------

    except Exception as e:

        print(
            f"[Gemini] Lỗi không xác định: {e}"
        )

        return None