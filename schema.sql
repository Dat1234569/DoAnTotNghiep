-- ============================================================
-- SCHEMA CSDL: Hệ thống quản lý Phòng khám Chuyên khoa
-- Tai Mũi Họng An Tâm Đà Nẵng
-- Sinh tự động từ Django migrations (python manage.py migrate)
-- Dùng để tham khảo / import vào MySQL Workbench để vẽ ERD.
-- Lưu ý: không cần chạy tay file này để triển khai — chỉ cần
-- chạy "python manage.py migrate", Django sẽ tự tạo đầy đủ.
-- ============================================================

CREATE DATABASE IF NOT EXISTS clinic_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE clinic_db;

-- Tài khoản đăng nhập (Django User) — tương ứng lớp User trong biểu đồ lớp
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Hồ sơ vai trò (role) của tài khoản — tương ứng lớp Profile
CREATE TABLE `app_profile` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `app_profile_user_id_87d292a0_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Nhóm khám (Tai / Mũi / Họng) — tương ứng lớp Department
CREATE TABLE `app_department` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Hồ sơ bác sĩ — tương ứng lớp Doctor
CREATE TABLE `app_doctor` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `work_days` varchar(50) NOT NULL,
  `work_hours` varchar(50) NOT NULL,
  `avatar_color` varchar(10) NOT NULL,
  `department_id` bigint(20) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `app_doctor_department_id_60816b61_fk_app_department_id` (`department_id`),
  CONSTRAINT `app_doctor_department_id_60816b61_fk_app_department_id` FOREIGN KEY (`department_id`) REFERENCES `app_department` (`id`),
  CONSTRAINT `app_doctor_user_id_fbf54f12_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Hồ sơ bệnh nhân (kèm hồ sơ bệnh án) — tương ứng lớp Patient
CREATE TABLE `app_patient` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `dob` date DEFAULT NULL,
  `gender` varchar(10) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address` varchar(255) NOT NULL,
  `email` varchar(254) NOT NULL,
  `allergies` longtext NOT NULL,
  `medical_history` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `app_patient_user_id_a1a06dec_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Lịch khám — tương ứng lớp Appointment
CREATE TABLE `app_appointment` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `appt_date` date NOT NULL,
  `appt_time` time(6) NOT NULL,
  `status` varchar(30) NOT NULL,
  `symptom_note` longtext NOT NULL,
  `exam_result` longtext NOT NULL,
  `diagnosis` longtext NOT NULL,
  `treatment` longtext NOT NULL,
  `doctor_note` longtext NOT NULL,
  `source` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `department_id` bigint(20) DEFAULT NULL,
  `doctor_id` bigint(20) DEFAULT NULL,
  `patient_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `app_appointment_department_id_550572d0_fk_app_department_id` (`department_id`),
  KEY `app_appointment_doctor_id_cdf11c64_fk_app_doctor_id` (`doctor_id`),
  KEY `app_appointment_patient_id_c300735e_fk_app_patient_id` (`patient_id`),
  CONSTRAINT `app_appointment_department_id_550572d0_fk_app_department_id` FOREIGN KEY (`department_id`) REFERENCES `app_department` (`id`),
  CONSTRAINT `app_appointment_doctor_id_cdf11c64_fk_app_doctor_id` FOREIGN KEY (`doctor_id`) REFERENCES `app_doctor` (`id`),
  CONSTRAINT `app_appointment_patient_id_c300735e_fk_app_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `app_patient` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Đơn thuốc — tương ứng lớp Prescription
CREATE TABLE `app_prescription` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `diagnosis` varchar(255) NOT NULL,
  `medicines` longtext NOT NULL,
  `note` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `appointment_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `app_prescription_appointment_id_cf5b5481_fk_app_appointment_id` (`appointment_id`),
  CONSTRAINT `app_prescription_appointment_id_cf5b5481_fk_app_appointment_id` FOREIGN KEY (`appointment_id`) REFERENCES `app_appointment` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Kho thuốc — tương ứng lớp Medicine
CREATE TABLE `app_medicine` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `category` varchar(100) NOT NULL,
  `quantity` int(11) NOT NULL,
  `unit` varchar(30) NOT NULL,
  `price` int(11) NOT NULL,
  `manufacturer` varchar(150) NOT NULL,
  `expiry_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Dịch vụ & bảng giá — tương ứng lớp Service
CREATE TABLE `app_service` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `price` int(11) NOT NULL,
  `description` longtext NOT NULL,
  `department_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `app_service_department_id_77831f57_fk_app_department_id` (`department_id`),
  CONSTRAINT `app_service_department_id_77831f57_fk_app_department_id` FOREIGN KEY (`department_id`) REFERENCES `app_department` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Hóa đơn (liên kết Service tùy chọn) — tương ứng lớp Invoice
CREATE TABLE `app_invoice` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `amount` int(11) NOT NULL,
  `status` varchar(30) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `appointment_id` bigint(20) NOT NULL,
  `service_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `app_invoice_appointment_id_4a1a751b_fk_app_appointment_id` (`appointment_id`),
  KEY `app_invoice_service_id_bc303c02_fk_app_service_id` (`service_id`),
  CONSTRAINT `app_invoice_appointment_id_4a1a751b_fk_app_appointment_id` FOREIGN KEY (`appointment_id`) REFERENCES `app_appointment` (`id`),
  CONSTRAINT `app_invoice_service_id_bc303c02_fk_app_service_id` FOREIGN KEY (`service_id`) REFERENCES `app_service` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Cơ sở tri thức triệu chứng cho Chatbot AI — tương ứng lớp SymptomKB
CREATE TABLE `chatbot_symptomkb` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `keyword` varchar(100) NOT NULL,
  `specialty` varchar(100) NOT NULL,
  `advice` longtext NOT NULL,
  `urgency` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Nhật ký hội thoại Chatbot AI — tương ứng lớp ChatLog
CREATE TABLE `chatbot_chatlog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(100) NOT NULL,
  `sender` varchar(10) NOT NULL,
  `message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `chatbot_chatlog_user_id_eee98da8_fk_auth_user_id` (`user_id`),
  CONSTRAINT `chatbot_chatlog_user_id_eee98da8_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- Ngoài các bảng nghiệp vụ trên, Django còn tự tạo thêm các bảng
-- nội bộ phục vụ framework (không thuộc biểu đồ lớp của đề tài):
--   django_migrations, django_session, django_admin_log,
--   django_content_type, auth_permission, auth_group,
--   auth_group_permissions, auth_user_groups, auth_user_user_permissions
-- ------------------------------------------------------------
