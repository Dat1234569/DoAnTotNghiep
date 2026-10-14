# Hệ thống quản lý Phòng khám Chuyên khoa Tai Mũi Họng An Tâm Đà Nẵng

Đồ án tốt nghiệp — xây dựng bằng **Django (Python)** + **MySQL**, theo đúng cấu trúc `app/` + `chatbot/` giống dự án thực tập tham khảo.

> 📄 **Tài liệu phân tích thiết kế đi kèm** (`PhanTich_UseCase_LuongHoatDong.docx`): danh sách tác nhân, use case, đặc tả use case, sơ đồ use case, sơ đồ hoạt động, sơ đồ tuần tự, biểu đồ lớp — **khớp 100%** với code trong repo này (tên lớp, tên hàm, tên bảng đều giống hệt). Dùng tài liệu đó làm cơ sở khi báo cáo, và dùng code này khi demo/chạy thật.

## 1. Công nghệ sử dụng
- **Backend & Frontend:** Django 5.1 (Python) — MVT, giao diện render bằng Django Template
- **Database:** MySQL 8 (qua PyMySQL)
- **Chatbot AI:** Google **Gemini API** (tùy chọn) + bộ luật tư vấn dự phòng
- **Triển khai:** Docker + docker-compose, Gunicorn + WhiteNoise (phục vụ static file khi chạy production)
- **Phân quyền:** 4 vai trò — Admin, Lễ tân, Bác sĩ, Bệnh nhân

## 2. Cấu trúc thư mục
```
clinic-django/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── schema.sql                # Schema CSDL tham khảo — import vào MySQL Workbench để vẽ ERD
├── .env.example
├── phongkham/                 # cấu hình project (settings, urls)
├── app/                        # app chính: quản lý phòng khám
│   ├── models.py                # Profile, Department, Doctor, Patient, Appointment, Prescription, Invoice
│   ├── views.py
│   ├── forms.py
│   ├── decorators.py            # phân quyền theo vai trò
│   ├── management/commands/seed_data.py
│   └── templates/app/
├── chatbot/                    # app chatbot AI
│   ├── models.py                 # SymptomKB, ChatLog
│   ├── views.py                   # API tư vấn + đặt lịch
│   └── utils.py                   # bộ luật tư vấn + tích hợp Gemini
└── static/css/style.css
```

---

## 3. Cách chạy — LOCAL (không Docker)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# hoặc: source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Copy `.env.example` → `.env`, điền `DB_PASSWORD` theo MySQL Workbench/XAMPP của bạn.

