# 🏥 Lifeline Care — Healthcare Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=for-the-badge&logo=mysql)
![Claude AI](https://img.shields.io/badge/Claude-AI-purple?style=for-the-badge)
![Razorpay](https://img.shields.io/badge/Razorpay-Payments-blue?style=for-the-badge)

A full-stack healthcare management platform built with Django, featuring AI-powered assistance, real-time notifications, and integrated payments.

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [User Roles](#user-roles)
- [Screenshots](#screenshots)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)

---

## 🌟 Overview

Lifeline Care is a complete healthcare management system that connects patients with doctors. It supports appointment booking, AI-powered health assistance, real-time notifications, document management, and secure payments — all in one platform.

---

## ✨ Features

### 👤 Patient
- 📅 Book, reschedule, and cancel appointments
- 🤖 AI health assistant (powered by Claude AI) with full conversation state machine
- 💳 Secure payments via Razorpay
- 📁 Access prescriptions, lab reports, and medical documents
- 🔔 Real-time notifications for appointments and payments
- 📊 Dashboard with health stats and history

### 🩺 Doctor
- 📋 Manage daily appointments and patient records
- 📁 Upload prescriptions and documents for patients
- ⏰ Set weekly availability schedules
- 💰 Track earnings and consultation history
- 🔔 Notifications for new bookings and cancellations

### 🛠️ Admin
- 📊 Platform-wide analytics dashboard
- ✅ Verify doctor registrations and licenses
- 👥 Manage patients and doctors
- 💳 Monitor all payments and transactions
- 🔔 System alerts and notifications

### 🤖 AI Chatbot
- Intent detection with 15+ supported intents
- Full conversation state machine (12 states)
- Book appointments directly via chat
- Symptom checker with specialist recommendations
- Appointment reschedule and cancellation via chat
- Fallback to Claude AI for general health questions

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 |
| Database | MySQL 8.0 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI | Anthropic Claude API (claude-haiku-4-5) |
| Payments | Razorpay |
| Static Files | WhiteNoise |
| Auth | Django Custom User Model |
| Notifications | Custom Django App with AJAX polling |

---

## 📁 Project Structure

```
lifeline_care/
├── accounts/           # Custom user model, login, signup, logout
├── patients/           # Patient dashboard, profile, documents
├── doctors/            # Doctor dashboard, profile, availability
├── appointments/       # Booking flow, slots, cancellation
├── payments/           # Razorpay integration, payment history
├── ai_assistant/       # Chatbot state machine, intent detection
│   ├── models.py       # ChatSession, ChatMessage
│   ├── views.py        # Chat API endpoints
│   ├── intent.py       # Regex-based intent detection
│   ├── actions.py      # DB query helpers
│   └── state_machine.py# Conversation state machine
├── notifications/      # Real-time notification system
├── admin_panel/        # Custom admin dashboard
├── templates/          # All HTML templates
│   ├── patients/       # 7 patient pages
│   ├── doctors/        # 5 doctor pages
│   ├── appointments/   # Booking flow pages
│   ├── admin_panel/    # Admin pages
│   └── notifications/  # Notification pages
├── static/
│   ├── css/            # All stylesheets
│   └── js/             # All JavaScript files
├── media/              # Uploaded files (gitignored)
├── lifeline_care/      # Django project settings
├── manage.py
├── requirements.txt
├── Procfile
└── .env                # Environment variables (gitignored)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lifeline-care.git
cd lifeline-care
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Database

```sql
CREATE DATABASE lifeline_care CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lifeline_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lifeline_care.* TO 'lifeline_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

DB_NAME=lifeline_care
DB_USER=lifeline_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

ANTHROPIC_API_KEY=your-anthropic-api-key
RAZORPAY_KEY_ID=rzp_test_your-key-id
RAZORPAY_KEY_SECRET=your-key-secret
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Admin)

```python
# Run in Django shell: python manage.py shell
from accounts.models import User
User.objects.create_superuser(
    username   = 'admin',
    email      = 'admin@lifelinecare.in',
    password   = 'Admin@1234',
    first_name = 'Super',
    last_name  = 'Admin',
    role       = 'admin'
)
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Run the Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` 🎉

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | Debug mode (`True`/`False`) | ✅ |
| `DB_NAME` | MySQL database name | ✅ |
| `DB_USER` | MySQL username | ✅ |
| `DB_PASSWORD` | MySQL password | ✅ |
| `DB_HOST` | MySQL host (default: `localhost`) | ✅ |
| `DB_PORT` | MySQL port (default: `3306`) | ✅ |
| `ANTHROPIC_API_KEY` | Claude AI API key | ✅ |
| `RAZORPAY_KEY_ID` | Razorpay key ID | ✅ |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | ✅ |

---

## 👥 User Roles

### Patient
- Register at `/accounts/auth/`
- Dashboard at `/patients/dashboard/`

### Doctor
- Register at `/accounts/auth/` (select Doctor role)
- Dashboard at `/doctors/dashboard/`
- Must be verified by admin before patients can book

### Admin
- Login at `/accounts/auth/`
- Dashboard at `/admin-panel/`
- Django admin at `/django-admin/`

---

## 🌐 API Endpoints

### Authentication
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/accounts/auth/` | Login / Signup page |
| POST | `/accounts/login/` | Login |
| POST | `/accounts/signup/` | Register |
| GET | `/accounts/logout/` | Logout |

### Appointments
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/appointments/book/<doctor_id>/` | Booking page |
| POST | `/appointments/confirm/` | Confirm & create Razorpay order |
| POST | `/appointments/payment/` | Verify payment & create appointment |
| GET | `/appointments/success/<appt_id>/` | Success page |
| POST | `/appointments/cancel/<appt_id>/` | Cancel appointment |
| GET | `/appointments/slots/` | AJAX: Get available slots |

### AI Assistant
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/ai/chat/` | Chat page |
| POST | `/ai/message/` | Send message (AJAX) |
| GET | `/ai/history/` | Get chat history |
| POST | `/ai/clear/` | Clear chat session |

### Notifications
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/notifications/` | All notifications |
| GET | `/notifications/unread/` | Unread count + recent (AJAX) |
| POST | `/notifications/mark-read/` | Mark all as read |
| POST | `/notifications/mark/<id>/` | Mark one as read |
| POST | `/notifications/delete/<id>/` | Delete notification |

---

## 🧪 Test Credentials

### Razorpay Test Payment
```
Card Number : 4111 1111 1111 1111
Expiry      : 12/28
CVV         : 123
OTP         : 1234
```

### Default Admin
```
Email    : admin@lifelinecare.in
Password : Admin@1234
```

---

## 📦 Requirements

```
Django>=4.2
mysqlclient
python-dotenv
Pillow
anthropic
razorpay
whitenoise
gunicorn
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Built with ❤️ as a full-stack Django healthcare platform.

---

<div align="center">
  <strong>Lifeline Care — Making Healthcare Accessible</strong>
</div>
