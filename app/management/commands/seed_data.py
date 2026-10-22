from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Profile, Department, Doctor, Patient, Appointment, Medicine, Service
from chatbot.models import SymptomKB


class Command(BaseCommand):
    help = "Khởi tạo dữ liệu mẫu cho Phòng khám Chuyên khoa Tai Mũi Họng An Tâm Đà Nẵng"

    def handle(self, *args, **options):
        if Department.objects.exists():
            self.stdout.write(self.style.WARNING("Dữ liệu mẫu đã tồn tại — bỏ qua."))
            return

        # ---- Nhóm khám: Tai / Mũi / Họng ----
        dep_tai = Department.objects.create(name="Tai", description="Khám và điều trị các bệnh lý về tai")
        dep_mui = Department.objects.create(name="Mũi", description="Khám và điều trị các bệnh lý về mũi, xoang")
        dep_hong = Department.objects.create(name="Họng", description="Khám và điều trị các bệnh lý về họng, thanh quản")

        # ---- Tài khoản Lễ tân ----
        reception_user = User.objects.create_user(username="letan", password="letan123", first_name="Nguyễn Thị Lễ Tân")
        Profile.objects.create(user=reception_user, role="reception", phone="0900000002")

        # ---- Bác sĩ (kèm tài khoản đăng nhập) ----
        doctors_data = [
            {"username": "bs.hoa", "full_name": "BS. Trần Minh Hòa", "dep": dep_tai, "phone": "0901234561", "work_days": "T2,T3,T4,T5,T6", "work_hours": "08:00 - 17:00", "color": "#2451B0"},
            {"username": "bs.lan", "full_name": "BS. Nguyễn Thị Lan", "dep": dep_mui, "phone": "0901234562", "work_days": "T2,T4,T6", "work_hours": "08:00 - 16:00", "color": "#C8891A"},
            {"username": "bs.duc", "full_name": "BS. Lê Văn Đức", "dep": dep_hong, "phone": "0901234563", "work_days": "T3,T5,T7", "work_hours": "09:00 - 17:00", "color": "#5232A8"},
        ]
        for d in doctors_data:
            user = User.objects.create_user(username=d["username"], password="bacsi123", first_name=d["full_name"])
            Profile.objects.create(user=user, role="doctor", phone=d["phone"])
            Doctor.objects.create(
                user=user, full_name=d["full_name"], department=d["dep"], phone=d["phone"],
                email=f"{d['username']}@clinic.vn", work_days=d["work_days"], work_hours=d["work_hours"], avatar_color=d["color"],
            )

        # ---- Bệnh nhân mẫu (kèm tài khoản) ----
        p1_user = User.objects.create_user(username="benhnhan1", password="123456", first_name="Nguyễn Văn An")
        Profile.objects.create(user=p1_user, role="patient", phone="0912345671")
        p1 = Patient.objects.create(user=p1_user, full_name="Nguyễn Văn An", gender="Nam", phone="0912345671", address="Quận Hải Châu, Đà Nẵng")

        p2_user = User.objects.create_user(username="benhnhan2", password="123456", first_name="Trần Thị Bích")
        Profile.objects.create(user=p2_user, role="patient", phone="0912345672")
        p2 = Patient.objects.create(user=p2_user, full_name="Trần Thị Bích", gender="Nữ", phone="0912345672", address="Quận Thanh Khê, Đà Nẵng")

        # ---- Lịch khám mẫu ----
        today = timezone.localdate()
        Appointment.objects.create(patient=p1, doctor=Doctor.objects.get(user=User.objects.get(username="bs.hoa")), department=dep_tai,
                                    appt_date=today, appt_time="09:00", status="Đã xác nhận", symptom_note="Đau tai, ù tai", source="Lễ tân")
        Appointment.objects.create(patient=p2, doctor=Doctor.objects.get(user=User.objects.get(username="bs.duc")), department=dep_hong,
                                    appt_date=today, appt_time="10:30", status="Chờ xác nhận", symptom_note="Đau họng, khàn tiếng", source="Chatbot AI")

        # ---- Cơ sở tri thức chatbot (chuyên khoa Tai Mũi Họng) ----
        # ---- Cơ sở tri thức chatbot (specialty phải trùng tên khoa ở trên) ----
        kb = [
            # ---------------- TAI ----------------
            ("đau tai", "Tai", "Đau tai có thể do viêm tai giữa, viêm tai ngoài hoặc ráy tai. Tránh ngoáy tai, giữ tai khô ráo. Nếu đau kéo dài hoặc chảy dịch, nên khám sớm.", "Trung bình"),
            ("ù tai", "Tai", "Ù tai có thể do áp lực, viêm nhiễm hoặc tiếp xúc tiếng ồn lớn. Nên nghỉ ngơi, tránh tiếng ồn; nếu kéo dài trên 2 ngày nên khám.", "Thấp"),
            ("chảy dịch tai", "Tai", "Chảy dịch tai là dấu hiệu viêm nhiễm cần được khám và điều trị sớm để tránh biến chứng.", "Trung bình"),
            ("chảy mủ tai", "Tai", "Chảy mủ tai thường là dấu hiệu viêm tai giữa có biến chứng, cần khám sớm để điều trị đúng cách.", "Trung bình"),
            ("chảy máu tai", "Tai", "Chảy máu tai cần được thăm khám sớm để xác định nguyên nhân, tránh trường hợp tổn thương màng nhĩ.", "Cao"),
            ("giảm thính lực", "Tai", "Giảm thính lực đột ngột cần được thăm khám sớm, không nên trì hoãn.", "Cao"),
            ("nghe kém", "Tai", "Nghe kém có thể do ráy tai, viêm tai hoặc các vấn đề về thính giác. Nên khám để xác định nguyên nhân cụ thể.", "Trung bình"),
            ("điếc", "Tai", "Mất thính lực đột ngột (điếc đột ngột) là tình trạng cần khám cấp cứu trong 24-48 giờ đầu để có cơ hội điều trị tốt nhất.", "Cao"),
            ("ngứa tai", "Tai", "Ngứa tai có thể do viêm da ống tai hoặc nấm tai. Tránh ngoáy tai bằng vật cứng, nên khám nếu ngứa kéo dài.", "Thấp"),
            ("đầy tai", "Tai", "Cảm giác đầy tai, bít tai có thể do ráy tai, viêm tai hoặc rối loạn vòi nhĩ. Nên khám để được lấy ráy tai hoặc điều trị phù hợp.", "Thấp"),
            ("bít tai", "Tai", "Cảm giác bít tai, đầy tai có thể do ráy tai hoặc dịch ứ trong tai giữa. Nên khám để kiểm tra cụ thể.", "Thấp"),
            ("ráy tai", "Tai", "Ráy tai nhiều gây bít tắc có thể tự cải thiện hoặc cần lấy ráy tai tại phòng khám, không nên tự ngoáy sâu.", "Thấp"),
            ("viêm tai giữa", "Tai", "Viêm tai giữa thường gặp ở trẻ em, gây đau tai và có thể sốt. Cần khám để điều trị kháng sinh đúng phác đồ nếu cần.", "Trung bình"),
            ("viêm tai ngoài", "Tai", "Viêm tai ngoài gây đau khi chạm vào vành tai, thường do nước đọng hoặc vi khuẩn. Nên khám để điều trị đúng thuốc.", "Trung bình"),
            ("dị vật trong tai", "Tai", "Dị vật hoặc côn trùng chui vào tai cần được bác sĩ lấy ra an toàn, không nên tự lấy tại nhà để tránh tổn thương.", "Cao"),
            ("côn trùng chui vào tai", "Tai", "Côn trùng chui vào tai cần đến khám ngay để được lấy ra an toàn, tránh tự ý xử lý gây tổn thương màng nhĩ.", "Cao"),
            ("chóng mặt", "Tai", "Chóng mặt có thể liên quan đến rối loạn tiền đình ở tai trong. Nên nghỉ ngơi, tránh thay đổi tư thế đột ngột và khám nếu tái diễn.", "Trung bình"),
            ("đau sau tai", "Tai", "Đau hoặc sưng vùng sau tai có thể liên quan viêm tai xương chũm, cần khám sớm để tránh biến chứng.", "Trung bình"),

            # ---------------- MŨI ----------------
            ("nghẹt mũi", "Mũi", "Nghẹt mũi thường do cảm cúm hoặc viêm mũi dị ứng. Xông hơi, giữ ấm; nếu kéo dài trên 1 tuần nên khám.", "Thấp"),
            ("sổ mũi", "Mũi", "Sổ mũi thường gặp khi cảm cúm hoặc viêm mũi dị ứng. Uống nhiều nước, giữ ấm; nếu kéo dài nên khám.", "Thấp"),
            ("chảy nước mũi", "Mũi", "Chảy nước mũi kéo dài, đặc biệt nếu đổi màu (vàng, xanh), có thể là dấu hiệu viêm xoang cần khám.", "Thấp"),
            ("hắt hơi", "Mũi", "Hắt hơi liên tục kèm ngứa mũi thường gặp trong viêm mũi dị ứng. Nên hạn chế tiếp xúc tác nhân dị ứng và khám nếu ảnh hưởng sinh hoạt.", "Thấp"),
            ("ngứa mũi", "Mũi", "Ngứa mũi thường liên quan dị ứng. Tránh tiếp xúc bụi, phấn hoa; nên khám nếu triệu chứng kéo dài hoặc nặng.", "Thấp"),
            ("viêm xoang", "Mũi", "Viêm xoang gây đau nhức vùng mặt, nghẹt mũi kéo dài. Nên khám để được điều trị đúng phác đồ, tránh biến chứng.", "Trung bình"),
            ("chảy máu cam", "Mũi", "Chảy máu cam thường không nguy hiểm, nên cúi đầu về trước và bóp nhẹ cánh mũi. Nếu chảy nhiều hoặc tái phát thường xuyên nên khám.", "Trung bình"),
            ("mất khứu giác", "Mũi", "Mất khứu giác có thể liên quan viêm mũi xoang hoặc bệnh lý khác, nên được thăm khám để xác định nguyên nhân.", "Trung bình"),
            ("đau nhức mặt", "Mũi", "Đau nhức vùng mặt, đặc biệt quanh mắt và trán, có thể là dấu hiệu viêm xoang. Nên khám để chẩn đoán chính xác.", "Trung bình"),
            ("đau vùng trán", "Mũi", "Đau vùng trán kèm nghẹt mũi có thể liên quan viêm xoang trán, nên khám nếu kéo dài.", "Trung bình"),
            ("đau gò má", "Mũi", "Đau vùng gò má kèm nghẹt mũi có thể liên quan viêm xoang hàm, nên khám để điều trị phù hợp.", "Trung bình"),
            ("polyp mũi", "Mũi", "Polyp mũi gây nghẹt mũi kéo dài, giảm khứu giác. Cần khám chuyên khoa để có hướng điều trị hoặc can thiệp phù hợp.", "Trung bình"),
            ("lệch vách ngăn", "Mũi", "Lệch vách ngăn mũi có thể gây nghẹt mũi một bên kéo dài. Nên khám để được tư vấn hướng xử lý phù hợp.", "Thấp"),
            ("khô mũi", "Mũi", "Khô mũi có thể do thời tiết hoặc viêm mũi mạn tính. Có thể dùng nước muối sinh lý; nên khám nếu khó chịu kéo dài.", "Thấp"),
            ("ngủ ngáy", "Mũi", "Ngủ ngáy có thể liên quan nghẹt mũi, lệch vách ngăn hoặc phì đại amidan. Nên khám để xác định nguyên nhân và hướng xử lý.", "Thấp"),
            ("viêm mũi dị ứng", "Mũi", "Viêm mũi dị ứng gây hắt hơi, ngứa mũi, chảy nước mũi tái diễn. Nên hạn chế tác nhân dị ứng và khám để được điều trị phù hợp.", "Thấp"),
            ("nghẹt một bên mũi", "Mũi", "Nghẹt mũi một bên kéo dài có thể liên quan lệch vách ngăn hoặc polyp mũi, nên khám để xác định nguyên nhân.", "Trung bình"),

            # ---------------- HỌNG ----------------
            ("đau họng", "Họng", "Đau họng có thể do viêm họng hoặc viêm amidan. Súc miệng nước muối ấm, hạn chế nói to. Nếu kèm sốt cao nên khám sớm.", "Thấp"),
            ("rát họng", "Họng", "Rát họng thường gặp khi viêm họng hoặc trào ngược. Uống nước ấm, tránh đồ cay nóng; nên khám nếu kéo dài.", "Thấp"),
            ("ho", "Họng", "Ho kéo dài có thể liên quan viêm họng, viêm thanh quản. Giữ ấm cổ, tránh khói bụi; nên khám nếu ho quá 1 tuần.", "Thấp"),
            ("ho khan", "Họng", "Ho khan kéo dài có thể do viêm họng hoặc kích ứng đường hô hấp trên. Nên khám nếu không cải thiện sau vài ngày.", "Thấp"),
            ("ho có đờm", "Họng", "Ho có đờm có thể liên quan viêm họng hoặc viêm đường hô hấp. Nên khám để xác định nguyên nhân và điều trị phù hợp.", "Trung bình"),
            ("viêm họng", "Họng", "Viêm họng gây đau rát, khó chịu khi nuốt. Súc miệng nước muối, nghỉ ngơi; nên khám nếu kèm sốt cao hoặc kéo dài.", "Thấp"),
            ("viêm amidan", "Họng", "Viêm amidan gây đau họng, sốt, khó nuốt. Cần khám để được điều trị đúng phác đồ, đặc biệt nếu tái phát nhiều lần.", "Trung bình"),
            ("sưng amidan", "Họng", "Amidan sưng to có thể gây khó nuốt, khó thở khi ngủ. Nên khám để đánh giá mức độ và hướng điều trị.", "Trung bình"),
            ("khàn tiếng", "Họng", "Khàn tiếng kéo dài có thể do viêm thanh quản hoặc dùng giọng quá mức. Nên hạn chế nói to, giữ ấm cổ họng và khám nếu không cải thiện sau vài ngày.", "Thấp"),
            ("mất tiếng", "Họng", "Mất tiếng đột ngột thường do viêm thanh quản cấp. Nên hạn chế nói, giữ ấm cổ và khám nếu không cải thiện sau 3-5 ngày.", "Trung bình"),
            ("nuốt vướng", "Họng", "Cảm giác nuốt vướng có thể liên quan viêm họng hoặc amidan. Nên khám để được chẩn đoán chính xác.", "Trung bình"),
            ("khó nuốt", "Họng", "Khó nuốt có thể liên quan viêm họng, viêm amidan hoặc các vấn đề khác vùng hầu họng. Nên khám sớm để xác định nguyên nhân.", "Trung bình"),
            ("đau khi nuốt", "Họng", "Đau khi nuốt thường gặp trong viêm họng, viêm amidan. Nên khám nếu đau nhiều hoặc kèm sốt.", "Trung bình"),
            ("hôi miệng", "Họng", "Hôi miệng có thể liên quan viêm amidan hốc mủ hoặc các vấn đề răng miệng. Nên khám Tai Mũi Họng để loại trừ nguyên nhân từ amidan.", "Thấp"),
            ("nổi hạch cổ", "Họng", "Nổi hạch vùng cổ có thể là phản ứng viêm họng hoặc amidan. Nên khám nếu hạch to, đau hoặc không giảm sau vài ngày.", "Trung bình"),
            ("vướng cổ họng", "Họng", "Cảm giác vướng ở cổ họng có thể liên quan viêm họng mạn hoặc trào ngược. Nên khám để xác định nguyên nhân cụ thể.", "Thấp"),
            ("khô họng", "Họng", "Khô họng có thể do thở bằng miệng, viêm họng mạn hoặc thời tiết hanh khô. Nên uống đủ nước và khám nếu kéo dài.", "Thấp"),
            ("ngưng thở khi ngủ", "Họng", "Ngưng thở khi ngủ có thể liên quan phì đại amidan hoặc VA. Nên khám để được đánh giá và tư vấn hướng xử lý.", "Trung bình"),
            ("khó thở", "Họng", "Khó thở kèm đau họng có thể là dấu hiệu nghiêm trọng (viêm thanh thiệt, dị vật đường thở). Nên đến cấp cứu ngay nếu khó thở tăng nhanh.", "Cao"),

            # ---------------- TRIỆU CHỨNG CHUNG LIÊN QUAN TMH ----------------
            ("sốt", "Họng", "Sốt kèm theo triệu chứng ở tai, mũi hoặc họng thường là dấu hiệu viêm nhiễm. Nên theo dõi nhiệt độ, nghỉ ngơi và mô tả thêm triệu chứng cụ thể (đau tai, nghẹt mũi hay đau họng) để được tư vấn chính xác hơn.", "Trung bình"),
            ("trẻ em", "Họng", "Trẻ nhỏ có triệu chứng bất thường ở tai, mũi, họng (quấy khóc, bỏ ăn, sốt) nên được đưa đi khám sớm để theo dõi phù hợp.", "Trung bình"),
        ]
        for keyword, specialty, advice, urgency in kb:
            SymptomKB.objects.create(keyword=keyword, specialty=specialty, advice=advice, urgency=urgency)

        # ---- Kho thuốc mẫu ----
        medicines = [
            {"name": "Amoxicillin 500mg", "category": "Kháng sinh", "quantity": 300, "unit": "viên", "price": 2000, "manufacturer": "Domesco", "expiry_date": "2027-06-30"},
            {"name": "Paracetamol 500mg", "category": "Giảm đau, hạ sốt", "quantity": 500, "unit": "viên", "price": 1000, "manufacturer": "Traphaco", "expiry_date": "2027-12-31"},
            {"name": "Cetirizine 10mg", "category": "Kháng histamin", "quantity": 200, "unit": "viên", "price": 1500, "manufacturer": "Stella", "expiry_date": "2027-03-31"},
            {"name": "Xịt mũi Natri Clorid 0.9%", "category": "Xịt/rửa mũi", "quantity": 120, "unit": "chai", "price": 25000, "manufacturer": "Fysoline", "expiry_date": "2026-12-31"},
            {"name": "Viên ngậm ho Bảo Thanh", "category": "Trị ho", "quantity": 150, "unit": "hộp", "price": 30000, "manufacturer": "Bảo Thanh", "expiry_date": "2027-01-31"},
            {"name": "Alpha Choay", "category": "Kháng viêm", "quantity": 250, "unit": "viên", "price": 1200, "manufacturer": "Mekophar", "expiry_date": "2027-05-31"},
        ]
        for m in medicines:
            Medicine.objects.create(**m)

        # ---- Dịch vụ & bảng giá mẫu ----
        services = [
            {"name": "Khám Tai tổng quát", "dep": dep_tai, "price": 150000, "description": "Khám và tư vấn các bệnh lý về tai"},
            {"name": "Nội soi Tai", "dep": dep_tai, "price": 250000, "description": "Nội soi chẩn đoán bệnh lý tai"},
            {"name": "Khám Mũi tổng quát", "dep": dep_mui, "price": 150000, "description": "Khám và tư vấn các bệnh lý về mũi, xoang"},
            {"name": "Nội soi Mũi", "dep": dep_mui, "price": 250000, "description": "Nội soi chẩn đoán bệnh lý mũi xoang"},
            {"name": "Khám Họng tổng quát", "dep": dep_hong, "price": 150000, "description": "Khám và tư vấn các bệnh lý về họng, thanh quản"},
            {"name": "Nội soi Họng - Thanh quản", "dep": dep_hong, "price": 250000, "description": "Nội soi chẩn đoán bệnh lý họng, thanh quản"},
        ]
        for s in services:
            Service.objects.create(name=s["name"], department=s["dep"], price=s["price"], description=s["description"])

        self.stdout.write(self.style.SUCCESS("✔ Đã tạo dữ liệu mẫu cho Phòng khám TMH An Tâm Đà Nẵng."))
        self.stdout.write("   🧑‍💼 Lễ tân   — letan / letan123")
        self.stdout.write("   ⚕️  Bác sĩ    — bs.hoa / bacsi123 (và bs.lan, bs.duc — cùng mật khẩu)")
        self.stdout.write("   🧑 Bệnh nhân — benhnhan1 / 123456 (và benhnhan2)")
        self.stdout.write("   👑 Admin     — tạo bằng: python manage.py createsuperuser")