```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Mở **http://localhost:8000**

---

## 4. Cách chạy — DOCKER (khuyên dùng khi deploy)

Yêu cầu đã cài [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

Lệnh này tự động:
1. Khởi tạo container MySQL 8 riêng (dữ liệu lưu bền trong volume `mysql_data`)
2. Build & chạy Django bằng Gunicorn, tự `migrate` khi container khởi động
3. Mở cổng **8000**

Sau khi container chạy, tạo dữ liệu mẫu + admin (chạy trong container `web`):
```bash
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py createsuperuser
```

Mở **http://localhost:8000**

Muốn đổi mật khẩu DB/SECRET_KEY khi deploy thật: tạo file `.env` cùng cấp `docker-compose.yml` với các biến `DB_PASSWORD`, `SECRET_KEY`, `ALLOWED_HOSTS`, `GEMINI_API_KEY` — compose sẽ tự đọc.

---

## 5. CSDL — MySQL Workbench

Không cần chạy tay `schema.sql` để ứng dụng hoạt động (bước `migrate` ở trên đã tự tạo đầy đủ). File `schema.sql` chỉ để:
- Import vào **MySQL Workbench** → **Database → Reverse Engineer** để vẽ ERD trực quan cho báo cáo
- Đối chiếu với **biểu đồ lớp** trong file Word — mỗi bảng đều có comment ghi rõ tương ứng lớp nào

| Bảng | Lớp trong biểu đồ lớp |
|---|---|
| `auth_user` | User |
| `app_profile` | Profile |
| `app_department` | Department |
| `app_doctor` | Doctor |
| `app_patient` | Patient |
| `app_appointment` | Appointment |
| `app_prescription` | Prescription |
| `app_invoice` | Invoice |
| `chatbot_symptomkb` | SymptomKB |
| `chatbot_chatlog` | ChatLog |

---

## 6. Tài khoản đăng nhập
| Vai trò | Tên đăng nhập | Mật khẩu | Cách tạo |
|---|---|---|---|
| 👑 Admin | (do bạn đặt) | (do bạn đặt) | `python manage.py createsuperuser` |
| 🧑‍💼 Lễ tân | `letan` | `letan123` | Có sẵn từ `seed_data` |
| ⚕️ Bác sĩ | `bs.hoa`, `bs.lan`, `bs.duc` | `bacsi123` | Có sẵn từ `seed_data` |
| 🧑 Bệnh nhân | `benhnhan1`, `benhnhan2` | `123456` | Có sẵn, hoặc tự đăng ký |

## 7. Cấu trúc "Nhóm khám"
Vì là phòng khám **chuyên khoa** (không đa khoa), hệ thống chia 3 nhóm khám: **Tai / Mũi / Họng** — quản lý ở trang "Khoa khám" (bảng kỹ thuật vẫn tên `Department`).

## 7b. Các module đã có
- **Trang giới thiệu công khai** (`/`) — không cần đăng nhập: giới thiệu phòng khám, đội ngũ bác sĩ theo từng nhóm khám, hotline/địa chỉ/giờ làm việc
- **Bệnh nhân tự phục vụ** (`/patient/`): xem & sửa hồ sơ cá nhân, đặt lịch khám trực tiếp (chọn nhóm khám, ngày giờ), xem lịch khám, xem đơn thuốc, xem hóa đơn — **chatbot AI chỉ là tính năng hỗ trợ thêm** (nút nổi góc màn hình)
- **Kho thuốc**: Admin quản lý danh mục thuốc (tên, loại, tồn kho, đơn vị, giá, NSX, hạn dùng). Khi bác sĩ kê đơn, chọn thuốc từ kho — hệ thống **tự động trừ tồn kho**
- **Dịch vụ & Bảng giá**: Admin quản lý danh mục dịch vụ khám theo từng nhóm khám kèm giá; khi lễ tân tạo hóa đơn có thể chọn dịch vụ để tự điền giá
- **Báo cáo thống kê**: biểu đồ lượt khám theo tháng, doanh thu theo tháng, tỷ lệ khám theo nhóm khám (dùng Chart.js)

## 8. Chatbot AI — Gemini
Mặc định dùng bộ luật đối chiếu từ khóa triệu chứng TMH (không cần key). Muốn bật Gemini thật: lấy key tại https://aistudio.google.com/apikey, điền `GEMINI_API_KEY` vào `.env`.

Lưu ý: Gemini không tự tìm kiếm internet khi trả lời — dựa vào kiến thức huấn luyện sẵn, đủ dùng cho tư vấn sức khỏe phổ thông.

## 9. Phân quyền
| Chức năng | Admin | Lễ tân | Bác sĩ | Bệnh nhân |
|---|:---:|:---:|:---:|:---:|
| Trang giới thiệu công khai | ✅ | ✅ | ✅ | ✅ (không cần đăng nhập) |
| Tổng quan | ✅ | ✅ | ✅ (số liệu của mình) | ❌ |
| Khoa khám | ✅ | 👁 | 👁 | ❌ |
| Bác sĩ (+ tài khoản) | ✅ | 👁 | 👁 | ❌ |
| Bệnh nhân / hồ sơ bệnh án | ✅ | ✅ | ✅ Sửa hồ sơ | ✅ (chỉ hồ sơ của mình) |
| Lịch khám | ✅ | ✅ | ✅ (lịch của mình) | ✅ (đặt/xem lịch của mình) |
| Đơn thuốc | ✅ | 👁 | ✅ Tạo đơn | 👁 (chỉ đơn của mình) |
| Kho thuốc | ✅ | ❌ | 👁 | ❌ |
| Dịch vụ & Bảng giá | ✅ | 👁 | ❌ | ❌ |
| Hóa đơn | ✅ | ✅ | ❌ | 👁 (chỉ hóa đơn của mình) |
| Báo cáo thống kê | ✅ | ❌ | ❌ | ❌ |
| Tài khoản nhân viên | ✅ | ❌ | ❌ | ❌ |
| Chat AI tư vấn + đặt lịch nhanh | ❌ | ❌ | ❌ | ✅ (nút chat nổi — hỗ trợ thêm) |

---

## 10. Đẩy lên GitHub

```bash
git init
git add .
git commit -m "Initial commit: Hệ thống quản lý phòng khám TMH An Tâm Đà Nẵng"
git branch -M main
git remote add origin https://github.com/<ten-tai-khoan>/<ten-repo>.git
git push -u origin main
```

`.gitignore` đã loại trừ sẵn `venv/`, `.env`, `__pycache__/`, `staticfiles/` — **không** commit nhầm mật khẩu hay file rác.

## 11. Deploy lên server riêng (VPS)

Gợi ý nhanh nếu server đã cài Docker:
```bash
git clone https://github.com/<ten-tai-khoan>/<ten-repo>.git
cd <ten-repo>
cp .env.example .env   # sửa lại SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS=domain-cua-ban
docker compose up -d --build
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py createsuperuser
```

Sau đó đặt **Nginx** làm reverse proxy trỏ về cổng 8000, và dùng **Certbot** để có HTTPS miễn phí — bước này tùy nhà cung cấp VPS (DigitalOcean, Vultr, AWS Lightsail...), có thể hỏi thêm khi bạn thuê server cụ thể.

## 12. Lưu ý cho báo cáo đồ án
- Mật khẩu được Django **băm (hash)** tự động.
- Chatbot chỉ tư vấn/chẩn đoán **sơ bộ**, không thay thế bác sĩ.
- Khi deploy thật: đặt `DEBUG=False`, `ALLOWED_HOSTS` đúng domain, `SECRET_KEY` ngẫu nhiên mạnh, bật HTTPS.

