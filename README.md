# 📋 دليل تشغيل نظام متابعة الطلبات الداخلية

## 🗂️ الملفات المطلوبة
```
app.py                 ← التطبيق الرئيسي
requirements.txt       ← المكتبات المطلوبة
service_account.json   ← مفتاح Google Service Account (تنشئه أنت)
```

---

## ⚙️ خطوات الإعداد

### 1. تثبيت المكتبات
```bash
pip install -r requirements.txt
```

---

### 2. إعداد Google Sheets

#### أ) إنشاء Google Sheet
1. افتح [Google Sheets](https://sheets.google.com)
2. أنشئ ملف جديد بأي اسم (مثل: "طلبات الشركة")
3. انسخ الـ **Sheet ID** من الرابط:
   - الرابط: `https://docs.google.com/spreadsheets/d/**YOUR_ID_HERE**/edit`

#### ب) إنشاء Service Account
1. افتح [Google Cloud Console](https://console.cloud.google.com)
2. أنشئ مشروعاً جديداً أو اختر موجوداً
3. فعّل **Google Sheets API** و **Google Drive API**
4. اذهب إلى: **IAM & Admin → Service Accounts → Create Service Account**
5. بعد الإنشاء: اضغط على الـ Account → **Keys → Add Key → JSON**
6. احفظ الملف باسم `service_account.json` في نفس مجلد `app.py`
7. افتح الـ Sheet → مشاركة (Share) → أضف **email الـ Service Account** بصلاحية **Editor**

---

### 3. إعداد إشعارات البريد (Gmail)

1. افتح حساب Gmail الذي تريد الإرسال منه
2. فعّل **2-Step Verification**
3. اذهب إلى: **Google Account → Security → App Passwords**
4. أنشئ App Password واختر "Other"
5. انسخ الكلمة المكوّنة من 16 حرف

---

### 4. تعديل إعدادات `app.py`

افتح `app.py` وعدّل القسم التالي:

```python
# ── Email settings ──
EMAIL_SENDER   = "your_email@gmail.com"    # ← بريدك
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"     # ← App Password

# ── Google Sheets ──
GOOGLE_SHEET_ID = "YOUR_GOOGLE_SHEET_ID"   # ← ID من الخطوة 2أ

# ── Users ──
USERS = {
    "agent1@company.com":      {"name": "اسم المندوب",  "role": "agent"},
    "supervisor1@company.com": {"name": "اسم المشرف",   "role": "supervisor"},
    "manager@company.com":     {"name": "اسم المدير",   "role": "manager"},
    # أضف المزيد...
}
```

---

### 5. تشغيل التطبيق
```bash
streamlit run app.py
```

افتح المتصفح على: `http://localhost:8501`

---

## 🚀 النشر على Streamlit Cloud (مجاناً)

1. ارفع المشروع على **GitHub** (لا ترفع `service_account.json`)
2. افتح [share.streamlit.io](https://share.streamlit.io) وسجّل دخولك
3. أنشئ تطبيقاً جديداً من الـ Repo
4. في **Settings → Secrets** أضف:

```toml
EMAIL_SENDER   = "your@gmail.com"
EMAIL_PASSWORD = "app_password"
GOOGLE_SHEET_ID = "sheet_id"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "...@....iam.gserviceaccount.com"
# (انسخ كل محتوى service_account.json هنا)
```

---

## 👥 الأدوار المدعومة

| الدور      | الصلاحيات |
|-----------|-----------|
| **مندوب** (agent) | إرسال طلبات جديدة + متابعة طلباته |
| **مشرف** (supervisor) | مراجعة الطلبات المعلّقة عليه + موافقة/رفض |
| **مدير** (manager) | مراجعة الطلبات المعتمدة من المشرف + الموافقة النهائية + عرض كل الطلبات |

---

## 📊 أعمدة Google Sheet

| العمود | الوصف |
|--------|-------|
| ID | رقم الطلب الفريد |
| اسم المندوب | اسم مقدّم الطلب |
| البريد الإلكتروني | إيميل المندوب |
| رقم السيارة | لوحة السيارة |
| نوع السيارة | موديل وسنة السيارة |
| نوع الطلب | إصلاح / شراء ... إلخ |
| وصف المشكلة | التفاصيل |
| المشرف | إيميل المشرف المختار |
| الحالة | Pending / Approved / Rejected |
| المدير | إيميل المدير الذي اتخذ القرار |
| التعليقات | تعليقات المشرف أو المدير |
| Timestamp | وقت آخر تحديث |
