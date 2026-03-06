import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid
import os
import hashlib

# ══════════════════════════════════════════
#  إعداد الصفحة
# ══════════════════════════════════════════
st.set_page_config(
    page_title="نظام متابعة الطلبات الداخلية",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap');
*, html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
}
.stApp, .main, .block-container { direction: rtl; text-align: right; }

.app-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
    color: white; padding: 1.2rem 2rem; border-radius: 12px;
    margin-bottom: 1.2rem; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.app-header h1 { font-size: 1.6rem; margin: 0; font-weight: 700; }
.app-header p  { font-size: 0.95rem; margin: 0.3rem 0 0; opacity: 0.85; }

.card {
    background: white; border-radius: 12px; padding: 1.4rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); margin-bottom: 1rem;
    border-right: 4px solid #2d6a9f;
}
.card-pending  { border-right-color: #f59e0b; }
.card-approved { border-right-color: #10b981; }
.card-rejected { border-right-color: #ef4444; }
.card-waiting  { border-right-color: #a78bfa; }

.badge {
    display:inline-block; padding:0.2rem 0.7rem;
    border-radius:20px; font-size:0.78rem; font-weight:700;
}
.badge-pending  { background:#fef3c7; color:#92400e; }
.badge-approved { background:#d1fae5; color:#065f46; }
.badge-rejected { background:#fee2e2; color:#991b1b; }
.badge-waiting  { background:#ede9fe; color:#5b21b6; }

.stButton > button {
    width: 100%; border-radius: 8px;
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem; padding: 0.55rem 1rem;
    font-weight: 600; transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.stTextInput label, .stSelectbox label,
.stTextArea label, .stDateInput label {
    font-family: 'Tajawal', sans-serif !important;
    font-weight: 600; font-size: 0.93rem;
}
.stTextInput input, .stTextArea textarea { direction: rtl; text-align: right; }

.success-box { background:#d1fae5; border-radius:8px; padding:0.9rem; color:#065f46; font-weight:600; text-align:center; margin:0.5rem 0; }
.error-box   { background:#fee2e2; border-radius:8px; padding:0.9rem; color:#991b1b; font-weight:600; text-align:center; margin:0.5rem 0; }
.info-box    { background:#dbeafe; border-radius:8px; padding:0.9rem; color:#1e40af; font-weight:600; text-align:center; margin:0.5rem 0; }
.warn-box    { background:#fef3c7; border-radius:8px; padding:0.9rem; color:#92400e; font-weight:600; text-align:center; margin:0.5rem 0; }
.purple-box  { background:#ede9fe; border-radius:8px; padding:0.9rem; color:#5b21b6; font-weight:600; text-align:center; margin:0.5rem 0; }

.user-badge {
    background: #1e3a5f; color: white; padding: 0.35rem 1rem;
    border-radius: 20px; font-size: 0.82rem; font-weight: 600;
    display: inline-block; margin-bottom: 0.8rem;
}
.login-help {
    background: #f0f9ff; border-radius: 10px; padding: 1rem;
    margin-top: 1.2rem; font-size: 0.85rem;
    color: #1e40af; line-height: 1.9;
}
hr { border-color: #e5e7eb; }
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #1e3a5f;
    margin: 1rem 0 0.6rem;
    border-bottom: 2px solid #2d6a9f; padding-bottom: 0.3rem;
}
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.4rem; }
    .app-header h1 { font-size: 1.3rem; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  ⚙️ الإعدادات – عدّل هنا
# ══════════════════════════════════════════

EMAIL_SENDER   = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"
EXCEL_FILE     = "requests.xlsx"

def h(p): return hashlib.sha256(p.encode()).hexdigest()

# ─── المستخدمون (الاسم العربي الكامل هو مفتاح الدخول) ───
# الأدوار: agent | maintenance_supervisor | supervisor | manager
USERS = {
    "أحمد علي":       {"password": h("1234"),   "role": "agent"},
    "سارة محمد":      {"password": h("1234"),   "role": "agent"},
    "عمر خالد":       {"password": h("1234"),   "role": "agent"},
    "محمد سعيد":      {"password": h("1234"),   "role": "agent"},
    "علي الصيانة":    {"password": h("maint1"), "role": "maintenance_supervisor"},
    "سامي الصيانة":   {"password": h("maint2"), "role": "maintenance_supervisor"},
    "خالد إبراهيم":   {"password": h("sup1"),   "role": "supervisor"},
    "منى حسن":        {"password": h("sup2"),   "role": "supervisor"},
    "عبدالله الأمير": {"password": h("mgr1"),   "role": "manager"},
}

AGENT_NAMES      = [k for k, v in USERS.items() if v["role"] == "agent"]
SUPERVISOR_NAMES = [k for k, v in USERS.items() if v["role"] == "supervisor"]

CAR_NUMBERS = [
    "أ ب ج 1234", "د هـ و 5678", "ز ح ط 9012",
    "ي ك ل 3456", "م ن س 7890", "ع غ ف 1111",
]

REQUEST_TYPES = ["إصلاح", "شراء قطع غيار", "صيانة دورية", "بدل فاقد", "طلب تأجير", "أخرى"]

# حالات الطلب
STATUS_AR = {
    "Pending":                    "⏳ بانتظار مراجعة الصيانة",
    "Reviewed by Maintenance":    "🔧 تمت مراجعة الصيانة",
    "Approved by Supervisor":     "✅ موافقة المشرف",
    "Rejected by Supervisor":     "❌ رفض المشرف",
    "Approved by Manager":        "✅ موافقة المدير",
    "Rejected by Manager":        "❌ رفض المدير",
}

ROLE_AR = {
    "agent":                  "مندوب",
    "maintenance_supervisor": "مشرف صيانة",
    "supervisor":             "مشرف",
    "manager":                "مدير",
}

COLUMNS = [
    "ID", "اسم المندوب", "اسم المستخدم",
    "رقم السيارة", "نوع السيارة", "نوع الطلب",
    "وصف المشكلة", "المشرف", "الحالة",
    "ملاحظات الصيانة", "آخر تاريخ صيانة",
    "تعليق المشرف", "المدير", "تعليق المدير",
    "Timestamp",
]


# ══════════════════════════════════════════
#  Excel HELPERS
# ══════════════════════════════════════════

def load_data() -> pd.DataFrame:
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE, dtype=str)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS].fillna("")
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df: pd.DataFrame):
    df.to_excel(EXCEL_FILE, index=False)

def append_row(row: dict):
    df  = load_data()
    new = pd.DataFrame([{col: row.get(col, "") for col in COLUMNS}])
    df  = pd.concat([df, new], ignore_index=True)
    save_data(df)

def update_row(request_id: str, updates: dict):
    df   = load_data()
    mask = df["ID"] == request_id
    if mask.any():
        for col, val in updates.items():
            if col in df.columns:
                df.loc[mask, col] = val
        save_data(df)

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ══════════════════════════════════════════
#  EMAIL
# ══════════════════════════════════════════

def send_email(to_email: str, subject: str, body: str):
    if not to_email or "@" not in to_email:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to_email
        html = f"""<html dir="rtl"><body style="font-family:Tajawal,Arial;direction:rtl;
              background:#f8fafc;padding:20px;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;
                    box-shadow:0 2px 10px rgba(0,0,0,.1);overflow:hidden;">
          <div style="background:linear-gradient(135deg,#1e3a5f,#2d6a9f);color:white;
                      padding:20px;text-align:center;">
            <h2 style="margin:0;">نظام متابعة الطلبات الداخلية</h2></div>
          <div style="padding:24px;">
            <p style="font-size:15px;line-height:1.8;color:#374151;">
              {body.replace(chr(10),'<br>')}</p></div>
          <div style="background:#f1f5f9;padding:12px;text-align:center;
                      font-size:12px;color:#6b7280;">هذا بريد آلي – لا تردّ عليه</div>
        </div></body></html>"""
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
    except Exception as e:
        st.warning(f"⚠️ تعذّر إرسال الإشعار: {e}")


# ══════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════

def status_badge(status: str) -> str:
    if "Approved" in status:   cls = "badge-approved"
    elif "Rejected" in status: cls = "badge-rejected"
    elif "Maintenance" in status: cls = "badge-waiting"
    else:                      cls = "badge-pending"
    return f'<span class="badge {cls}">{STATUS_AR.get(status, status)}</span>'

def request_card(row, card_cls="card-pending"):
    maint_note = row.get("ملاحظات الصيانة", "")
    last_maint = row.get("آخر تاريخ صيانة", "")
    sup_comment = row.get("تعليق المشرف", "")
    mgr_comment = row.get("تعليق المدير", "")

    maint_html = ""
    if maint_note or last_maint:
        maint_html = f"""
        <div style="background:#f5f3ff;border-radius:8px;padding:0.6rem 1rem;margin:6px 0;">
          <p style="margin:2px 0;">🔧 <strong>ملاحظات الصيانة:</strong> {maint_note}</p>
          <p style="margin:2px 0;">📅 <strong>آخر تاريخ صيانة:</strong> {last_maint}</p>
        </div>"""

    comments_html = ""
    if sup_comment:
        comments_html += f"<p>💬 <strong>تعليق المشرف:</strong> {sup_comment}</p>"
    if mgr_comment:
        comments_html += f"<p>💬 <strong>تعليق المدير:</strong> {mgr_comment}</p>"

    return f"""
    <div class="card {card_cls}">
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
        <strong>🔖 #{row.get('ID','')}</strong>
        {status_badge(row.get('الحالة','Pending'))}
      </div>
      <hr style="margin:6px 0;">
      <p>👤 <strong>المندوب:</strong> {row.get('اسم المندوب','')}</p>
      <p>🚗 <strong>السيارة:</strong> {row.get('رقم السيارة','')} – {row.get('نوع السيارة','')}</p>
      <p>📌 <strong>نوع الطلب:</strong> {row.get('نوع الطلب','')}</p>
      <p>📝 <strong>التفاصيل:</strong> {row.get('وصف المشكلة','')}</p>
      <p>🔍 <strong>المشرف:</strong> {row.get('المشرف','')}</p>
      <p>🕐 <strong>التاريخ:</strong> {row.get('Timestamp','')}</p>
      {maint_html}
      {comments_html}
    </div>"""

def show_user_bar():
    info = st.session_state.get("user_info", {})
    name = info.get("name", "")
    role = ROLE_AR.get(info.get("role", ""), "")
    st.markdown(
        f'<div class="user-badge">👤 {name} &nbsp;|&nbsp; {role}</div>',
        unsafe_allow_html=True)

def logout_btn():
    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        for k in ["logged_in", "username", "user_info"]:
            st.session_state.pop(k, None)
        st.rerun()


# ══════════════════════════════════════════
#  صفحة تسجيل الدخول
# ══════════════════════════════════════════

def page_login():
    st.markdown("""
    <div class="app-header">
        <h1>📋 نظام متابعة الطلبات الداخلية</h1>
        <p>منصة رقمية لإدارة طلبات الصيانة والمشتريات</p>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div style="background:white;border-radius:20px;padding:2.5rem 2rem;
             box-shadow:0 8px 40px rgba(0,0,0,0.12);text-align:center;">
          <div style="font-size:3.5rem;">📋</div>
          <div style="font-size:1.5rem;font-weight:700;color:#1e3a5f;margin-bottom:0.3rem;">
              تسجيل الدخول
          </div>
          <div style="font-size:0.9rem;color:#6b7280;margin-bottom:1.5rem;">
              أدخل اسمك الكامل وكلمة المرور
          </div>
        </div>""", unsafe_allow_html=True)

        fullname = st.text_input("👤 الاسم الكامل", placeholder="مثال: عمر خالد")
        password = st.text_input("🔒 كلمة المرور", type="password",
                                 placeholder="أدخل كلمة المرور")

        if st.button("دخول ←", type="primary"):
            name = fullname.strip()
            if name in USERS and USERS[name]["password"] == h(password):
                st.session_state["logged_in"] = True
                st.session_state["username"]  = name
                st.session_state["user_info"] = {**USERS[name], "name": name}
                st.rerun()
            else:
                st.markdown(
                    '<div class="error-box">🚫 الاسم أو كلمة المرور غير صحيحة،'
                    '<br>يرجى المحاولة مرة أخرى</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div class="login-help">
            <b>📌 طريقة الدخول:</b><br>
            ١. اكتب اسمك الكامل بالعربي كما هو مسجّل في النظام<br>
            &nbsp;&nbsp;&nbsp; مثال: <b>عمر خالد</b> أو <b>خالد إبراهيم</b><br>
            ٢. اكتب كلمة المرور الخاصة بك<br>
            ٣. اضغط زر <b>دخول</b><br><br>
            <b>💡 في حال نسيت بياناتك</b> تواصل مع مسؤول النظام.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════
#  صفحة المندوب
# ══════════════════════════════════════════

def page_agent():
    info = st.session_state["user_info"]
    st.markdown(f"""
    <div class="app-header">
        <h1>👤 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم المندوب – إرسال ومتابعة الطلبات</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    tab1, tab2 = st.tabs(["📝 إرسال طلب جديد", "📋 متابعة طلباتي"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">تفاصيل الطلب الجديد</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            default_i  = AGENT_NAMES.index(info["name"]) if info["name"] in AGENT_NAMES else 0
            agent_name = st.selectbox("👤 اسم المندوب *", AGENT_NAMES, index=default_i)
            car_number = st.selectbox("🚗 رقم السيارة *", CAR_NUMBERS)
        with c2:
            car_type     = st.text_input("🏷️ نوع السيارة *",
                                         placeholder="مثال: تويوتا هايلكس 2022")
            request_type = st.selectbox("📌 نوع الطلب *", REQUEST_TYPES)

        problem_desc = st.text_area("📝 وصف المشكلة / التفاصيل *", height=120,
                                    placeholder="اكتب وصفاً تفصيلياً للمشكلة أو الطلب...")
        supervisor   = st.selectbox("🔍 المشرف المسؤول *", SUPERVISOR_NAMES)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("✅ إرسال الطلب", type="primary"):
            if not all([car_type.strip(), problem_desc.strip()]):
                st.markdown('<div class="error-box">⚠️ يرجى تعبئة جميع الحقول</div>',
                            unsafe_allow_html=True)
            else:
                req_id = str(uuid.uuid4())[:8].upper()
                append_row({
                    "ID":                req_id,
                    "اسم المندوب":       agent_name,
                    "اسم المستخدم":      st.session_state["username"],
                    "رقم السيارة":       car_number,
                    "نوع السيارة":       car_type,
                    "نوع الطلب":         request_type,
                    "وصف المشكلة":       problem_desc,
                    "المشرف":            supervisor,
                    "الحالة":            "Pending",
                    "ملاحظات الصيانة":   "",
                    "آخر تاريخ صيانة":  "",
                    "تعليق المشرف":      "",
                    "المدير":            "",
                    "تعليق المدير":      "",
                    "Timestamp":         now_str(),
                })
                st.markdown(
                    f'<div class="success-box">✅ تم إرسال طلبك بنجاح!<br>'
                    f'رقم طلبك: <strong style="font-size:1.2rem">{req_id}</strong><br>'
                    f'<small>سيتم مراجعته من قِبل الصيانة أولاً ثم المشرف</small></div>',
                    unsafe_allow_html=True)
                st.balloons()

    with tab2:
        df    = load_data()
        my_df = df[df["اسم المستخدم"] == st.session_state["username"]] \
                if not df.empty else pd.DataFrame()

        if my_df.empty:
            st.markdown('<div class="info-box">📭 لم تقم بإرسال أي طلبات حتى الآن</div>',
                        unsafe_allow_html=True)
        else:
            total    = len(my_df)
            pending  = len(my_df[my_df["الحالة"] == "Pending"])
            reviewed = len(my_df[my_df["الحالة"] == "Reviewed by Maintenance"])
            approved = len(my_df[my_df["الحالة"].str.contains("Approved", na=False)])
            rejected = len(my_df[my_df["الحالة"].str.contains("Rejected", na=False)])

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📋 الإجمالي",      total)
            c2.metric("⏳ انتظار صيانة",  pending)
            c3.metric("🔧 راجعتها صيانة", reviewed)
            c4.metric("✅ معتمدة",         approved)
            c5.metric("❌ مرفوضة",         rejected)
            st.divider()

            for _, row in my_df.iterrows():
                s   = row.get("الحالة", "Pending")
                cls = "card-approved" if "Approved" in s else \
                      "card-rejected" if "Rejected" in s else \
                      "card-waiting"  if "Maintenance" in s else "card-pending"
                st.markdown(request_card(row, cls), unsafe_allow_html=True)

    logout_btn()


# ══════════════════════════════════════════
#  صفحة مشرف الصيانة  🔑 البوابة الأولى
# ══════════════════════════════════════════

def page_maintenance():
    info = st.session_state["user_info"]
    st.markdown(f"""
    <div class="app-header">
        <h1>🔧 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم مشرف الصيانة – مراجعة الطلبات وكتابة التاريخ</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    st.markdown("""
    <div class="purple-box">
        🔑 أنت <strong>البوابة الأولى</strong> – المشرف والمدير لن يستطيعا
        رؤية الطلب إلا بعد كتابتك للملاحظات وتاريخ الصيانة
    </div>""", unsafe_allow_html=True)

    df = load_data()

    # الطلبات التي لم تُراجع بعد من الصيانة
    new_requests = df[df["الحالة"] == "Pending"] if not df.empty else pd.DataFrame()

    st.markdown(f'<div class="info-box">📬 طلبات جديدة تنتظر مراجعتك: <strong>{len(new_requests)}</strong></div>',
                unsafe_allow_html=True)

    if new_requests.empty:
        st.markdown('<div class="success-box">✅ لا توجد طلبات جديدة بانتظارك</div>',
                    unsafe_allow_html=True)
    else:
        for _, row in new_requests.iterrows():
            req_id = row.get("ID", "")
            st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)

            st.markdown('<div class="section-title">✍️ أضف مراجعتك</div>',
                        unsafe_allow_html=True)
            maint_note = st.text_area(
                f"ملاحظات الصيانة – طلب #{req_id} *",
                key=f"mn_{req_id}",
                placeholder="اكتب ملاحظاتك عن حالة السيارة والمشكلة...")

            maint_date = st.date_input(
                f"📅 آخر تاريخ إصلاح/شراء – طلب #{req_id} *",
                key=f"md_{req_id}",
                value=datetime.today(),
                format="YYYY/MM/DD")

            if st.button(f"💾 حفظ وإرسال للمشرف – #{req_id}",
                         key=f"msave_{req_id}", type="primary"):
                if not maint_note.strip():
                    st.markdown(
                        '<div class="error-box">⚠️ يرجى كتابة ملاحظات الصيانة أولاً</div>',
                        unsafe_allow_html=True)
                else:
                    update_row(req_id, {
                        "ملاحظات الصيانة":  maint_note,
                        "آخر تاريخ صيانة": str(maint_date),
                        "الحالة":           "Reviewed by Maintenance",
                        "Timestamp":        now_str(),
                    })
                    st.markdown(
                        '<div class="success-box">✅ تم الحفظ – الطلب أصبح مرئياً للمشرف الآن</div>',
                        unsafe_allow_html=True)
                    st.rerun()
            st.divider()

    # طلبات راجعها الصيانة سابقاً (للاطلاع فقط)
    reviewed = df[df["الحالة"] != "Pending"] if not df.empty else pd.DataFrame()
    if not reviewed.empty:
        with st.expander(f"📂 الطلبات التي راجعتها سابقاً ({len(reviewed)})"):
            for _, row in reviewed.iterrows():
                s   = row.get("الحالة", "")
                cls = "card-approved" if "Approved" in s else \
                      "card-rejected" if "Rejected" in s else "card-waiting"
                st.markdown(request_card(row, cls), unsafe_allow_html=True)

    logout_btn()


# ══════════════════════════════════════════
#  صفحة المشرف  🔓 يرى فقط ما راجعته الصيانة
# ══════════════════════════════════════════

def page_supervisor():
    info     = st.session_state["user_info"]
    sup_name = info["name"]

    st.markdown(f"""
    <div class="app-header">
        <h1>🔍 مرحباً، {sup_name}</h1>
        <p>لوحة تحكم المشرف – مراجعة الطلبات والبت فيها</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    df = load_data()

    # شرط: الحالة = Reviewed by Maintenance والمشرف = اسمه
    ready = df[
        (df["المشرف"] == sup_name) &
        (df["الحالة"] == "Reviewed by Maintenance")
    ] if not df.empty else pd.DataFrame()

    st.markdown(
        f'<div class="info-box">📬 الطلبات الجاهزة لمراجعتك (راجعتها الصيانة): '
        f'<strong>{len(ready)}</strong></div>',
        unsafe_allow_html=True)

    if ready.empty:
        st.markdown(
            '<div class="warn-box">⏳ لا توجد طلبات جاهزة للمراجعة حالياً،'
            '<br>انتظر حتى تنهي الصيانة مراجعتها</div>',
            unsafe_allow_html=True)
    else:
        for _, row in ready.iterrows():
            req_id = row.get("ID", "")
            st.markdown(request_card(row, "card-waiting"), unsafe_allow_html=True)

            comment = st.text_area(
                f"💬 تعليقك على الطلب #{req_id}",
                key=f"sc_{req_id}",
                placeholder="أضف تعليقاً – مطلوب عند الرفض، اختياري عند الموافقة")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ موافقة", key=f"sa_{req_id}", type="primary"):
                    update_row(req_id, {
                        "الحالة":        "Approved by Supervisor",
                        "تعليق المشرف":  comment,
                        "Timestamp":     now_str(),
                    })
                    st.markdown(
                        '<div class="success-box">✅ تمت الموافقة – الطلب انتقل للمدير</div>',
                        unsafe_allow_html=True)
                    st.rerun()
            with c2:
                if st.button("❌ رفض", key=f"sr_{req_id}"):
                    if not comment.strip():
                        st.markdown(
                            '<div class="error-box">⚠️ يرجى كتابة سبب الرفض أولاً</div>',
                            unsafe_allow_html=True)
                    else:
                        update_row(req_id, {
                            "الحالة":       "Rejected by Supervisor",
                            "تعليق المشرف": comment,
                            "Timestamp":    now_str(),
                        })
                        st.markdown(
                            '<div class="error-box">❌ تم الرفض وتسجيله</div>',
                            unsafe_allow_html=True)
                        st.rerun()
            st.divider()

    logout_btn()


# ══════════════════════════════════════════
#  صفحة المدير  🔓 يرى فقط ما راجعته الصيانة
# ══════════════════════════════════════════

def page_manager():
    info = st.session_state["user_info"]
    st.markdown(f"""
    <div class="app-header">
        <h1>🏢 مرحباً، {info['name']}</h1>
        <p>لوحة تحكم المدير – الموافقة النهائية والتقارير</p>
    </div>""", unsafe_allow_html=True)
    show_user_bar()

    df = load_data()

    tab1, tab2, tab3 = st.tabs([
        "📥 بانتظار موافقتي",
        "⚡ موافقة مباشرة",
        "📊 كل الطلبات",
    ])

    # ─── تبويب ١: موافقة المشرف ← بانتظار المدير ───
    with tab1:
        st.markdown('<div class="section-title">طلبات وافق عليها المشرف وتنتظر قرارك</div>',
                    unsafe_allow_html=True)
        sup_appr = df[df["الحالة"] == "Approved by Supervisor"] \
                   if not df.empty else pd.DataFrame()

        st.markdown(
            f'<div class="info-box">📬 عدد الطلبات: <strong>{len(sup_appr)}</strong></div>',
            unsafe_allow_html=True)

        if sup_appr.empty:
            st.markdown('<div class="success-box">✅ لا توجد طلبات بانتظار موافقتك</div>',
                        unsafe_allow_html=True)
        else:
            for _, row in sup_appr.iterrows():
                req_id = row.get("ID", "")
                st.markdown(request_card(row, "card-pending"), unsafe_allow_html=True)
                comment = st.text_area(f"💬 تعليق #{req_id}", key=f"mc1_{req_id}",
                                       placeholder="أضف تعليقاً – مطلوب عند الرفض")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ موافقة نهائية", key=f"ma1_{req_id}", type="primary"):
                        update_row(req_id, {
                            "الحالة":       "Approved by Manager",
                            "المدير":       info["name"],
                            "تعليق المدير": comment,
                            "Timestamp":    now_str(),
                        })
                        st.markdown('<div class="success-box">✅ تمت الموافقة النهائية</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
                with c2:
                    if st.button("❌ رفض", key=f"mr1_{req_id}"):
                        if not comment.strip():
                            st.markdown(
                                '<div class="error-box">⚠️ يرجى كتابة سبب الرفض أولاً</div>',
                                unsafe_allow_html=True)
                        else:
                            update_row(req_id, {
                                "الحالة":       "Rejected by Manager",
                                "المدير":       info["name"],
                                "تعليق المدير": comment,
                                "Timestamp":    now_str(),
                            })
                            st.markdown('<div class="error-box">❌ تم الرفض</div>',
                                        unsafe_allow_html=True)
                            st.rerun()
                st.divider()

    # ─── تبويب ٢: موافقة مباشرة (يرى فقط ما راجعته الصيانة) ───
    with tab2:
        st.markdown("""
        <div class="warn-box">
            ⚡ <strong>موافقة مباشرة</strong> – بدون انتظار المشرف.<br>
            تظهر هنا فقط الطلبات التي راجعتها الصيانة.
        </div>""", unsafe_allow_html=True)

        # يرى فقط الطلبات التي راجعتها الصيانة (وليست معتمدة أو مرفوضة بعد)
        direct = df[df["الحالة"] == "Reviewed by Maintenance"] \
                 if not df.empty else pd.DataFrame()

        st.markdown(
            f'<div class="info-box">📬 الطلبات المتاحة: <strong>{len(direct)}</strong></div>',
            unsafe_allow_html=True)

        if direct.empty:
            st.markdown('<div class="success-box">✅ لا توجد طلبات متاحة حالياً</div>',
                        unsafe_allow_html=True)
        else:
            for _, row in direct.iterrows():
                req_id = row.get("ID", "")
                st.markdown(request_card(row, "card-waiting"), unsafe_allow_html=True)
                comment = st.text_area(f"💬 تعليق #{req_id}", key=f"mc2_{req_id}",
                                       placeholder="أضف تعليقاً (اختياري)")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ موافقة مباشرة", key=f"ma2_{req_id}", type="primary"):
                        update_row(req_id, {
                            "الحالة":       "Approved by Manager",
                            "المدير":       info["name"],
                            "تعليق المدير": comment,
                            "Timestamp":    now_str(),
                        })
                        st.markdown('<div class="success-box">✅ تمت الموافقة المباشرة</div>',
                                    unsafe_allow_html=True)
                        st.rerun()
                with c2:
                    if st.button("❌ رفض مباشر", key=f"mr2_{req_id}"):
                        if not comment.strip():
                            st.markdown(
                                '<div class="error-box">⚠️ يرجى كتابة سبب الرفض أولاً</div>',
                                unsafe_allow_html=True)
                        else:
                            update_row(req_id, {
                                "الحالة":       "Rejected by Manager",
                                "المدير":       info["name"],
                                "تعليق المدير": comment,
                                "Timestamp":    now_str(),
                            })
                            st.markdown('<div class="error-box">❌ تم الرفض</div>',
                                        unsafe_allow_html=True)
                            st.rerun()
                st.divider()

    # ─── تبويب ٣: كل الطلبات ───
    with tab3:
        if df.empty:
            st.markdown('<div class="info-box">📭 لا توجد طلبات مسجلة</div>',
                        unsafe_allow_html=True)
        else:
            total    = len(df)
            pending  = len(df[df["الحالة"] == "Pending"])
            reviewed = len(df[df["الحالة"] == "Reviewed by Maintenance"])
            approved = len(df[df["الحالة"].str.contains("Approved", na=False)])
            rejected = len(df[df["الحالة"].str.contains("Rejected", na=False)])

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("📋 الإجمالي",        total)
            c2.metric("⏳ انتظار صيانة",    pending)
            c3.metric("🔧 راجعتها صيانة",   reviewed)
            c4.metric("✅ معتمدة",           approved)
            c5.metric("❌ مرفوضة",           rejected)
            st.divider()

            show = df.copy()
            show["الحالة"] = show["الحالة"].map(lambda s: STATUS_AR.get(s, s))
            cols = ["ID", "اسم المندوب", "رقم السيارة", "نوع السيارة",
                    "نوع الطلب", "الحالة", "آخر تاريخ صيانة", "Timestamp"]
            st.dataframe(show[[c for c in cols if c in show.columns]],
                         use_container_width=True)

            if os.path.exists(EXCEL_FILE):
                with open(EXCEL_FILE, "rb") as f:
                    st.download_button(
                        "📥 تحميل كل الطلبات (Excel)",
                        data=f,
                        file_name=f"الطلبات_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    logout_btn()


# ══════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════

def main():
    if not st.session_state.get("logged_in"):
        page_login()
        return

    role = st.session_state["user_info"].get("role", "")

    if   role == "agent":                  page_agent()
    elif role == "maintenance_supervisor": page_maintenance()
    elif role == "supervisor":             page_supervisor()
    elif role == "manager":                page_manager()
    else:
        st.error("⚠️ دور غير معروف، تواصل مع مسؤول النظام")
        if st.button("خروج"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
